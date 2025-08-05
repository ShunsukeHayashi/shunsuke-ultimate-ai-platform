/**
 * Course Service with Database
 * Ultimate ShunsukeModel Ecosystem
 */

import { 
  PrismaClient, 
  Course, 
  CourseStatus,
  ExportFormat as PrismaExportFormat,
  Prisma
} from '../generated/prisma';
import { 
  Course as CourseType, 
  CourseMetadata, 
  CourseModule,
  ExportFormat
} from '../types';
import { AppError, ErrorCodes } from '../utils/errors';
import { databaseService } from './databaseService';
import { cacheService, CacheKeys, CacheTTL } from './cacheService';
import { 
  courseStrategies, 
  CacheInvalidator,
  Cacheable,
  InvalidatesCache 
} from './cacheStrategies';

export class CourseService {
  private prisma: PrismaClient;
  
  constructor() {
    this.prisma = databaseService.getClient();
  }
  
  /**
   * Create a new course
   */
  async createCourse(
    userId: string,
    courseData: CourseType,
    scripts: Map<string, string>,
    audioFiles: Map<string, string>,
    summary?: string
  ): Promise<Course> {
    // Calculate stats
    const totalModules = courseData.modules.length;
    const totalLessons = courseData.modules.reduce(
      (total, module) => total + module.sections.reduce(
        (sectionTotal, section) => sectionTotal + section.lessons.length, 
        0
      ), 
      0
    );
    
    // Create course with related data in a transaction
    const course = await this.prisma.$transaction(async (tx) => {
      // Create course
      const newCourse = await tx.course.create({
        data: {
          userId,
          title: courseData.metadata.course_title,
          description: courseData.metadata.course_description,
          field: courseData.metadata.specialty_field,
          level: courseData.metadata.difficulty_level,
          audience: courseData.metadata.target_audience,
          language: courseData.metadata.language || 'ja',
          instructorName: courseData.metadata.instructor?.name,
          instructorPersona: courseData.metadata.instructor?.persona,
          instructorTone: courseData.metadata.instructor?.tone,
          modules: courseData.modules as unknown as Prisma.JsonValue,
          summary,
          totalModules,
          totalLessons,
          status: courseData.status === 'draft' ? CourseStatus.DRAFT : CourseStatus.PUBLISHED
        }
      });
      
      // Create scripts
      if (scripts.size > 0) {
        const scriptData = Array.from(scripts.entries()).map(([lessonKey, content]) => ({
          courseId: newCourse.id,
          lessonKey,
          content
        }));
        
        await tx.script.createMany({
          data: scriptData
        });
      }
      
      // Create audio files
      if (audioFiles.size > 0) {
        const audioData = Array.from(audioFiles.entries()).map(([lessonKey, fileData]) => ({
          courseId: newCourse.id,
          lessonKey,
          fileData: Buffer.from(fileData, 'base64')
        }));
        
        await tx.audioFile.createMany({
          data: audioData
        });
      }
      
      return newCourse;
    });
    
    // Invalidate related caches
    await CacheInvalidator.invalidateCourse(course.id, userId);
    
    return course;
  }
  
  /**
   * Create a simple course for testing
   */
  async createSimpleCourse(data: {
    userId: string;
    title: string;
    description: string;
    field: string;
    level: string;
    language: string;
  }): Promise<Course> {
    const course = await this.prisma.course.create({
      data: {
        userId: data.userId,
        title: data.title,
        description: data.description,
        field: data.field,
        level: data.level,
        language: data.language,
        audience: 'general',
        modules: [],
        totalModules: 0,
        totalLessons: 0,
        status: CourseStatus.DRAFT
      }
    });
    
    // Invalidate related caches
    await CacheInvalidator.invalidateCourse(course.id, data.userId);
    
    return course;
  }
  
