/**
 * Web Crawler Service
 * Ultimate ShunsukeModel Ecosystem
 * 
 * Intelligent web content extraction and crawling
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import { URL } from 'url';
import { AppError, ErrorCodes } from '../utils/errors';
import { RateLimiter } from '../utils/rateLimiter';
import { cacheService, CacheKeys, CacheTTL } from './cacheService';

export interface CrawlSettings {
  maxDepth?: number;
  maxPagesPerDomain?: number;
  concurrentRequests?: number;
  downloadDelay?: number;
  respectRobotsTxt?: boolean;
  excludePatterns?: string[];
  includeOnlyPatterns?: string[];
  userAgent?: string;
  timeout?: number;
}

export interface CrawlResult {
  url: string;
  title: string;
  content: string;
  metadata: {
    crawledAt: string;
    contentType: string;
    language?: string;
    author?: string;
    publishedDate?: string;
    tags?: string[];
    description?: string;
  };
  links: string[];
  headings: {
    h1: string[];
    h2: string[];
    h3: string[];
    h4: string[];
    h5: string[];
    h6: string[];
  };
}

export interface OrganizedContent {
  mainTopic: string;
  sections: Array<{
    title: string;
    content: string;
    subsections?: Array<{
      title: string;
      content: string;
    }>;
  }>;
  metadata: {
    totalPages: number;
    crawledAt: string;
    sources: string[];
  };
}

export class WebCrawlerService {
  private crawledUrls = new Set<string>();
  private urlQueue: string[] = [];
  private rateLimiter: RateLimiter;
  private defaultSettings: Required<CrawlSettings> = {
    maxDepth: 3,
    maxPagesPerDomain: 50,
    concurrentRequests: 5,
    downloadDelay: 1000,
    respectRobotsTxt: true,
    excludePatterns: [],
    includeOnlyPatterns: [],
    userAgent: 'Ultimate ShunsukeModel Bot/1.0',
    timeout: 30000
  };

  constructor() {
    // Rate limiter for crawling
    this.rateLimiter = new RateLimiter(10, 60000); // 10 requests per minute
  }

  /**
   * Crawl a single URL and extract content
   */
  async crawlUrl(url: string, settings?: CrawlSettings): Promise<CrawlResult> {
    const crawlSettings = { ...this.defaultSettings, ...settings };
    
    // Validate URL
    try {
      new URL(url);
    } catch {
      throw new AppError('Invalid URL provided', ErrorCodes.INVALID_URL);
    }

    // Check cache first
    const cacheKey = `${CacheKeys.WEB_CONTENT}${url}`;
    const cached = await cacheService.get<CrawlResult>(cacheKey);
    if (cached) {
      console.log(`Cache hit for URL: ${url}`);
      return cached;
    }

    // Check if already crawled in current session
    if (this.crawledUrls.has(url)) {
      throw new AppError(`URL already crawled: ${url}`, ErrorCodes.VALIDATION_ERROR);
    }

    // Check URL patterns
    if (!this.isUrlAllowed(url, crawlSettings)) {
      throw new AppError(`URL not allowed by patterns: ${url}`, ErrorCodes.VALIDATION_ERROR);
    }

    // Rate limiting
    await this.rateLimiter.acquire();

    try {
      const response = await axios.get(url, {
        headers: {
          'User-Agent': crawlSettings.userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'ja,en;q=0.9',
        },
        timeout: crawlSettings.timeout,
        maxRedirects: 5,
        validateStatus: (status) => status < 400
      });

      const result = this.extractContent(url, response.data, response.headers['content-type']);
      this.crawledUrls.add(url);
      
      // Cache the result
      await cacheService.set(cacheKey, result, { ttl: CacheTTL.LONG });
      
      return result;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 404) {
          throw new AppError(`Page not found: ${url}`, ErrorCodes.CONTENT_NOT_FOUND, error);
        }
        if (error.code === 'ETIMEDOUT') {
          throw new AppError(`Request timed out: ${url}`, ErrorCodes.TIMEOUT_ERROR, error);
        }
      }
      throw new AppError(`Failed to crawl URL ${url}`, ErrorCodes.NETWORK_ERROR, error);
    }
  }

  /**
   * Crawl multiple URLs with depth control
   */
  async crawlMultipleUrls(
    urls: string[], 
    settings?: CrawlSettings,
    onProgress?: (current: number, total: number, url: string) => void
  ): Promise<CrawlResult[]> {
    const crawlSettings = { ...this.defaultSettings, ...settings };
    const results: CrawlResult[] = [];
    const totalUrls = urls.length;
    
    // Initialize URL queue
    this.urlQueue = [...urls];
    const processedCount = new Map<string, number>();
    
    while (this.urlQueue.length > 0 && results.length < crawlSettings.maxPagesPerDomain) {
      const currentUrl = this.urlQueue.shift()!;
      
      if (this.crawledUrls.has(currentUrl)) {
        continue;
      }

      const domain = new URL(currentUrl).hostname;
      const domainCount = processedCount.get(domain) || 0;
      
      if (domainCount >= crawlSettings.maxPagesPerDomain) {
        continue;
      }

      try {
        if (onProgress) {
          onProgress(results.length + 1, totalUrls, currentUrl);
        }

        const result = await this.crawlUrl(currentUrl, crawlSettings);
        results.push(result);
        processedCount.set(domain, domainCount + 1);

        // Add discovered links to queue
        if (crawlSettings.maxDepth > 1) {
          const newUrls = this.filterValidUrls(result.links, currentUrl, crawlSettings);
          this.urlQueue.push(...newUrls.slice(0, 10)); // Add max 10 links
        }

        // Download delay
        if (crawlSettings.downloadDelay > 0) {
          await this.delay(crawlSettings.downloadDelay);
        }
      } catch (error) {
        console.error(`Error crawling ${currentUrl}:`, error);
        // Continue with next URL
      }
    }

    return results;
  }

  /**
   * Extract content from HTML
   */
  private extractContent(url: string, html: string, contentType?: string): CrawlResult {
    const $ = cheerio.load(html);
    
    // Remove script and style elements
    $('script, style, noscript').remove();
    
    // Extract metadata
    const title = $('title').text() || $('h1').first().text() || 'Untitled';
    const description = $('meta[name="description"]').attr('content') || 
                       $('meta[property="og:description"]').attr('content') || '';
    const author = $('meta[name="author"]').attr('content') || '';
    const language = $('html').attr('lang') || 
                    $('meta[property="og:locale"]').attr('content') || 'ja';
    
    // Extract headings
    const headings = {
      h1: $('h1').map((_, el) => $(el).text().trim()).get(),
      h2: $('h2').map((_, el) => $(el).text().trim()).get(),
      h3: $('h3').map((_, el) => $(el).text().trim()).get(),
      h4: $('h4').map((_, el) => $(el).text().trim()).get(),
      h5: $('h5').map((_, el) => $(el).text().trim()).get(),
      h6: $('h6').map((_, el) => $(el).text().trim()).get(),
    };
    
    // Extract main content
    const mainContent = this.extractMainContent($);
    
    // Extract links
    const links = this.extractLinks($, url);
    
    // Extract tags
    const tags = $('meta[name="keywords"]').attr('content')?.split(',').map(t => t.trim()) || [];
    
    return {
      url,
      title: title.trim(),
      content: mainContent,
      metadata: {
        crawledAt: new Date().toISOString(),
        contentType: contentType || 'text/html',
        language,
        author,
        publishedDate: this.extractPublishDate($),
        tags,
        description
      },
      links,
      headings
    };
  }

  /**
   * Extract main content from page
   */
  private extractMainContent($: cheerio.CheerioAPI): string {
    // Try common content selectors
    const contentSelectors = [
      'main',
      'article',
      '[role="main"]',
      '.content',
      '#content',
      '.main-content',
      '#main-content',
      '.post-content',
      '.entry-content'
    ];
    
    for (const selector of contentSelectors) {
      const content = $(selector);
      if (content.length > 0) {
        return content.text().replace(/\s+/g, ' ').trim();
      }
    }
    
    // Fallback to body
    return $('body').text().replace(/\s+/g, ' ').trim();
  }

  /**
   * Extract publish date from page
   */
  private extractPublishDate($: cheerio.CheerioAPI): string | undefined {
    const dateSelectors = [
      'meta[property="article:published_time"]',
      'meta[name="publish_date"]',
      'time[datetime]',
      '.publish-date',
      '.post-date'
    ];
    
    for (const selector of dateSelectors) {
      const element = $(selector);
      if (element.length > 0) {
        const date = element.attr('content') || 
                    element.attr('datetime') || 
                    element.text();
        if (date) return date;
      }
    }
    
    return undefined;
  }

  /**
   * Extract and normalize links
   */
  private extractLinks($: cheerio.CheerioAPI, baseUrl: string): string[] {
    const links = new Set<string>();
    const base = new URL(baseUrl);
    
    $('a[href]').each((_, element) => {
      const href = $(element).attr('href');
      if (!href) return;
      
      try {
        const absoluteUrl = new URL(href, base).toString();
        
        // Filter out non-HTTP URLs
        if (absoluteUrl.startsWith('http://') || absoluteUrl.startsWith('https://')) {
          links.add(absoluteUrl);
        }
      } catch {
        // Invalid URL, skip
      }
    });
    
    return Array.from(links);
  }

  /**
   * Check if URL is allowed by patterns
   */
  private isUrlAllowed(url: string, settings: CrawlSettings): boolean {
    // Check exclude patterns
    if (settings.excludePatterns && settings.excludePatterns.length > 0) {
      for (const pattern of settings.excludePatterns) {
        if (new RegExp(pattern).test(url)) {
          return false;
        }
      }
    }
    
    // Check include patterns
    if (settings.includeOnlyPatterns && settings.includeOnlyPatterns.length > 0) {
      for (const pattern of settings.includeOnlyPatterns) {
        if (new RegExp(pattern).test(url)) {
          return true;
        }
      }
      return false; // Not in include list
    }
    
    return true;
  }

  /**
   * Filter valid URLs based on settings
   */
  private filterValidUrls(
    links: string[], 
    sourceUrl: string, 
    settings: CrawlSettings
  ): string[] {
    const sourceDomain = new URL(sourceUrl).hostname;
    
    return links.filter(link => {
      try {
        const linkUrl = new URL(link);
        
        // Same domain only
        if (linkUrl.hostname !== sourceDomain) {
          return false;
        }
        
        // Check patterns
        return this.isUrlAllowed(link, settings);
      } catch {
        return false;
      }
    });
  }

  /**
   * Organize crawled content into structured format
   */
  async organizeContent(crawlResults: CrawlResult[]): Promise<OrganizedContent> {
    const organized: OrganizedContent = {
      mainTopic: this.extractMainTopic(crawlResults),
      sections: this.groupContentIntoSections(crawlResults),
      metadata: {
        totalPages: crawlResults.length,
        crawledAt: new Date().toISOString(),
        sources: crawlResults.map(r => r.url)
      }
    };
    
    return organized;
  }

  /**
   * Extract main topic from crawled content
   */
  private extractMainTopic(results: CrawlResult[]): string {
    // Find most common h1 or title
    const titles = results.map(r => r.title);
    const h1s = results.flatMap(r => r.headings.h1);
    
    const allTitles = [...titles, ...h1s];
    
    if (allTitles.length === 0) {
      return 'Untitled Content';
    }
    
    // Simple frequency analysis
    const frequency = new Map<string, number>();
    for (const title of allTitles) {
      frequency.set(title, (frequency.get(title) || 0) + 1);
    }
    
    return Array.from(frequency.entries())
      .sort((a, b) => b[1] - a[1])[0][0];
  }

  /**
   * Group content into logical sections
   */
  private groupContentIntoSections(results: CrawlResult[]): OrganizedContent['sections'] {
    const sections: OrganizedContent['sections'] = [];
    
    for (const result of results) {
      sections.push({
        title: result.title,
        content: result.content,
        subsections: result.headings.h2.map(h2 => ({
          title: h2,
          content: '' // Would need more sophisticated extraction
        }))
      });
    }
    
    return sections;
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Clear crawl cache
   */
  clearCache(): void {
    this.crawledUrls.clear();
    this.urlQueue = [];
  }

  /**
   * Get crawl statistics
   */
  getStats(): {
    crawledUrls: number;
    queuedUrls: number;
    rateLimiterTokens: number;
  } {
    return {
      crawledUrls: this.crawledUrls.size,
      queuedUrls: this.urlQueue.length,
      rateLimiterTokens: this.rateLimiter.getAvailableTokens()
    };
  }
}