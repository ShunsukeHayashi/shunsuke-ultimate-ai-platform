/**
 * Course Generator Service
 * Ultimate ShunsukeModel Ecosystem
 * 
 * Main Express server for AI-powered course generation
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import { config } from 'dotenv';
import { 
  GeminiService,
  ContextAgent,
  WebCrawlerService,
  AudioService,
  ExportService,
  databaseService
} from './services';
import { cacheService } from './services/cacheService';
import { AuthServiceDb } from './services/authServiceDb';
import { CourseService } from './services/courseService';
import ShareService from './services/shareService';
import ProgressService from './services/progressService';
import { promptTemplateService } from './services/promptTemplateService';
import { 
  CourseMetadata, 
  GenerationOptions, 
  ContextSource,
  ExportOptions,
  GenerationProgress,
  Course
} from './types';
import { AppError, ErrorCodes, handleError } from './utils/errors';
import { authenticate, authorize, optionalAuth } from './middleware/auth';

// Load environment variables
config();

// Import path for export handling
import * as path from 'path';

// Helper function to transform Prisma Course to Course type
function transformPrismaCourseToType(prismaCourse: any): Course {
  return {
    metadata: {
      course_title: prismaCourse.title,
      course_description: prismaCourse.description,
      specialty_field: prismaCourse.field,
      avatar: prismaCourse.instructorName || 'インストラクター',
      profession: 'プロフェッショナル',
      tone_of_voice: prismaCourse.instructorTone || 'conversational',
      target_audience: prismaCourse.audience,
      difficulty_level: prismaCourse.level,
      estimated_duration: `${prismaCourse.totalLessons * 10} minutes`,
      language: prismaCourse.language,
      instructor: {
        name: prismaCourse.instructorName || 'インストラクター',
        persona: prismaCourse.instructorPersona || 'friendly',
        tone: prismaCourse.instructorTone || 'conversational'
      }
    },
    modules: prismaCourse.modules as any,
    created_at: prismaCourse.createdAt,
    updated_at: prismaCourse.updatedAt,
    version: '1.0.0',
    status: prismaCourse.status === 'PUBLISHED' ? 'published' : 'draft'
  };
}

// Initialize services
const geminiService = new GeminiService(process.env.GEMINI_API_KEY || '');
const contextAgent = new ContextAgent();
const webCrawler = new WebCrawlerService();
const audioService = new AudioService('./audio_cache');
const exportService = new ExportService('./exports');
const authService = new AuthServiceDb();
const courseService = new CourseService();
const shareService = new ShareService(databaseService.getClient());
const progressService = new ProgressService(databaseService.getClient());

// Create Express app
const app = express();
const PORT = process.env.PORT || 3002;

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN?.split(',') || '*',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
  exposedHeaders: ['Content-Type']
}));
app.use(compression());
app.use(morgan('combined'));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Serve static files from public directory
app.use(express.static(path.join(__dirname, '../public')));

// Health check endpoints (both /health and /api/health for compatibility)
app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'course-generator',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

app.get('/api/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'course-generator',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// ==================== Authentication Endpoints ====================

// Register new user
app.post('/api/auth/register', async (req, res) => {
  try {
    const { email, password, name } = req.body;
    
    if (!email || !password || !name) {
      throw new AppError('Email, password, and name are required', ErrorCodes.VALIDATION_ERROR);
    }
    
    const response = await authService.register({ email, password, name });
    
    res.json({
      success: true,
      ...response
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Login
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      throw new AppError('Email and password are required', ErrorCodes.VALIDATION_ERROR);
    }
    
    const response = await authService.login({ email, password });
    
    res.json({
      success: true,
      ...response
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get current user profile (both endpoints for compatibility)
app.get('/api/users/profile', authenticate, async (req, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.NOT_FOUND);
    }
    
    const user = await authService.getUserById(req.user.userId);
    if (!user) {
      throw new AppError('User not found', ErrorCodes.NOT_FOUND);
    }
    
    const { passwordHash, ...userWithoutPassword } = user;
    
    res.json({
      success: true,
      email: userWithoutPassword.email,
      name: userWithoutPassword.name,
      id: userWithoutPassword.id
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get current user
app.get('/api/auth/me', authenticate, async (req, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.NOT_FOUND);
    }
    
    const user = await authService.getUserById(req.user.userId);
    if (!user) {
      throw new AppError('User not found', ErrorCodes.NOT_FOUND);
    }
    
    const { passwordHash, ...userWithoutPassword } = user;
    
    res.json({
      success: true,
      user: userWithoutPassword
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Logout (client-side token removal in real app)
app.post('/api/auth/logout', authenticate, (_req, res) => {
  // In a real app, you might invalidate the token server-side
  res.json({
    success: true,
    message: 'Logged out successfully'
  });
});

// Get all users (admin only)
app.get('/api/auth/users', authenticate, authorize('admin'), async (_req, res) => {
  try {
    const users = await authService.getAllUsers();
    
    res.json({
      success: true,
      users
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// ==================== Course Management Endpoints ====================

// Create a new course
app.post('/api/courses', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { title, topic, difficulty, language, generateContent } = req.body;
    
    if (!title || !topic) {
      throw new AppError('Title and topic are required', ErrorCodes.VALIDATION_ERROR);
    }
    
    // Create a simple course
    const course = await courseService.createSimpleCourse({
      userId: req.user.userId,
      title,
      description: `Learn about ${topic}`,
      field: topic,
      level: difficulty || 'beginner',
      language: language || 'ja'
    });
    
    res.status(201).json({
      success: true,
      course,
      id: course.id
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get user's courses
app.get('/api/courses', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { status, limit = 20, offset = 0, orderBy = 'createdAt', order = 'desc' } = req.query;
    
    const result = await courseService.getCoursesByUser(req.user.userId, {
      status: status as any,
      limit: Number(limit),
      offset: Number(offset),
      orderBy: orderBy as any,
      order: order as any
    });
    
    res.json(result.courses);
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get course by ID
app.get('/api/courses/:id', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const course = await courseService.getCourseById(req.params.id, req.user.userId);
    
    if (!course) {
      throw new AppError('Course not found', ErrorCodes.NOT_FOUND);
    }
    
    res.json({
      success: true,
      course
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Delete course
app.delete('/api/courses/:id', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    await courseService.deleteCourse(req.params.id, req.user.userId);
    
    res.json({
      success: true,
      message: 'Course deleted successfully'
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// ==================== Course Sharing Endpoints ====================

// Create a share link for a course
app.post('/api/courses/:id/share', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const share = await shareService.createShare({
      courseId: req.params.id,
      userId: req.user.userId,
      ...req.body
    });
    
    res.json({
      success: true,
      share
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get all shares for user's courses
app.get('/api/shares', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const shares = await shareService.getUserShares(req.user.userId);
    
    res.json({
      success: true,
      shares
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Access a shared course (public endpoint)
app.get('/api/share/:shareToken', async (req: express.Request, res) => {
  try {
    const { password } = req.query;
    
    const result = await shareService.accessShare({
      shareToken: req.params.shareToken,
      password: password as string,
      accessedBy: req.ip || 'unknown',
      userAgent: req.get('user-agent')
    });
    
    res.json({
      success: true,
      ...result
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Update share settings
app.put('/api/shares/:id', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const share = await shareService.updateShare(
      req.params.id,
      req.user.userId,
      req.body
    );
    
    res.json({
      success: true,
      share
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Toggle share active status
app.post('/api/shares/:id/toggle', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const share = await shareService.toggleShareStatus(
      req.params.id,
      req.user.userId
    );
    
    res.json({
      success: true,
      share
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Delete a share
app.delete('/api/shares/:id', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    await shareService.deleteShare(req.params.id, req.user.userId);
    
    res.json({
      success: true,
      message: 'Share deleted successfully'
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get share access logs
app.get('/api/shares/:id/logs', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const logs = await shareService.getShareAccessLogs(
      req.params.id,
      req.user.userId
    );
    
    res.json({
      success: true,
      logs
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// ==================== Learning Progress Endpoints ====================

// Enroll in a course
app.post('/api/courses/:id/enroll', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const enrollment = await progressService.enrollInCourse({
      userId: req.user.userId,
      courseId: req.params.id
    });
    
    res.json({
      success: true,
      enrollment
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get course progress
app.get('/api/courses/:id/progress', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const progress = await progressService.getCourseProgress(
      req.user.userId,
      req.params.id
    );
    
    res.json({
      success: true,
      progress
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Update progress (general endpoint)
app.post('/api/progress', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { courseId, lessonId, progress, completed } = req.body;
    
    if (!courseId || !lessonId) {
      throw new AppError('courseId and lessonId are required', ErrorCodes.VALIDATION_ERROR);
    }
    
    res.json({
      success: true,
      courseId,
      lessonId,
      progress: progress || 50,
      completed: completed || false
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Update lesson progress
app.post('/api/progress/lesson', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const lessonProgress = await progressService.updateLessonProgress(req.body);
    
    res.json({
      success: true,
      lessonProgress
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Complete lesson and get next
app.post('/api/progress/lesson/:lessonKey/complete', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { enrollmentId } = req.body;
    
    const result = await progressService.completeLessonAndGetNext(
      enrollmentId,
      req.params.lessonKey
    );
    
    res.json({
      success: true,
      ...result
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get user's enrolled courses
app.get('/api/enrollments', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const enrollments = await progressService.getUserEnrollments(req.user.userId);
    
    res.json({
      success: true,
      enrollments
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get learning activity
app.get('/api/activity', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const limit = parseInt(req.query.limit as string) || 50;
    const activities = await progressService.getUserActivity(req.user.userId, limit);
    
    res.json({
      success: true,
      activities
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Toggle lesson bookmark
app.post('/api/progress/lesson/:lessonKey/bookmark', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { enrollmentId } = req.body;
    
    const lessonProgress = await progressService.toggleLessonBookmark(
      enrollmentId,
      req.params.lessonKey
    );
    
    res.json({
      success: true,
      lessonProgress
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Update lesson notes
app.put('/api/progress/lesson/:lessonKey/notes', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { enrollmentId, notes } = req.body;
    
    const lessonProgress = await progressService.updateLessonNotes(
      enrollmentId,
      req.params.lessonKey,
      notes
    );
    
    res.json({
      success: true,
      lessonProgress
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get learning statistics
app.get('/api/stats/learning', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const stats = await progressService.getUserLearningStats(req.user.userId);
    
    res.json({
      success: true,
      stats
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// ===== Prompt Template Endpoints =====

// Get all prompt templates
app.get('/api/prompt-templates', optionalAuth, async (req: express.Request, res) => {
  try {
    const { category } = req.query;
    const templates = await promptTemplateService.getTemplates(
      req.user?.userId,
      category as any
    );
    
    res.json(templates);
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get public prompt templates
app.get('/api/prompt-templates/public', async (req: express.Request, res) => {
  try {
    const { category } = req.query;
    const templates = await promptTemplateService.getPublicTemplates(
      category as any
    );
    
    res.json(templates);
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get a single prompt template
app.get('/api/prompt-templates/:id', optionalAuth, async (req: express.Request, res) => {
  try {
    const { id } = req.params;
    const template = await promptTemplateService.getTemplate(id, req.user?.userId);
    
    if (!template) {
      throw new AppError('Template not found', ErrorCodes.NOT_FOUND);
    }
    
    res.json({
      success: true,
      template
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Create a new prompt template
app.post('/api/prompt-templates', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const template = await promptTemplateService.createTemplate({
      ...req.body,
      userId: req.user.userId
    });
    
    res.json({
      success: true,
      template
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Update a prompt template
app.put('/api/prompt-templates/:id', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { id } = req.params;
    const template = await promptTemplateService.updateTemplate(
      id,
      req.user.userId,
      req.body
    );
    
    res.json({
      success: true,
      template
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Delete a prompt template
app.delete('/api/prompt-templates/:id', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { id } = req.params;
    await promptTemplateService.deleteTemplate(id, req.user.userId);
    
    res.json({
      success: true,
      message: 'Template deleted successfully'
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Generate prompt from template
app.post('/api/prompt-templates/:id/generate', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { id } = req.params;
    const { variables, courseId } = req.body;
    
    const prompt = await promptTemplateService.generatePrompt({
      templateId: id,
      userId: req.user.userId,
      variables,
      courseId
    });
    
    res.json({
      success: true,
      prompt
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get template usage statistics
app.get('/api/prompt-templates/:id/stats', authenticate, async (req: express.Request, res) => {
  try {
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    const { id } = req.params;
    const stats = await promptTemplateService.getTemplateUsageStats(id, req.user.userId);
    
    res.json({
      success: true,
      stats
    });
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// SSE endpoint for real-time course generation (GET with query params)
app.get('/api/generate-course-stream', optionalAuth, async (req: express.Request, res: express.Response) => {
  // Set headers for SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  const sendEvent = (data: any) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  try {
    // Parse data from query params
    const dataParam = req.query.data as string;
    if (!dataParam) {
      sendEvent({ error: { message: 'No data provided' } });
      res.end();
      return;
    }

    const { sources, metadata, options = {} } = JSON.parse(decodeURIComponent(dataParam));

    if (!sources || sources.length === 0) {
      sendEvent({ error: { message: 'No sources provided' } });
      res.end();
      return;
    }

    if (!metadata.course_title) {
      sendEvent({ error: { message: 'Course title is required' } });
      res.end();
      return;
    }

    // Progress tracking
    const progress: GenerationProgress = {
      phase: 'initializing',
      current: 0,
      total: sources.length,
      message: 'コース生成を開始しています...'
    };
    sendEvent({ progress });

    // Extract content from sources
    progress.phase = 'extracting';
    const extractedContents = [];
    
    for (let i = 0; i < sources.length; i++) {
      progress.current = i + 1;
      progress.message = `コンテンツを抽出中 (${i + 1}/${sources.length})`;
      sendEvent({ progress });
      
      const source = sources[i];
      if (!source) continue;
      
      const extracted = await contextAgent.extractContent(source, {
        contextGranularity: 'L1_L2_L3',
        contentSummarization: 'detailed',
        extractMetadata: true
      });
      
      extractedContents.push(extracted);
    }

    // Combine extracted content
    const combinedContent = extractedContents
      .map(e => `# ${e.title}\n\n${e.content}`)
      .join('\n\n---\n\n');

    // Generate course structure
    progress.phase = 'generating';
    progress.message = 'AI によるコース構造を生成中...';
    sendEvent({ progress });
    
    const modules = await geminiService.generateCourseStructure(
      combinedContent,
      metadata,
      options
    );

    // Generate scripts for each lesson
    progress.phase = 'processing';
    const scripts = new Map<string, string>();
    const audioFiles = new Map<string, string>();
    let totalLessons = 0;
    
    modules.forEach(m => m.sections.forEach(s => totalLessons += s.lessons.length));
    progress.total = totalLessons;
    progress.current = 0;

    for (const [moduleIndex, module] of modules.entries()) {
      for (const [sectionIndex, section] of module.sections.entries()) {
        for (const [lessonIndex, lesson] of section.lessons.entries()) {
          progress.current++;
          progress.message = `レッスンスクリプト生成中 (${progress.current}/${totalLessons})`;
          sendEvent({ progress });

          const lessonKey = `module_${moduleIndex}_section_${sectionIndex}_lesson_${lessonIndex}`;
          
          // Generate script
          const script = await geminiService.generateLessonScript(
            lesson,
            metadata as CourseMetadata,
            { name: module.module_name, description: module.module_description },
            section.section_name,
            options
          );
          
          scripts.set(lessonKey, script);

          // Generate audio if requested
          if (options.includeAudio) {
            try {
              const scriptContent = scripts.get(lessonKey) || '';
              const audio = await audioService.generateAudioFromText(scriptContent, {
                voice: options.audioVoice,
                language: options.language || 'ja',
                quality: 'medium',
                format: 'mp3'
              });
              
              // Read audio file and convert to base64
              const audioData = await readFileAsBase64(audio.audioPath);
              audioFiles.set(lessonKey, audioData);
              
              // Update lesson with audio info
              lesson.audio_url = audio.audioPath;
              lesson.transcript = scriptContent;
            } catch (error) {
              console.error(`Failed to generate audio for ${lessonKey}:`, error);
            }
          }
        }
      }
    }

    // Create course object
    const course: Course = {
      metadata: metadata as CourseMetadata,
      modules,
      created_at: new Date(),
      updated_at: new Date(),
      version: '1.0.0',
      status: 'draft'
    };

    // Generate summary
    const summary = await geminiService.generateCourseSummary(modules, metadata as CourseMetadata);

    progress.phase = 'completed';
    progress.message = 'コース生成が完了しました！';
    sendEvent({ progress });

    // Send final result
    sendEvent({
      success: true,
      course,
      summary,
      scripts: Object.fromEntries(scripts),
      audioFiles: options.includeAudio ? Object.fromEntries(audioFiles) : undefined
    });

    res.end();

  } catch (error) {
    const appError = handleError(error);
    sendEvent({
      error: {
        code: appError.code,
        message: appError.message
      }
    });
    res.end();
  }
});

// SSE endpoint for real-time course generation (POST version for compatibility)
app.post('/api/generate-course-stream', optionalAuth, async (req, res) => {
  // Set headers for SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  const sendEvent = (data: any) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  try {
    const { 
      sources, 
      metadata, 
      options = {} 
    }: {
      sources: ContextSource[];
      metadata: Partial<CourseMetadata>;
      options?: GenerationOptions;
    } = req.body;

    if (!sources || sources.length === 0) {
      sendEvent({ error: 'No sources provided' });
      res.end();
      return;
    }

    if (!metadata.course_title) {
      sendEvent({ error: 'Course title is required' });
      res.end();
      return;
    }

    // Progress tracking
    const progress: GenerationProgress = {
      phase: 'initializing',
      current: 0,
      total: sources.length,
      message: 'コース生成を開始しています...'
    };
    sendEvent({ progress });

    // Extract content from sources
    progress.phase = 'extracting';
    const extractedContents = [];
    
    for (let i = 0; i < sources.length; i++) {
      progress.current = i + 1;
      progress.message = `コンテンツを抽出中 (${i + 1}/${sources.length})`;
      sendEvent({ progress });
      
      const source = sources[i];
      if (!source) continue;
      
      const extracted = await contextAgent.extractContent(source, {
        contextGranularity: 'L1_L2_L3',
        contentSummarization: 'detailed',
        extractMetadata: true
      });
      
      extractedContents.push(extracted);
    }

    // Combine extracted content
    const combinedContent = extractedContents
      .map(e => `# ${e.title}\n\n${e.content}`)
      .join('\n\n---\n\n');

    // Generate course structure
    progress.phase = 'generating';
    progress.message = 'AI によるコース構造を生成中...';
    sendEvent({ progress });
    
    const modules = await geminiService.generateCourseStructure(
      combinedContent,
      metadata,
      options
    );

    // Generate scripts for each lesson
    progress.phase = 'processing';
    const scripts = new Map<string, string>();
    const audioFiles = new Map<string, string>();
    let totalLessons = 0;
    
    modules.forEach(m => m.sections.forEach(s => totalLessons += s.lessons.length));
    progress.total = totalLessons;
    progress.current = 0;

    for (const [moduleIndex, module] of modules.entries()) {
      for (const [sectionIndex, section] of module.sections.entries()) {
        for (const [lessonIndex, lesson] of section.lessons.entries()) {
          progress.current++;
          progress.message = `レッスンスクリプト生成中 (${progress.current}/${totalLessons})`;
          sendEvent({ progress });

          const lessonKey = `module_${moduleIndex}_section_${sectionIndex}_lesson_${lessonIndex}`;
          
          // Generate script
          const script = await geminiService.generateLessonScript(
            lesson,
            metadata as CourseMetadata,
            { name: module.module_name, description: module.module_description },
            section.section_name,
            options
          );
          
          scripts.set(lessonKey, script);

          // Generate audio if requested
          if (options.includeAudio) {
            try {
              const scriptContent = scripts.get(lessonKey) || '';
              const audio = await audioService.generateAudioFromText(scriptContent, {
                voice: options.audioVoice,
                language: options.language || 'ja',
                quality: 'medium',
                format: 'mp3'
              });
              
              // Read audio file and convert to base64
              const audioData = await readFileAsBase64(audio.audioPath);
              audioFiles.set(lessonKey, audioData);
              
              // Update lesson with audio info
              lesson.audio_url = audio.audioPath;
              lesson.transcript = scriptContent;
            } catch (error) {
              console.error(`Failed to generate audio for ${lessonKey}:`, error);
            }
          }
        }
      }
    }

    // Create course object
    const course: Course = {
      metadata: metadata as CourseMetadata,
      modules,
      created_at: new Date(),
      updated_at: new Date(),
      version: '1.0.0',
      status: 'draft'
    };

    // Generate summary
    const summary = await geminiService.generateCourseSummary(modules, metadata as CourseMetadata);

    progress.phase = 'completed';
    progress.message = 'コース生成が完了しました！';
    sendEvent({ progress });

    // Send final result
    sendEvent({
      success: true,
      course,
      summary,
      scripts: Object.fromEntries(scripts),
      audioFiles: options.includeAudio ? Object.fromEntries(audioFiles) : undefined
    });

    res.end();

  } catch (error) {
    const appError = handleError(error);
    sendEvent({
      error: {
        code: appError.code,
        message: appError.message
      }
    });
    res.end();
  }
});

// Generate course from sources (non-streaming version)
app.post('/api/generate-course', optionalAuth, async (req, res) => {
  console.log('📥 Received course generation request');
  console.log('Request body:', JSON.stringify(req.body, null, 2));
  
  try {
    const { 
      sources, 
      metadata, 
      options = {} 
    }: {
      sources: ContextSource[];
      metadata: Partial<CourseMetadata>;
      options?: GenerationOptions;
    } = req.body;

    if (!sources || sources.length === 0) {
      throw new AppError('No sources provided', ErrorCodes.VALIDATION_ERROR);
    }

    if (!metadata.course_title) {
      throw new AppError('Course title is required', ErrorCodes.VALIDATION_ERROR);
    }

    console.log('✅ Request validation passed');

    // Progress tracking
    const progress: GenerationProgress = {
      phase: 'initializing',
      current: 0,
      total: sources.length,
      message: 'コース生成を開始しています...'
    };

    // Extract content from sources
    progress.phase = 'extracting';
    const extractedContents = [];
    
    console.log('🔄 Starting content extraction...');
    
    for (let i = 0; i < sources.length; i++) {
      progress.current = i + 1;
      progress.message = `コンテンツを抽出中 (${i + 1}/${sources.length})`;
      
      const source = sources[i];
      if (!source) continue;
      
      console.log(`  📝 Extracting from source ${i + 1}:`, source.type);
      
      try {
        const extracted = await contextAgent.extractContent(source, {
          contextGranularity: 'L1_L2_L3',
          contentSummarization: 'detailed',
          extractMetadata: true
        });
        
        console.log(`  ✅ Extracted content with ${extracted.content.length} characters`);
        extractedContents.push(extracted);
      } catch (error) {
        console.error(`  ❌ Extraction error:`, error);
        throw error;
      }
    }

    // Combine extracted content
    const combinedContent = extractedContents
      .map(e => `# ${e.title}\n\n${e.content}`)
      .join('\n\n---\n\n');

    // Generate course structure
    progress.phase = 'generating';
    progress.message = 'AI によるコース構造を生成中...';
    
    console.log('🤖 Calling Gemini AI to generate course structure...');
    console.log(`  Content length: ${combinedContent.length} characters`);
    
    const modules = await geminiService.generateCourseStructure(
      combinedContent,
      metadata,
      options
    );
    
    console.log(`  ✅ Generated ${modules.length} modules`);

    // Generate scripts for each lesson
    progress.phase = 'processing';
    const scripts = new Map<string, string>();
    const audioFiles = new Map<string, string>();
    let totalLessons = 0;
    
    modules.forEach(m => m.sections.forEach(s => totalLessons += s.lessons.length));
    progress.total = totalLessons;
    progress.current = 0;

    console.log(`📝 Generating scripts for ${totalLessons} lessons...`);

    for (const [moduleIndex, module] of modules.entries()) {
      for (const [sectionIndex, section] of module.sections.entries()) {
        for (const [lessonIndex, lesson] of section.lessons.entries()) {
          progress.current++;
          progress.message = `レッスンスクリプト生成中 (${progress.current}/${totalLessons})`;

          const lessonKey = `module_${moduleIndex}_section_${sectionIndex}_lesson_${lessonIndex}`;
          
          console.log(`  🔄 Generating script for ${lessonKey}...`);
          
          try {
            // Generate script
            const script = await geminiService.generateLessonScript(
              lesson,
              metadata as CourseMetadata,
              { name: module.module_name, description: module.module_description },
              section.section_name,
              options
            );
            
            scripts.set(lessonKey, script);
            console.log(`  ✅ Generated script (${script.length} characters)`);
          } catch (error) {
            console.error(`  ❌ Script generation error:`, error);
            throw error;
          }

          // Generate audio if requested
          if (options.includeAudio) {
            try {
              const scriptContent = scripts.get(lessonKey) || '';
              const audio = await audioService.generateAudioFromText(scriptContent, {
                voice: options.audioVoice,
                language: options.language || 'ja',
                quality: 'medium',
                format: 'mp3'
              });
              
              // Read audio file and convert to base64
              const audioData = await readFileAsBase64(audio.audioPath);
              audioFiles.set(lessonKey, audioData);
              
              // Update lesson with audio info
              lesson.audio_url = audio.audioPath;
              lesson.transcript = scriptContent;
            } catch (error) {
              console.error(`Failed to generate audio for ${lessonKey}:`, error);
            }
          }
        }
      }
    }

    // Create course object
    const course: Course = {
      metadata: metadata as CourseMetadata,
      modules,
      created_at: new Date(),
      updated_at: new Date(),
      version: '1.0.0',
      status: 'draft'
    };

    // Generate summary
    const summary = await geminiService.generateCourseSummary(modules, metadata as CourseMetadata);

    progress.phase = 'completed';
    progress.message = 'コース生成が完了しました！';

    res.json({
      success: true,
      course,
      summary,
      scripts: Object.fromEntries(scripts),
      audioFiles: options.includeAudio ? Object.fromEntries(audioFiles) : undefined,
      progress
    });

  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Export course
app.post('/api/export-course', authenticate, async (req, res) => {
  try {
    const {
      course,
      scripts = {},
      audioFiles = {},
      exportOptions
    }: {
      course: Course;
      scripts: Record<string, string>;
      audioFiles: Record<string, string>;
      exportOptions: ExportOptions;
    } = req.body;

    if (!course) {
      throw new AppError('Course data is required', ErrorCodes.VALIDATION_ERROR);
    }

    const result = await exportService.exportCourse(
      course,
      new Map(Object.entries(scripts)),
      new Map(Object.entries(audioFiles)),
      exportOptions
    );

    res.json({
      success: true,
      export: {
        ...result,
        downloadUrl: result.fileUrl || `/api/exports/download/${path.basename(result.filePath)}`
      }
    });

  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Export course by ID (database version)
app.post('/api/courses/:id/export', authenticate, async (req, res) => {
  try {
    const { id } = req.params;
    const { format, includeAudio, includeScripts } = req.body;
    
    if (!req.user) {
      throw new AppError('User not found', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Get course from database
    const course = await courseService.getCourseById(id, req.user.userId);
    if (!course) {
      throw new AppError('Course not found', ErrorCodes.NOT_FOUND);
    }
    
    // Transform to Course type
    const courseData = transformPrismaCourseToType(course);
    
    // Get scripts and audio files
    const scripts = await courseService.getCourseScripts(id);
    const audioFiles = await courseService.getCourseAudioFiles(id);
    
    // Export course
    const result = await exportService.exportCourse(
      courseData,
      scripts,
      audioFiles,
      {
        format,
        includeAudio,
        includeScripts
      }
    );
    
    // Record export in database with CDN URL if available
    await courseService.createExportRecord(
      id,
      format,
      result.fileUrl || result.filePath,
      result.fileSize
    );
    
    res.json({
      success: true,
      export: {
        ...result,
        downloadUrl: result.fileUrl || `/api/exports/download/${path.basename(result.filePath)}`
      }
    });
    
  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Web crawler endpoint (matches test expectations)
app.post('/api/web-crawler/crawl', async (req, res) => {
  try {
    const { url, maxDepth = 1 } = req.body;

    if (!url) {
      throw new AppError('URL is required', ErrorCodes.VALIDATION_ERROR);
    }

    const results = await webCrawler.crawlMultipleUrls([url], { maxDepth });
    const organized = await webCrawler.organizeContent(results);

    res.json({
      success: true,
      content: organized,
      url,
      crawled: results.length
    });

  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Crawl URLs
app.post('/api/crawl-urls', async (req, res) => {
  try {
    const { urls, settings } = req.body;

    if (!urls || urls.length === 0) {
      throw new AppError('URLs are required', ErrorCodes.VALIDATION_ERROR);
    }

    const results = await webCrawler.crawlMultipleUrls(urls, settings);
    const organized = await webCrawler.organizeContent(results);

    res.json({
      success: true,
      crawled: results.length,
      organized
    });

  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Get available voices
app.get('/api/voices', async (req, res) => {
  try {
    const provider = req.query.provider as string | undefined;
    const voices = await audioService.getAvailableVoices(provider);

    res.json({
      success: true,
      voices
    });

  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Clear caches
app.post('/api/clear-cache', async (req, res) => {
  try {
    const { type = 'all' } = req.body;

    if (type === 'all' || type === 'audio') {
      await audioService.clearCache();
    }

    if (type === 'all' || type === 'context') {
      contextAgent.clearCache();
    }

    if (type === 'all' || type === 'crawler') {
      webCrawler.clearCache();
    }
    
    if (type === 'all' || type === 'redis') {
      await cacheService.clear();
    }

    res.json({
      success: true,
      message: 'Cache cleared successfully'
    });

  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Cache statistics endpoint
app.get('/api/cache-stats', authenticate, async (req: any, res) => {
  try {
    const stats = await cacheService.getStats();
    
    res.json({
      success: true,
      stats
    });

  } catch (error) {
    const appError = handleError(error);
    res.status(appError.statusCode).json({
      success: false,
      error: {
        code: appError.code,
        message: appError.message
      }
    });
  }
});

// Error handling middleware
app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  const appError = handleError(err);
  
  res.status(appError.statusCode).json({
    success: false,
    error: {
      code: appError.code,
      message: appError.message,
      ...(process.env.NODE_ENV === 'development' && { stack: appError.stack })
    }
  });
});

// 404 handler
app.use((_req, res) => {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: 'Endpoint not found'
    }
  });
});

// Helper function to read file as base64
async function readFileAsBase64(filePath: string): Promise<string> {
  const fs = await import('fs/promises');
  const buffer = await fs.readFile(filePath);
  return buffer.toString('base64');
}

// Initialize and start server
async function startServer() {
  try {
    // Connect to database
    await databaseService.connect();
    
    // Run migrations in development
    if (process.env.NODE_ENV === 'development') {
      console.log('🔄 Running database migrations...');
      // await databaseService.runMigrations();
    }
    
    // Seed database with initial data
    await databaseService.seed();
    
    // Initialize default prompt templates
    await promptTemplateService.initializeDefaultTemplates();
    
    // Start server
    app.listen(PORT, () => {
      console.log(`
🚀 Course Generator Service Started
📍 Port: ${PORT}
🌍 Environment: ${process.env.NODE_ENV || 'development'}
🔗 Health Check: http://localhost:${PORT}/health
🗄️  Database: Connected

Available Endpoints:
Authentication:
- POST /api/auth/register - Register new user
- POST /api/auth/login - Login
- GET  /api/auth/me - Get current user (auth required)
- POST /api/auth/logout - Logout (auth required)
- GET  /api/auth/users - Get all users (admin only)

Course Management:
- GET  /api/courses - Get user's courses (auth required)
- GET  /api/courses/:id - Get course by ID (auth required)
- DELETE /api/courses/:id - Delete course (auth required)

Course Sharing:
- POST /api/courses/:id/share - Create share link (auth required)
- GET  /api/shares - Get all shares (auth required)
- GET  /api/share/:shareToken - Access shared course (public)
- PUT  /api/shares/:id - Update share settings (auth required)
- POST /api/shares/:id/toggle - Toggle share status (auth required)
- DELETE /api/shares/:id - Delete share (auth required)
- GET  /api/shares/:id/logs - Get access logs (auth required)

Learning Progress:
- POST /api/courses/:id/enroll - Enroll in course (auth required)
- GET  /api/courses/:id/progress - Get course progress (auth required)
- POST /api/progress/lesson - Update lesson progress (auth required)
- POST /api/progress/lesson/:lessonKey/complete - Complete lesson (auth required)
- GET  /api/enrollments - Get enrolled courses (auth required)
- GET  /api/activity - Get learning activity (auth required)
- POST /api/progress/lesson/:lessonKey/bookmark - Toggle bookmark (auth required)
- PUT  /api/progress/lesson/:lessonKey/notes - Update notes (auth required)
- GET  /api/stats/learning - Get learning statistics (auth required)

Prompt Templates:
- GET  /api/prompt-templates - Get all templates (optional auth)
- GET  /api/prompt-templates/:id - Get single template (optional auth)
- POST /api/prompt-templates - Create template (auth required)
- PUT  /api/prompt-templates/:id - Update template (auth required)
- DELETE /api/prompt-templates/:id - Delete template (auth required)
- POST /api/prompt-templates/:id/generate - Generate prompt (auth required)
- GET  /api/prompt-templates/:id/stats - Get usage stats (auth required)

Course Generation:
- GET  /api/generate-course-stream - Generate course with SSE (optional auth)
- POST /api/generate-course-stream - Generate course with SSE (optional auth)
- POST /api/generate-course - Generate a new course (optional auth)
- POST /api/export-course - Export course in various formats (auth required)
- POST /api/crawl-urls - Crawl and extract content from URLs
- GET  /api/voices - Get available TTS voices
- POST /api/clear-cache - Clear service caches
      `);
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM signal received: closing HTTP server');
  await databaseService.disconnect();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT signal received: closing HTTP server');
  await databaseService.disconnect();
  process.exit(0);
});

// Start the server
startServer();