  /**
   * Get course by ID with caching
   */
  async getCourseById(courseId: string, userId?: string): Promise<Course | null> {
    // Try cache first
    const cacheKey = courseStrategies.getCourse.generateKey(courseId);
    const cached = await cacheService.get<Course>(cacheKey);
    
    if (cached) {
      // Verify access if userId provided
      if (userId && cached.userId !== userId) {
        return null;
      }
      console.log(`Cache hit: ${cacheKey}`);
      return cached;
    }
    
    // Fetch from database
    const where: Prisma.CourseWhereInput = { id: courseId };
    if (userId) {
      where.userId = userId;
    }
    
    const course = await this.prisma.course.findFirst({
      where,
      include: {
        scripts: true,
        audioFiles: true,
        exports: true,
        user: {
          select: {
            id: true,
            name: true,
            email: true
          }
        }
      }
    });
    
    // Cache the result
    if (course) {
      await cacheService.set(cacheKey, course, { 
        ttl: courseStrategies.getCourse.ttl 
      });
      console.log(`Cached: ${cacheKey}`);
    }
    
    return course;
  }
  
  /**
   * Get courses by user
   */
  async getCoursesByUser(
    userId: string,
    options?: {
      status?: CourseStatus;
      limit?: number;
      offset?: number;
      orderBy?: 'createdAt' | 'updatedAt' | 'title';
      order?: 'asc' | 'desc';
    }
  ): Promise<{ courses: Course[]; total: number }> {
    // Generate cache key
    const cacheKey = courseStrategies.getUserCourses.generateKey(userId, options?.status);
    const cacheData = await cacheService.get<{ courses: Course[]; total: number }>(cacheKey);
    
    if (cacheData) {
      console.log(`Cache hit: ${cacheKey}`);
      return cacheData;
    }
    
    const where: Prisma.CourseWhereInput = { userId };
    
    if (options?.status) {
      where.status = options.status;
    }
    
    const [courses, total] = await this.prisma.$transaction([
      this.prisma.course.findMany({
        where,
        take: options?.limit || 20,
        skip: options?.offset || 0,
        orderBy: {
          [options?.orderBy || 'createdAt']: options?.order || 'desc'
        },
        include: {
          scripts: {
            select: {
              id: true,
              lessonKey: true
            }
          },
          audioFiles: {
            select: {
              id: true,
              lessonKey: true
            }
          },
          exports: {
            select: {
              id: true,
              format: true,
              createdAt: true
            }
          }
        }
      }),
      this.prisma.course.count({ where })
    ]);
    
    const result = { courses, total };
    
    // Cache the result
    await cacheService.set(cacheKey, result, { 
      ttl: courseStrategies.getUserCourses.ttl 
    });
    console.log(`Cached: ${cacheKey}`);
    
    return result;
  }
  
  /**
   * Update course
   */
  async updateCourse(
    courseId: string,
    userId: string,
    updates: Partial<{
      title: string;
      description: string;
      status: CourseStatus;
      modules: CourseModule[];
      summary: string;
    }>
  ): Promise<Course> {
    // Verify ownership
    const existingCourse = await this.prisma.course.findFirst({
      where: { id: courseId, userId }
    });
    
    if (!existingCourse) {
      throw new AppError('Course not found', ErrorCodes.NOT_FOUND);
    }
    
    // Prepare update data
    const updateData: Prisma.CourseUpdateInput = {};
    
    if (updates.title) updateData.title = updates.title;
    if (updates.description) updateData.description = updates.description;
    if (updates.status) updateData.status = updates.status;
    if (updates.summary) updateData.summary = updates.summary;
    
    if (updates.modules) {
      updateData.modules = updates.modules as unknown as Prisma.JsonValue;
      
      // Update stats
      updateData.totalModules = updates.modules.length;
      updateData.totalLessons = updates.modules.reduce(
        (total, module) => total + module.sections.reduce(
          (sectionTotal, section) => sectionTotal + section.lessons.length, 
          0
        ), 
        0
      );
    }
    
    // Update published date if status changes to published
    if (updates.status === CourseStatus.PUBLISHED && existingCourse.status !== CourseStatus.PUBLISHED) {
      updateData.publishedAt = new Date();
    }
    
    const updatedCourse = await this.prisma.course.update({
      where: { id: courseId },
      data: updateData
    });
    
    // Invalidate related caches
    await CacheInvalidator.invalidateCourse(courseId, userId);
    
    return updatedCourse;
  }
  
