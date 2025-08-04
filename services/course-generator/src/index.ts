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
  ExportService
} from './services';
import { 
  CourseMetadata, 
  GenerationOptions, 
  ContextSource,
  ExportOptions,
  GenerationProgress,
  Course
} from './types';
import { AppError, ErrorCodes, handleError } from './utils/errors';

// Load environment variables
config();

// Initialize services
const geminiService = new GeminiService(process.env.GEMINI_API_KEY || '');
const contextAgent = new ContextAgent();
const webCrawler = new WebCrawlerService();
const audioService = new AudioService('./audio_cache');
const exportService = new ExportService('./exports');

// Create Express app
const app = express();
const PORT = process.env.PORT || 3002;

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN?.split(',') || '*',
  credentials: true
}));
app.use(compression());
app.use(morgan('combined'));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'course-generator',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Generate course from sources
app.post('/api/generate-course', async (req, res) => {
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
    
    for (let i = 0; i < sources.length; i++) {
      progress.current = i + 1;
      progress.message = `コンテンツを抽出中 (${i + 1}/${sources.length})`;
      
      const extracted = await contextAgent.extractContent(sources[i], {
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
              const audio = await audioService.generateAudioFromText(script, {
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
              lesson.transcript = script;
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
app.post('/api/export-course', async (req, res) => {
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
      export: result
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

// Error handling middleware
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
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
app.use((req, res) => {
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

// Start server
app.listen(PORT, () => {
  console.log(`
🚀 Course Generator Service Started
📍 Port: ${PORT}
🌍 Environment: ${process.env.NODE_ENV || 'development'}
🔗 Health Check: http://localhost:${PORT}/health

Available Endpoints:
- POST /api/generate-course - Generate a new course
- POST /api/export-course - Export course in various formats
- POST /api/crawl-urls - Crawl and extract content from URLs
- GET  /api/voices - Get available TTS voices
- POST /api/clear-cache - Clear service caches
  `);
});