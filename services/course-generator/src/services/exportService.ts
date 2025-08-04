/**
 * Export Service
 * Ultimate ShunsukeModel Ecosystem
 * 
 * Multi-format course content export service
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import archiver from 'archiver';
import PDFDocument from 'pdfkit';
import { Course, Module, Section, Lesson } from '../types';
import { AppError, ErrorCodes } from '../utils/errors';

export interface ExportOptions {
  includeAudio?: boolean;
  includeScripts?: boolean;
  includeMetadata?: boolean;
  format: 'json' | 'markdown' | 'html' | 'pdf' | 'scorm' | 'zip';
  outputPath?: string;
}

export interface ExportResult {
  success: boolean;
  filePath: string;
  format: string;
  fileSize: number;
  exportedAt: Date;
}

export class ExportService {
  private outputDirectory: string;

  constructor(outputDir: string = './exports') {
    this.outputDirectory = outputDir;
    this.initializeOutputDirectory();
  }

  /**
   * Initialize output directory
   */
  private async initializeOutputDirectory(): Promise<void> {
    try {
      await fs.mkdir(this.outputDirectory, { recursive: true });
    } catch (error) {
      console.error('Failed to create output directory:', error);
    }
  }

  /**
   * Export course in specified format
   */
  async exportCourse(
    course: Course,
    scripts: Map<string, string>,
    audioFiles: Map<string, string>,
    options: ExportOptions
  ): Promise<ExportResult> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const courseName = this.sanitizeFilename(course.metadata.course_title);
    const baseFileName = `${courseName}_${timestamp}`;
    const outputPath = options.outputPath || this.outputDirectory;

    try {
      let filePath: string;

      switch (options.format) {
        case 'json':
          filePath = await this.exportAsJSON(course, scripts, audioFiles, baseFileName, outputPath, options);
          break;
        case 'markdown':
          filePath = await this.exportAsMarkdown(course, scripts, baseFileName, outputPath, options);
          break;
        case 'html':
          filePath = await this.exportAsHTML(course, scripts, audioFiles, baseFileName, outputPath, options);
          break;
        case 'pdf':
          filePath = await this.exportAsPDF(course, scripts, baseFileName, outputPath, options);
          break;
        case 'scorm':
          filePath = await this.exportAsSCORM(course, scripts, audioFiles, baseFileName, outputPath, options);
          break;
        case 'zip':
          filePath = await this.exportAsZIP(course, scripts, audioFiles, baseFileName, outputPath, options);
          break;
        default:
          throw new AppError(`Unsupported export format: ${options.format}`, ErrorCodes.UNSUPPORTED_FORMAT);
      }

      const stats = await fs.stat(filePath);

      return {
        success: true,
        filePath,
        format: options.format,
        fileSize: stats.size,
        exportedAt: new Date()
      };
    } catch (error) {
      throw new AppError(
        `Failed to export course as ${options.format}`,
        ErrorCodes.EXPORT_ERROR,
        error
      );
    }
  }

  /**
   * Export as JSON
   */
  private async exportAsJSON(
    course: Course,
    scripts: Map<string, string>,
    audioFiles: Map<string, string>,
    baseFileName: string,
    outputPath: string,
    options: ExportOptions
  ): Promise<string> {
    const exportData = {
      course,
      scripts: options.includeScripts ? Object.fromEntries(scripts) : {},
      audioFiles: options.includeAudio ? Object.fromEntries(audioFiles) : {},
      exportedAt: new Date().toISOString(),
      version: '1.0.0'
    };

    const filePath = path.join(outputPath, `${baseFileName}.json`);
    await fs.writeFile(filePath, JSON.stringify(exportData, null, 2));
    
    return filePath;
  }

  /**
   * Export as Markdown
   */
  private async exportAsMarkdown(
    course: Course,
    scripts: Map<string, string>,
    baseFileName: string,
    outputPath: string,
    options: ExportOptions
  ): Promise<string> {
    let markdown = `# ${course.metadata.course_title}\n\n`;
    markdown += `${course.metadata.course_description}\n\n`;
    
    if (options.includeMetadata) {
      markdown += `## コース情報\n\n`;
      markdown += `- **講師**: ${course.metadata.avatar}\n`;
      markdown += `- **専門分野**: ${course.metadata.specialty_field}\n`;
      markdown += `- **職業**: ${course.metadata.profession}\n`;
      markdown += `- **対象者**: ${course.metadata.target_audience || '一般学習者'}\n`;
      markdown += `- **難易度**: ${course.metadata.difficulty_level || '中級'}\n`;
      markdown += `- **推定学習時間**: ${course.metadata.estimated_duration || '未定'}\n\n`;
    }

    markdown += `---\n\n`;

    // Course content
    course.modules.forEach((module, moduleIndex) => {
      markdown += `## モジュール ${moduleIndex + 1}: ${module.module_name}\n\n`;
      markdown += `${module.module_description}\n\n`;

      module.sections.forEach((section, sectionIndex) => {
        markdown += `### セクション ${moduleIndex + 1}.${sectionIndex + 1}: ${section.section_name}\n\n`;
        
        if (section.description) {
          markdown += `${section.description}\n\n`;
        }

        section.lessons.forEach((lesson, lessonIndex) => {
          const lessonKey = this.generateLessonKey(moduleIndex, sectionIndex, lessonIndex);
          markdown += `#### レッスン ${lessonIndex + 1}: ${lesson.lesson_title}\n\n`;
          markdown += `**所要時間**: ${lesson.script_length_minutes}分\n\n`;

          if (options.includeScripts && scripts.has(lessonKey)) {
            markdown += `**スクリプト**:\n\n`;
            markdown += scripts.get(lessonKey) + '\n\n';
          }

          markdown += `---\n\n`;
        });
      });
    });

    const filePath = path.join(outputPath, `${baseFileName}.md`);
    await fs.writeFile(filePath, markdown, 'utf-8');
    
    return filePath;
  }

  /**
   * Export as HTML
   */
  private async exportAsHTML(
    course: Course,
    scripts: Map<string, string>,
    audioFiles: Map<string, string>,
    baseFileName: string,
    outputPath: string,
    options: ExportOptions
  ): Promise<string> {
    const html = `<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${course.metadata.course_title}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        h3 { color: #7f8c8d; }
        .metadata {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .lesson {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .script {
            background: #f5f5f5;
            padding: 10px;
            border-left: 3px solid #3498db;
            margin-top: 10px;
            white-space: pre-wrap;
        }
        audio {
            width: 100%;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h1>${course.metadata.course_title}</h1>
    <p>${course.metadata.course_description}</p>
    
    ${options.includeMetadata ? `
    <div class="metadata">
        <h2>コース情報</h2>
        <ul>
            <li><strong>講師</strong>: ${course.metadata.avatar}</li>
            <li><strong>専門分野</strong>: ${course.metadata.specialty_field}</li>
            <li><strong>対象者</strong>: ${course.metadata.target_audience || '一般学習者'}</li>
            <li><strong>難易度</strong>: ${course.metadata.difficulty_level || '中級'}</li>
        </ul>
    </div>
    ` : ''}
    
    ${course.modules.map((module, mIdx) => `
        <h2>モジュール ${mIdx + 1}: ${module.module_name}</h2>
        <p>${module.module_description}</p>
        
        ${module.sections.map((section, sIdx) => `
            <h3>セクション ${mIdx + 1}.${sIdx + 1}: ${section.section_name}</h3>
            ${section.description ? `<p>${section.description}</p>` : ''}
            
            ${section.lessons.map((lesson, lIdx) => {
                const lessonKey = this.generateLessonKey(mIdx, sIdx, lIdx);
                const script = scripts.get(lessonKey);
                const audioFile = audioFiles.get(lessonKey);
                
                return `
                <div class="lesson">
                    <h4>レッスン ${lIdx + 1}: ${lesson.lesson_title}</h4>
                    <p><strong>所要時間</strong>: ${lesson.script_length_minutes}分</p>
                    
                    ${options.includeScripts && script ? `
                        <div class="script">${this.escapeHtml(script)}</div>
                    ` : ''}
                    
                    ${options.includeAudio && audioFile ? `
                        <audio controls>
                            <source src="data:audio/mp3;base64,${audioFile}" type="audio/mp3">
                            Your browser does not support the audio element.
                        </audio>
                    ` : ''}
                </div>
                `;
            }).join('')}
        `).join('')}
    `).join('')}
    
    <footer>
        <p>エクスポート日時: ${new Date().toLocaleString('ja-JP')}</p>
    </footer>
</body>
</html>`;

    const filePath = path.join(outputPath, `${baseFileName}.html`);
    await fs.writeFile(filePath, html, 'utf-8');
    
    return filePath;
  }

  /**
   * Export as PDF
   */
  private async exportAsPDF(
    course: Course,
    scripts: Map<string, string>,
    baseFileName: string,
    outputPath: string,
    options: ExportOptions
  ): Promise<string> {
    // This would require a proper PDF generation library like pdfkit
    // For now, throwing not implemented
    throw new AppError(
      'PDF export not implemented yet',
      ErrorCodes.PROCESSING_ERROR
    );
  }

  /**
   * Export as SCORM package
   */
  private async exportAsSCORM(
    course: Course,
    scripts: Map<string, string>,
    audioFiles: Map<string, string>,
    baseFileName: string,
    outputPath: string,
    options: ExportOptions
  ): Promise<string> {
    // SCORM requires specific structure and manifest files
    // This is a simplified implementation
    throw new AppError(
      'SCORM export not implemented yet',
      ErrorCodes.PROCESSING_ERROR
    );
  }

  /**
   * Export as ZIP archive
   */
  private async exportAsZIP(
    course: Course,
    scripts: Map<string, string>,
    audioFiles: Map<string, string>,
    baseFileName: string,
    outputPath: string,
    options: ExportOptions
  ): Promise<string> {
    const archive = archiver('zip', {
      zlib: { level: 9 }
    });

    const zipPath = path.join(outputPath, `${baseFileName}.zip`);
    const output = await fs.open(zipPath, 'w');
    const stream = output.createWriteStream();

    archive.pipe(stream);

    // Add course metadata
    archive.append(JSON.stringify(course, null, 2), { name: 'course.json' });

    // Add scripts
    if (options.includeScripts) {
      for (const [key, script] of scripts) {
        archive.append(script, { name: `scripts/${key}.txt` });
      }
    }

    // Add audio files
    if (options.includeAudio) {
      for (const [key, audioData] of audioFiles) {
        archive.append(Buffer.from(audioData, 'base64'), { name: `audio/${key}.mp3` });
      }
    }

    // Add README
    const readme = this.generateReadme(course);
    archive.append(readme, { name: 'README.md' });

    await archive.finalize();
    await output.close();

    return zipPath;
  }

  /**
   * Generate README content
   */
  private generateReadme(course: Course): string {
    return `# ${course.metadata.course_title}

${course.metadata.course_description}

## コース構成

このコースは${course.modules.length}つのモジュールから構成されています。

${course.modules.map((m, i) => `${i + 1}. ${m.module_name}`).join('\n')}

## ファイル構成

- \`course.json\` - コースのメタデータと構造
- \`scripts/\` - 各レッスンのスクリプト
- \`audio/\` - 音声ファイル（含まれている場合）

## 使用方法

1. ZIPファイルを解凍
2. \`course.json\`でコース構造を確認
3. \`scripts/\`フォルダ内のテキストファイルでレッスン内容を確認
4. \`audio/\`フォルダ内の音声ファイルで学習（含まれている場合）

作成日: ${new Date().toLocaleString('ja-JP')}
`;
  }

  /**
   * Sanitize filename
   */
  private sanitizeFilename(filename: string): string {
    return filename.replace(/[^a-zA-Z0-9-_]/g, '_');
  }

  /**
   * Generate lesson key
   */
  private generateLessonKey(moduleIndex: number, sectionIndex: number, lessonIndex: number): string {
    return `module_${moduleIndex}_section_${sectionIndex}_lesson_${lessonIndex}`;
  }

  /**
   * Escape HTML special characters
   */
  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, m => map[m]);
  }
}