  /**
   * Delete course
   */
  async deleteCourse(courseId: string, userId: string): Promise<void> {
    // Verify ownership
    const course = await this.prisma.course.findFirst({
      where: { id: courseId, userId }
    });
    
    if (!course) {
      throw new AppError('Course not found', ErrorCodes.NOT_FOUND);
    }
    
    // Delete course (cascades to related records)
    await this.prisma.course.delete({
      where: { id: courseId }
    });
    
    // Invalidate related caches
    await CacheInvalidator.invalidateCourse(courseId, userId);
  }
  
  /**
   * Create export record
   */
  async createExportRecord(
    courseId: string,
    format: ExportFormat,
    filePath: string,
    fileSize: number
  ): Promise<void> {
    const prismaFormat = format.toUpperCase() as PrismaExportFormat;
    
    await this.prisma.export.create({
      data: {
        courseId,
        format: prismaFormat,
        filePath,
        fileSize,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      }
    });
  }
  
  /**
   * Get course scripts
   */
  async getCourseScripts(courseId: string): Promise<Map<string, string>> {
    const scripts = await this.prisma.script.findMany({
      where: { courseId }
    });
    
    const scriptMap = new Map<string, string>();
    scripts.forEach(script => {
      scriptMap.set(script.lessonKey, script.content);
    });
    
    return scriptMap;
  }
  
  /**
   * Get course audio files
   */
  async getCourseAudioFiles(courseId: string): Promise<Map<string, string>> {
    const audioFiles = await this.prisma.audioFile.findMany({
      where: { courseId }
    });
    
    const audioMap = new Map<string, string>();
    audioFiles.forEach(audio => {
      if (audio.fileData) {
        audioMap.set(audio.lessonKey, Buffer.from(audio.fileData).toString('base64'));
      }
    });
    
    return audioMap;
  }
  
  /**
   * Search courses
   */
  async searchCourses(
    query: string,
    options?: {
      userId?: string;
      status?: CourseStatus;
      field?: string;
      limit?: number;
    }
  ): Promise<Course[]> {
    // Check if should cache
    if (courseStrategies.searchCourses.shouldCache && 
        !courseStrategies.searchCourses.shouldCache(query)) {
      // Don't cache short queries
      return this.performCourseSearch(query, options);
    }
    
    // Generate cache key
    const cacheKey = courseStrategies.searchCourses.generateKey(query, options);
    const cached = await cacheService.get<Course[]>(cacheKey);
    
    if (cached) {
      console.log(`Cache hit: ${cacheKey}`);
      return cached;
    }
    
    const results = await this.performCourseSearch(query, options);
    
    // Cache the result
    await cacheService.set(cacheKey, results, { 
      ttl: courseStrategies.searchCourses.ttl 
    });
    console.log(`Cached: ${cacheKey}`);
    
    return results;
  }
  
  private async performCourseSearch(
    query: string,
    options?: {
      userId?: string;
      status?: CourseStatus;
      field?: string;
      limit?: number;
    }
  ): Promise<Course[]> {
    const where: Prisma.CourseWhereInput = {
      OR: [
        { title: { contains: query, mode: 'insensitive' } },
        { description: { contains: query, mode: 'insensitive' } },
        { summary: { contains: query, mode: 'insensitive' } }
      ]
    };
    
    if (options?.userId) where.userId = options.userId;
    if (options?.status) where.status = options.status;
    if (options?.field) where.field = options.field;
    
    return await this.prisma.course.findMany({
      where,
      take: options?.limit || 20,
      orderBy: { createdAt: 'desc' }
    });
  }
}