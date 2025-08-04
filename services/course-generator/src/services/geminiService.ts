/**
 * Gemini AI Service
 * Ultimate ShunsukeModel Ecosystem
 */

import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import type { CourseMetadata, Lesson, Module, GenerationOptions } from '../types';
import { AppError } from '../utils/errors';
import { RateLimiter } from '../utils/rateLimiter';

export class GeminiService {
  private genAI: GoogleGenerativeAI;
  private model: GenerativeModel;
  private rateLimiter: RateLimiter;
  
  constructor(apiKey: string) {
    if (!apiKey) {
      throw new AppError('Gemini API key is required', 'CONFIG_ERROR');
    }
    
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({ 
      model: 'gemini-1.5-pro-latest',
      generationConfig: {
        temperature: 0.7,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 8192,
      }
    });
    
    // Rate limiter: 60 requests per minute
    this.rateLimiter = new RateLimiter(60, 60000);
  }

  /**
   * Generate course structure from extracted content
   */
  async generateCourseStructure(
    content: string,
    metadata: Partial<CourseMetadata>,
    options?: GenerationOptions
  ): Promise<Module[]> {
    await this.rateLimiter.acquire();
    
    const prompt = this.buildCourseStructurePrompt(content, metadata, options);
    
    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      const text = response.text();
      
      return this.parseCourseStructure(text);
    } catch (error) {
      throw new AppError(
        `Failed to generate course structure: ${error.message}`,
        'AI_GENERATION_ERROR',
        error
      );
    }
  }

  /**
   * Generate script for a lesson
   */
  async generateLessonScript(
    lesson: Lesson,
    metadata: CourseMetadata,
    moduleContext: { name: string; description: string },
    sectionName: string,
    options?: GenerationOptions
  ): Promise<string> {
    await this.rateLimiter.acquire();
    
    const prompt = this.buildLessonScriptPrompt(
      lesson,
      metadata,
      moduleContext,
      sectionName,
      options
    );
    
    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      return response.text().trim();
    } catch (error) {
      throw new AppError(
        `Failed to generate lesson script: ${error.message}`,
        'AI_GENERATION_ERROR',
        error
      );
    }
  }

  /**
   * Generate course summary
   */
  async generateCourseSummary(
    modules: Module[],
    metadata: CourseMetadata
  ): Promise<string> {
    await this.rateLimiter.acquire();
    
    const prompt = this.buildSummaryPrompt(modules, metadata);
    
    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      return response.text().trim();
    } catch (error) {
      throw new AppError(
        `Failed to generate course summary: ${error.message}`,
        'AI_GENERATION_ERROR',
        error
      );
    }
  }

  private buildCourseStructurePrompt(
    content: string,
    metadata: Partial<CourseMetadata>,
    options?: GenerationOptions
  ): string {
    const language = options?.language || 'ja';
    const customPrompt = options?.customPrompt || '';
    
    return `
あなたは教育コンテンツ設計の専門家です。以下の内容から構造化されたオンラインコースを作成してください。

【講師プロフィール】
- 専門分野: ${metadata.specialty_field || '未指定'}
- 職業: ${metadata.profession || '教育者'}
- ペルソナ: ${metadata.avatar || 'プロフェッショナル'}
- トーン: ${metadata.tone_of_voice || 'フレンドリーで分かりやすい'}
- 対象者: ${metadata.target_audience || '一般学習者'}
- 難易度: ${metadata.difficulty_level || 'intermediate'}

【ソースコンテンツ】
${content}

${customPrompt}

【要求事項】
1. モジュール（大単元）を3-5個作成
2. 各モジュールに2-4個のセクション（中単元）を作成
3. 各セクションに2-5個のレッスン（小単元）を作成
4. 各レッスンは5-15分程度の長さ
5. 論理的な学習順序に配慮
6. 実践的な内容を含める

以下のJSON形式で出力してください：
{
  "modules": [
    {
      "module_name": "モジュール名",
      "module_description": "モジュールの説明",
      "sections": [
        {
          "section_name": "セクション名",
          "lessons": [
            {
              "lesson_title": "レッスンタイトル",
              "script_length_minutes": "10"
            }
          ]
        }
      ]
    }
  ]
}`;
  }

  private buildLessonScriptPrompt(
    lesson: Lesson,
    metadata: CourseMetadata,
    moduleContext: { name: string; description: string },
    sectionName: string,
    options?: GenerationOptions
  ): string {
    return `
あなたは「${metadata.specialty_field}」の専門家で、${metadata.profession}として活動している「${metadata.avatar}」です。

【コース情報】
- コースタイトル: ${metadata.course_title}
- コース説明: ${metadata.course_description}
- モジュール: ${moduleContext.name}
- セクション: ${sectionName}
- レッスン: ${lesson.lesson_title}
- 長さ: ${lesson.script_length_minutes}分

【話し方の特徴】
${metadata.tone_of_voice}

【タスク】
このレッスンの完全なスクリプトを作成してください。

【要求事項】
1. 指定された長さ（${lesson.script_length_minutes}分）に適した内容量
2. 導入→本編→まとめの構成
3. 具体例や実践的なアドバイスを含める
4. 聞き手を引き込む話し方
5. 専門用語は分かりやすく説明
6. 次のレッスンへの期待を持たせる締めくくり

音声ナレーション用のスクリプトとして、自然な話し言葉で書いてください。`;
  }

  private buildSummaryPrompt(
    modules: Module[],
    metadata: CourseMetadata
  ): string {
    const moduleList = modules.map(m => 
      `- ${m.module_name}: ${m.sections.length}セクション`
    ).join('\n');
    
    return `
以下のコース構成から、魅力的なコース概要を作成してください。

【コース情報】
タイトル: ${metadata.course_title}
説明: ${metadata.course_description}

【モジュール構成】
${moduleList}

【要求事項】
1. コースの全体像が分かる
2. 学習者が得られる成果を明確に
3. 各モジュールの重要性を説明
4. 200-300文字程度
5. 魅力的で期待感を持たせる内容`;
  }

  private parseCourseStructure(text: string): Module[] {
    try {
      // JSONブロックを抽出
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in response');
      }
      
      const parsed = JSON.parse(jsonMatch[0]);
      
      if (!parsed.modules || !Array.isArray(parsed.modules)) {
        throw new Error('Invalid course structure format');
      }
      
      return parsed.modules;
    } catch (error) {
      throw new AppError(
        'Failed to parse course structure',
        'PARSE_ERROR',
        error
      );
    }
  }
}