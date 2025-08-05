/**
 * Course Generator Types
 * Ultimate ShunsukeModel Ecosystem
 */

export interface CourseMetadata {
  course_title: string;
  course_description: string;
  specialty_field: string;
  profession: string;
  avatar: string;
  tone_of_voice: string;
  target_audience?: string;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  estimated_duration?: string;
  language?: string;
  instructor?: {
    name?: string;
    persona?: string;
    tone?: string;
  };
}

export interface Lesson {
  lesson_title: string;
  script_length_minutes: string;
  content?: string;
  audio_url?: string;
  transcript?: string;
  resources?: Resource[];
}

export interface Resource {
  type: 'link' | 'file' | 'video' | 'document';
  title: string;
  url: string;
  description?: string;
}

export interface Section {
  section_name: string;
  lessons: Lesson[];
  description?: string;
}

export interface Module {
  module_name: string;
  module_description: string;
  sections: Section[];
}

export type CourseModule = Module;

export interface Course {
  metadata: CourseMetadata;
  modules: Module[];
  created_at: Date;
  updated_at: Date;
  version: string;
  status: 'draft' | 'published' | 'archived';
}

export interface GenerationOptions {
  includeAudio?: boolean;
  audioVoice?: string;
  includeVisuals?: boolean;
  exportFormat?: 'zip' | 'pdf' | 'scorm' | 'json';
  language?: string;
  customPrompt?: string;
  promptTemplateId?: string;
  promptVariables?: Record<string, any>;
}

export interface GenerationProgress {
  phase: 'initializing' | 'extracting' | 'generating' | 'processing' | 'completed' | 'error';
  current: number;
  total: number;
  message: string;
  details?: Record<string, any>;
}

export interface ContextSource {
  type: 'url' | 'text' | 'file' | 'youtube' | 'pdf';
  content: string;
  metadata?: Record<string, any>;
}

export interface ExtractionResult {
  title: string;
  content: string;
  summary: string;
  keywords: string[];
  headings: HeadingStructure[];
  metadata: Record<string, any>;
}

export interface HeadingStructure {
  level: 1 | 2 | 3 | 4 | 5 | 6;
  text: string;
  content: string;
  children?: HeadingStructure[];
}

export type ExportFormat = 'json' | 'markdown' | 'html' | 'pdf' | 'scorm' | 'zip';

export interface ExportOptions {
  includeAudio?: boolean;
  includeScripts?: boolean;
  includeMetadata?: boolean;
  format: ExportFormat;
  outputPath?: string;
}

// Re-export auth types
export * from './auth';