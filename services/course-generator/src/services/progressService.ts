import { PrismaClient, ProgressStatus } from '../generated/prisma';

export interface EnrollmentData {
  userId: string;
  courseId: string;
}

export interface LessonProgressData {
  enrollmentId: string;
  moduleIndex: number;
  sectionIndex: number;
  lessonIndex: number;
  lessonKey: string;
  timeSpent?: number;
  notes?: string;
}

export interface CourseProgress {
  enrollment: any;
  lessonProgress: any[];
  nextLesson?: {
    moduleIndex: number;
    sectionIndex: number;
    lessonIndex: number;
    lessonKey: string;
  };
}

class ProgressService {
  private prisma: PrismaClient;

  constructor(prisma: PrismaClient) {
    this.prisma = prisma;
  }

  /**
   * Enroll a user in a course
   */
  async enrollInCourse(data: EnrollmentData) {
    const { userId, courseId } = data;

    // Check if already enrolled
    const existingEnrollment = await this.prisma.courseEnrollment.findUnique({
      where: {
        userId_courseId: {
          userId,
          courseId
        }
      }
    });

    if (existingEnrollment) {
      return existingEnrollment;
    }

    // Create enrollment
    const enrollment = await this.prisma.courseEnrollment.create({
      data: {
        userId,
        courseId,
        status: 'NOT_STARTED'
      },
      include: {
        course: {
          select: {
            id: true,
            title: true,
            totalModules: true,
            totalLessons: true
          }
        }
      }
    });

    // Log activity
    await this.prisma.learningActivity.create({
      data: {
        userId,
        courseId,
        activityType: 'enrolled_course'
      }
    });

    return enrollment;
  }

  /**
   * Get user's course progress
   */
  async getCourseProgress(userId: string, courseId: string): Promise<CourseProgress | null> {
    const enrollment = await this.prisma.courseEnrollment.findUnique({
      where: {
        userId_courseId: {
          userId,
          courseId
        }
      },
      include: {
        course: {
          include: {
            user: {
              select: {
                id: true,
                name: true,
                email: true
              }
            }
          }
        },
        lessonProgress: {
          orderBy: [
            { moduleIndex: 'asc' },
            { sectionIndex: 'asc' },
            { lessonIndex: 'asc' }
          ]
        }
      }
    });

    if (!enrollment) {
      return null;
    }

    // Calculate next lesson
    const course = enrollment.course;
    const modules = course.modules as any[];
    let nextLesson = null;

    // Find the first incomplete lesson
    for (let moduleIndex = 0; moduleIndex < modules.length; moduleIndex++) {
      const module = modules[moduleIndex];
      if (!module.sections) continue;

      for (let sectionIndex = 0; sectionIndex < module.sections.length; sectionIndex++) {
        const section = module.sections[sectionIndex];
        if (!section.lessons) continue;

        for (let lessonIndex = 0; lessonIndex < section.lessons.length; lessonIndex++) {
          const lessonKey = `module_${moduleIndex}_section_${sectionIndex}_lesson_${lessonIndex}`;
          const progress = enrollment.lessonProgress.find(p => p.lessonKey === lessonKey);
          
          if (!progress || progress.status !== 'COMPLETED') {
            nextLesson = {
              moduleIndex,
              sectionIndex,
              lessonIndex,
              lessonKey
            };
            break;
          }
        }
        if (nextLesson) break;
      }
      if (nextLesson) break;
    }

    return {
      enrollment,
      lessonProgress: enrollment.lessonProgress,
      nextLesson
    };
  }

  /**
   * Start or update lesson progress
   */
  async updateLessonProgress(data: LessonProgressData) {
    const { enrollmentId, moduleIndex, sectionIndex, lessonIndex, lessonKey } = data;

    // Get enrollment
    const enrollment = await this.prisma.courseEnrollment.findUnique({
      where: { id: enrollmentId }
    });

    if (!enrollment) {
      throw new Error('Enrollment not found');
    }

    // Find or create lesson progress
    let lessonProgress = await this.prisma.lessonProgress.findUnique({
      where: {
        enrollmentId_lessonKey: {
          enrollmentId,
          lessonKey
        }
      }
    });

    if (!lessonProgress) {
      lessonProgress = await this.prisma.lessonProgress.create({
        data: {
          enrollmentId,
          moduleIndex,
          sectionIndex,
          lessonIndex,
          lessonKey,
          status: 'IN_PROGRESS',
          startedAt: new Date(),
          lastAccessedAt: new Date(),
          viewCount: 1
        }
      });

      // Update enrollment if this is the first lesson
      if (enrollment.status === 'NOT_STARTED') {
        await this.prisma.courseEnrollment.update({
          where: { id: enrollmentId },
          data: {
            status: 'IN_PROGRESS',
            startedAt: new Date(),
            lastAccessedAt: new Date()
          }
        });

        // Log activity
        await this.prisma.learningActivity.create({
          data: {
            userId: enrollment.userId,
            courseId: enrollment.courseId,
            activityType: 'started_course'
          }
        });
      }
    } else {
      // Update existing progress
      lessonProgress = await this.prisma.lessonProgress.update({
        where: { id: lessonProgress.id },
        data: {
          lastAccessedAt: new Date(),
          viewCount: lessonProgress.viewCount + 1,
          timeSpent: data.timeSpent || lessonProgress.timeSpent,
          notes: data.notes !== undefined ? data.notes : lessonProgress.notes
        }
      });
    }

    // Update enrollment last accessed
    await this.prisma.courseEnrollment.update({
      where: { id: enrollmentId },
      data: {
        lastAccessedAt: new Date()
      }
    });

    return lessonProgress;
  }

