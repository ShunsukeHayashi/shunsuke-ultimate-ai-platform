/**
 * Context Extraction Agent
 * Ultimate ShunsukeModel Ecosystem
 * 
 * AI-powered content extraction and structure analysis
 */

import { AppError, ErrorCodes } from '../utils/errors';
import { RateLimiter } from '../utils/rateLimiter';
import type { 
  ContextSource, 
  ExtractionResult, 
  HeadingStructure 
} from '../types';

export interface ContextExtractionOptions {
  contextGranularity?: 'L1_only' | 'L1_L2' | 'L1_L2_L3' | 'full_hierarchy';
  contentSummarization?: 'none' | 'brief' | 'detailed' | 'full';
  languageDetection?: boolean;
  extractMetadata?: boolean;
  maxDepth?: number;
}

export class ContextAgent {
  private rateLimiter: RateLimiter;
  private processedUrls = new Set<string>();

  constructor() {
    // Rate limiter for external API calls
    this.rateLimiter = new RateLimiter(30, 60000); // 30 requests per minute
  }

  /**
   * Extract structured content from various sources
   */
  async extractContent(
    source: ContextSource,
    options: ContextExtractionOptions = {}
  ): Promise<ExtractionResult> {
    await this.rateLimiter.acquire();

    try {
      switch (source.type) {
        case 'url':
          return await this.extractFromUrl(source.content, options);
        case 'text':
          return await this.extractFromText(source.content, options);
        case 'file':
          return await this.extractFromFile(source.content, options);
        case 'youtube':
          return await this.extractFromYoutube(source.content, options);
        case 'pdf':
          return await this.extractFromPdf(source.content, options);
        default:
          throw new AppError(
            `Unsupported source type: ${source.type}`,
            ErrorCodes.VALIDATION_ERROR
          );
      }
    } catch (error) {
      if (error instanceof AppError) throw error;
      
      throw new AppError(
        `Failed to extract content from ${source.type}`,
        ErrorCodes.CONTENT_EXTRACTION_ERROR,
        error
      );
    }
  }

  /**
   * Extract content from URL
   */
  private async extractFromUrl(
    url: string,
    options: ContextExtractionOptions
  ): Promise<ExtractionResult> {
    // Validate URL
    try {
      new URL(url);
    } catch {
      throw new AppError(
        'Invalid URL provided',
        ErrorCodes.INVALID_URL
      );
    }

    // Check if already processed
    if (this.processedUrls.has(url)) {
      throw new AppError(
        'URL already processed',
        ErrorCodes.VALIDATION_ERROR
      );
    }

    this.processedUrls.add(url);

    // TODO: Implement actual web scraping
    // For now, returning mock data
    return this.createMockExtractionResult(url, 'URL content', options);
  }

  /**
   * Extract content from raw text
   */
  private async extractFromText(
    text: string,
    options: ContextExtractionOptions
  ): Promise<ExtractionResult> {
    const headings = this.extractHeadings(text, options);
    const keywords = this.extractKeywords(text);
    const summary = this.generateSummary(text, options.contentSummarization);

    return {
      title: this.extractTitle(text) || 'Untitled Document',
      content: text,
      summary,
      keywords,
      headings,
      metadata: {
        sourceType: 'text',
        language: options.languageDetection ? this.detectLanguage(text) : 'ja',
        extractedAt: new Date().toISOString()
      }
    };
  }

  /**
   * Extract content from file
   */
  private async extractFromFile(
    filePath: string,
    options: ContextExtractionOptions
  ): Promise<ExtractionResult> {
    // TODO: Implement file reading
    throw new AppError(
      'File extraction not yet implemented',
      ErrorCodes.PROCESSING_ERROR
    );
  }

  /**
   * Extract content from YouTube
   */
  private async extractFromYoutube(
    url: string,
    options: ContextExtractionOptions
  ): Promise<ExtractionResult> {
    // TODO: Implement YouTube transcript extraction
    throw new AppError(
      'YouTube extraction not yet implemented',
      ErrorCodes.PROCESSING_ERROR
    );
  }

  /**
   * Extract content from PDF
   */
  private async extractFromPdf(
    filePath: string,
    options: ContextExtractionOptions
  ): Promise<ExtractionResult> {
    // TODO: Implement PDF extraction
    throw new AppError(
      'PDF extraction not yet implemented',
      ErrorCodes.PROCESSING_ERROR
    );
  }