  /**
   * Mark lesson as completed
   */
  async completeLessonAndGetNext(enrollmentId: string, lessonKey: string) {
    const enrollment = await this.prisma.courseEnrollment.findUnique({
      where: { id: enrollmentId },
      include: { course: true }
    });

    if (!enrollment) {
      throw new Error('Enrollment not found');
    }

    // Mark lesson as completed
    const lessonProgress = await this.prisma.lessonProgress.update({
      where: {
        enrollmentId_lessonKey: {
          enrollmentId,
          lessonKey
        }
      },
      data: {
        status: 'COMPLETED',
        completedAt: new Date()
      }
    });

    // Log activity
    await this.prisma.learningActivity.create({
      data: {
        userId: enrollment.userId,
        courseId: enrollment.courseId,
        activityType: 'completed_lesson',
        lessonKey
      }
    });

    // Calculate overall progress
    const totalLessons = enrollment.course.totalLessons;
    const completedLessons = await this.prisma.lessonProgress.count({
      where: {
        enrollmentId,
        status: 'COMPLETED'
      }
    });

    const progressPercentage = (completedLessons / totalLessons) * 100;

    // Update enrollment progress
    const updatedEnrollment = await this.prisma.courseEnrollment.update({
      where: { id: enrollmentId },
      data: {
        progressPercentage,
        status: progressPercentage === 100 ? 'COMPLETED' : 'IN_PROGRESS',
        completedAt: progressPercentage === 100 ? new Date() : undefined
      }
    });

    // If course completed, log activity
    if (progressPercentage === 100) {
      await this.prisma.learningActivity.create({
        data: {
          userId: enrollment.userId,
          courseId: enrollment.courseId,
          activityType: 'completed_course'
        }
      });
    }

    // Get next lesson
    const progress = await this.getCourseProgress(enrollment.userId, enrollment.courseId);
    
    return {
      completedLesson: lessonProgress,
      enrollment: updatedEnrollment,
      nextLesson: progress?.nextLesson,
      progressPercentage
    };
  }

  /**
   * Get user's enrolled courses
   */
  async getUserEnrollments(userId: string) {
    const enrollments = await this.prisma.courseEnrollment.findMany({
      where: { userId },
      include: {
        course: {
          select: {
            id: true,
            title: true,
            description: true,
            field: true,
            totalModules: true,
            totalLessons: true,
            estimatedDuration: true
          }
        },
        _count: {
          select: {
            lessonProgress: {
              where: {
                status: 'COMPLETED'
              }
            }
          }
        }
      },
      orderBy: {
        lastAccessedAt: 'desc'
      }
    });

    return enrollments.map(enrollment => ({
      ...enrollment,
      completedLessons: enrollment._count.lessonProgress
    }));
  }

  /**
   * Get user's learning activity
   */
  async getUserActivity(userId: string, limit = 50) {
    const activities = await this.prisma.learningActivity.findMany({
      where: { userId },
      include: {
        course: {
          select: {
            id: true,
            title: true
          }
        }
      },
      orderBy: {
        createdAt: 'desc'
      },
      take: limit
    });

    return activities;
  }

  /**
   * Toggle lesson bookmark
   */
  async toggleLessonBookmark(enrollmentId: string, lessonKey: string) {
    const lessonProgress = await this.prisma.lessonProgress.findUnique({
      where: {
        enrollmentId_lessonKey: {
          enrollmentId,
          lessonKey
        }
      }
    });

    if (!lessonProgress) {
      throw new Error('Lesson progress not found');
    }

    const updated = await this.prisma.lessonProgress.update({
      where: { id: lessonProgress.id },
      data: {
        bookmarked: !lessonProgress.bookmarked
      }
    });

    return updated;
  }

  /**
   * Update lesson notes
   */
  async updateLessonNotes(enrollmentId: string, lessonKey: string, notes: string) {
    const updated = await this.prisma.lessonProgress.update({
      where: {
        enrollmentId_lessonKey: {
          enrollmentId,
          lessonKey
        }
      },
      data: {
        notes
      }
    });

    return updated;
  }

  /**
   * Get learning statistics
   */
  async getUserLearningStats(userId: string) {
    const [
      totalEnrollments,
      completedCourses,
      inProgressCourses,
      totalTimeSpent,
      recentActivity
    ] = await Promise.all([
      this.prisma.courseEnrollment.count({
        where: { userId }
      }),
      this.prisma.courseEnrollment.count({
        where: { userId, status: 'COMPLETED' }
      }),
      this.prisma.courseEnrollment.count({
        where: { userId, status: 'IN_PROGRESS' }
      }),
      this.prisma.courseEnrollment.aggregate({
        where: { userId },
        _sum: {
          totalTimeSpent: true
        }
      }),
      this.prisma.learningActivity.count({
        where: {
          userId,
          createdAt: {
            gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // Last 7 days
          }
        }
      })
    ]);

    return {
      totalEnrollments,
      completedCourses,
      inProgressCourses,
      totalTimeSpent: totalTimeSpent._sum.totalTimeSpent || 0,
      recentActivity,
      completionRate: totalEnrollments > 0 
        ? Math.round((completedCourses / totalEnrollments) * 100) 
        : 0
    };
  }
}

export default ProgressService;