  /**
   * Extract headings from text
   */
  private extractHeadings(
    text: string,
    options: ContextExtractionOptions
  ): HeadingStructure[] {
    const headings: HeadingStructure[] = [];
    const lines = text.split('\n');
    const granularity = options.contextGranularity || 'L1_L2';

    for (const line of lines) {
      const trimmed = line.trim();
      
      // Check for markdown headings
      if (trimmed.startsWith('#')) {
        const level = trimmed.match(/^#+/)?.[0].length || 1;
        const text = trimmed.replace(/^#+\s*/, '');
        
        if (this.shouldIncludeLevel(level, granularity)) {
          headings.push({
            level: level as 1 | 2 | 3 | 4 | 5 | 6,
            text,
            content: this.extractHeadingContent(lines, lines.indexOf(line))
          });
        }
      }
    }

    return this.buildHeadingHierarchy(headings);
  }

  /**
   * Check if heading level should be included
   */
  private shouldIncludeLevel(
    level: number,
    granularity: string
  ): boolean {
    switch (granularity) {
      case 'L1_only':
        return level === 1;
      case 'L1_L2':
        return level <= 2;
      case 'L1_L2_L3':
        return level <= 3;
      case 'full_hierarchy':
        return true;
      default:
        return level <= 2;
    }
  }

  /**
   * Extract content under a heading
   */
  private extractHeadingContent(
    lines: string[],
    startIndex: number
  ): string {
    const content: string[] = [];
    const headingLevel = lines[startIndex].match(/^#+/)?.[0].length || 1;

    for (let i = startIndex + 1; i < lines.length; i++) {
      const line = lines[i];
      const nextHeadingMatch = line.match(/^#+/);
      
      if (nextHeadingMatch && nextHeadingMatch[0].length <= headingLevel) {
        break;
      }
      
      content.push(line);
    }

    return content.join('\n').trim();
  }

  /**
   * Build hierarchical structure from flat headings
   */
  private buildHeadingHierarchy(
    headings: HeadingStructure[]
  ): HeadingStructure[] {
    const result: HeadingStructure[] = [];
    const stack: HeadingStructure[] = [];

    for (const heading of headings) {
      // Pop from stack until we find parent level
      while (stack.length > 0 && stack[stack.length - 1].level >= heading.level) {
        stack.pop();
      }

      if (stack.length === 0) {
        // Top level heading
        result.push(heading);
      } else {
        // Child heading
        const parent = stack[stack.length - 1];
        if (!parent.children) {
          parent.children = [];
        }
        parent.children.push(heading);
      }

      stack.push(heading);
    }

    return result;
  }

  /**
   * Extract keywords from text
   */
  private extractKeywords(text: string): string[] {
    // Simple keyword extraction
    const words = text.toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, ' ')
      .split(/\s+/)
      .filter(word => word.length > 3);

    const wordFreq = new Map<string, number>();
    for (const word of words) {
      wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
    }

    return Array.from(wordFreq.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word]) => word);
  }

  /**
   * Generate summary based on options
   */
  private generateSummary(
    text: string,
    level?: string
  ): string {
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [];
    
    switch (level) {
      case 'none':
        return '';
      case 'brief':
        return sentences.slice(0, 2).join(' ').trim();
      case 'detailed':
        return sentences.slice(0, 5).join(' ').trim();
      case 'full':
        return text;
      default:
        return sentences.slice(0, 3).join(' ').trim();
    }
  }

  /**
   * Extract title from text
   */
  private extractTitle(text: string): string | null {
    const lines = text.split('\n');
    
    // Look for first heading
    for (const line of lines) {
      if (line.trim().startsWith('#')) {
        return line.replace(/^#+\s*/, '').trim();
      }
    }
    
    // Use first non-empty line
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed) {
        return trimmed.slice(0, 100);
      }
    }
    
    return null;
  }

  /**
   * Detect language of text
   */
  private detectLanguage(text: string): string {
    // Simple Japanese detection
    if (/[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/.test(text)) {
      return 'ja';
    }
    return 'en';
  }

  /**
   * Create mock extraction result for testing
   */
  private createMockExtractionResult(
    source: string,
    content: string,
    options: ContextExtractionOptions
  ): ExtractionResult {
    return {
      title: `Content from ${source}`,
      content,
      summary: 'This is a mock summary for testing purposes.',
      keywords: ['test', 'mock', 'content', 'extraction'],
      headings: [
        {
          level: 1,
          text: 'Main Topic',
          content: 'Main topic content',
          children: [
            {
              level: 2,
              text: 'Subtopic',
              content: 'Subtopic content'
            }
          ]
        }
      ],
      metadata: {
        sourceType: 'url',
        url: source,
        extractedAt: new Date().toISOString(),
        language: 'ja'
      }
    };
  }

  /**
   * Clear processed URLs cache
   */
  clearCache(): void {
    this.processedUrls.clear();
  }

  /**
   * Get processing statistics
   */
  getStats(): {
    processedUrls: number;
    rateLimiterTokens: number;
  } {
    return {
      processedUrls: this.processedUrls.size,
      rateLimiterTokens: this.rateLimiter.getAvailableTokens()
    };
  }
}