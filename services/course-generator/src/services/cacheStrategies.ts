/**
 * Cache Strategies
 * Ultimate ShunsukeModel Ecosystem
 * 
 * Intelligent caching strategies for optimal performance
 */

import { cacheService, CacheKeys, CacheTTL } from './cacheService';
import { AppError, ErrorCodes } from '../utils/errors';

export interface CacheStrategy {
  key: string;
  ttl?: number;
  generateKey?: (...args: any[]) => string;
  shouldCache?: (...args: any[]) => boolean;
  invalidatePatterns?: string[];
}

/**
 * Course caching strategies
 */
export const courseStrategies = {
  // Course details
  getCourse: {
    key: CacheKeys.COURSE,
    ttl: CacheTTL.MEDIUM,
    generateKey: (courseId: string) => `${CacheKeys.COURSE}${courseId}`,
    invalidatePatterns: ['course:*', 'enrollment:*', 'progress:*']
  },
  
  // User courses list
  getUserCourses: {
    key: CacheKeys.COURSE,
    ttl: CacheTTL.SHORT,
    generateKey: (userId: string, status?: string) => 
      `${CacheKeys.COURSE}list:${userId}:${status || 'all'}`,
    invalidatePatterns: ['course:list:*']
  },
  
  // Course search
  searchCourses: {
    key: CacheKeys.COURSE,
    ttl: CacheTTL.SHORT,
    generateKey: (query: string, options?: any) => 
      `${CacheKeys.COURSE}search:${query}:${JSON.stringify(options || {})}`,
    shouldCache: (query: string) => query.length > 2
  }
};

/**
 * User caching strategies
 */
export const userStrategies = {
  // User profile
  getUser: {
    key: CacheKeys.USER,
    ttl: CacheTTL.LONG,
    generateKey: (userId: string) => `${CacheKeys.USER}${userId}`,
    invalidatePatterns: ['user:*', 'session:*']
  },
  
  // User sessions
  getSession: {
    key: CacheKeys.SESSION,
    ttl: CacheTTL.WEEK,
    generateKey: (sessionId: string) => `${CacheKeys.SESSION}${sessionId}`
  }
};

/**
 * Template caching strategies
 */
export const templateStrategies = {
  // Template details
  getTemplate: {
    key: CacheKeys.TEMPLATE,
    ttl: CacheTTL.LONG,
    generateKey: (templateId: string) => `${CacheKeys.TEMPLATE}${templateId}`,
    invalidatePatterns: ['template:*']
  },
  
  // Templates list
  getTemplates: {
    key: CacheKeys.TEMPLATE,
    ttl: CacheTTL.MEDIUM,
    generateKey: (category?: string, isPublic?: boolean, userId?: string) => 
      `${CacheKeys.TEMPLATE}list:${category || 'all'}:${isPublic}:${userId || 'public'}`
  }
};

/**
 * Progress caching strategies
 */
export const progressStrategies = {
  // Course enrollment
  getEnrollment: {
    key: CacheKeys.ENROLLMENT,
    ttl: CacheTTL.MEDIUM,
    generateKey: (userId: string, courseId: string) => 
      `${CacheKeys.ENROLLMENT}${userId}:${courseId}`,
    invalidatePatterns: ['enrollment:*', 'progress:*', 'activity:*']
  },
  
  // Lesson progress
  getLessonProgress: {
    key: CacheKeys.PROGRESS,
    ttl: CacheTTL.SHORT,
    generateKey: (enrollmentId: string, lessonKey: string) => 
      `${CacheKeys.PROGRESS}${enrollmentId}:${lessonKey}`
  },
  
  // Learning statistics
  getLearningStats: {
    key: CacheKeys.STATS,
    ttl: CacheTTL.SHORT,
    generateKey: (userId: string, period?: string) => 
      `${CacheKeys.STATS}learning:${userId}:${period || 'all'}`
  }
};

/**
 * Content caching strategies
 */
export const contentStrategies = {
  // Generated content
  getGeneratedContent: {
    key: CacheKeys.GENERATED_CONTENT,
    ttl: CacheTTL.LONG,
    generateKey: (contentHash: string) => 
      `${CacheKeys.GENERATED_CONTENT}${contentHash}`,
    shouldCache: (content: any) => content && content.length > 100
  },
  
  // Web content is already cached in webCrawlerService
  getWebContent: {
    key: CacheKeys.WEB_CONTENT,
    ttl: CacheTTL.LONG,
    generateKey: (url: string) => `${CacheKeys.WEB_CONTENT}${url}`
  }
};

/**
 * Invalidation helper
 */
export class CacheInvalidator {
  /**
   * Invalidate cache by patterns
   */
  static async invalidatePatterns(patterns: string[]): Promise<number> {
    let totalDeleted = 0;
    
    for (const pattern of patterns) {
      const deleted = await cacheService.deletePattern(pattern);
      totalDeleted += deleted;
    }
    
    return totalDeleted;
  }
  
  /**
   * Invalidate course-related caches
   */
  static async invalidateCourse(courseId: string, userId?: string): Promise<void> {
    const patterns = [
      `${CacheKeys.COURSE}${courseId}*`,
      `${CacheKeys.COURSE}list:*`,
      `${CacheKeys.COURSE}search:*`,
      `${CacheKeys.ENROLLMENT}*:${courseId}*`,
      `${CacheKeys.PROGRESS}*:${courseId}*`
    ];
    
    if (userId) {
      patterns.push(
        `${CacheKeys.COURSE}list:${userId}:*`,
        `${CacheKeys.STATS}learning:${userId}:*`
      );
    }
    
    await this.invalidatePatterns(patterns);
  }
  
  /**
   * Invalidate user-related caches
   */
  static async invalidateUser(userId: string): Promise<void> {
    const patterns = [
      `${CacheKeys.USER}${userId}*`,
      `${CacheKeys.SESSION}*:${userId}*`,
      `${CacheKeys.COURSE}list:${userId}:*`,
      `${CacheKeys.ENROLLMENT}${userId}:*`,
      `${CacheKeys.STATS}*:${userId}:*`
    ];
    
    await this.invalidatePatterns(patterns);
  }
  
  /**
   * Invalidate template-related caches
   */
  static async invalidateTemplate(templateId: string, userId?: string): Promise<void> {
    const patterns = [
      `${CacheKeys.TEMPLATE}${templateId}*`,
      `${CacheKeys.TEMPLATE}list:*`
    ];
    
    if (userId) {
      patterns.push(`${CacheKeys.TEMPLATE}list:*:*:${userId}`);
    }
    
    await this.invalidatePatterns(patterns);
  }
  
  /**
   * Invalidate progress-related caches
   */
  static async invalidateProgress(enrollmentId: string, userId: string): Promise<void> {
    const patterns = [
      `${CacheKeys.ENROLLMENT}${userId}:*`,
      `${CacheKeys.PROGRESS}${enrollmentId}:*`,
      `${CacheKeys.ACTIVITY}${userId}:*`,
      `${CacheKeys.STATS}learning:${userId}:*`
    ];
    
    await this.invalidatePatterns(patterns);
  }
}

/**
 * Cache decorator for methods
 */
export function Cacheable(strategy: CacheStrategy) {
  return function (target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = async function (...args: any[]) {
      // Generate cache key
      const cacheKey = strategy.generateKey ? 
        strategy.generateKey(...args) : 
        `${strategy.key}:${propertyName}:${JSON.stringify(args)}`;
      
      // Check if should cache
      if (strategy.shouldCache && !strategy.shouldCache(...args)) {
        return originalMethod.apply(this, args);
      }
      
      // Try to get from cache
      const cached = await cacheService.get(cacheKey);
      if (cached !== null) {
        console.log(`Cache hit: ${cacheKey}`);
        return cached;
      }
      
      // Execute original method
      const result = await originalMethod.apply(this, args);
      
      // Cache the result
      if (result !== null && result !== undefined) {
        await cacheService.set(cacheKey, result, { ttl: strategy.ttl });
        console.log(`Cached: ${cacheKey}`);
      }
      
      return result;
    };
    
    return descriptor;
  };
}

/**
 * Cache invalidation decorator
 */
export function InvalidatesCache(patterns: string[] | ((args: any[]) => string[])) {
  return function (target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = async function (...args: any[]) {
      // Execute original method
      const result = await originalMethod.apply(this, args);
      
      // Invalidate cache
      const invalidatePatterns = typeof patterns === 'function' ? 
        patterns(args) : patterns;
      
      await CacheInvalidator.invalidatePatterns(invalidatePatterns);
      console.log(`Invalidated cache patterns: ${invalidatePatterns.join(', ')}`);
      
      return result;
    };
    
    return descriptor;
  };
}

/**
 * Warmup cache helper
 */
export class CacheWarmer {
  /**
   * Warmup course caches
   */
  static async warmupCourses(courseIds: string[]): Promise<void> {
    console.log(`Warming up cache for ${courseIds.length} courses...`);
    
    // This would typically call the service methods to populate cache
    // Implementation depends on the specific service methods
  }
  
  /**
   * Warmup user caches
   */
  static async warmupUsers(userIds: string[]): Promise<void> {
    console.log(`Warming up cache for ${userIds.length} users...`);
    
    // This would typically call the service methods to populate cache
    // Implementation depends on the specific service methods
  }
}

/**
 * Cache health monitor
 */
export class CacheHealthMonitor {
  /**
   * Check cache health
   */
  static async checkHealth(): Promise<{
    healthy: boolean;
    stats: any;
    errors: string[];
  }> {
    const errors: string[] = [];
    
    try {
      const stats = await cacheService.getStats();
      
      if (!stats.connected) {
        errors.push('Cache not connected');
      }
      
      return {
        healthy: stats.connected,
        stats,
        errors
      };
    } catch (error) {
      errors.push(`Cache health check failed: ${error}`);
      return {
        healthy: false,
        stats: null,
        errors
      };
    }
  }
  
  /**
   * Get cache metrics
   */
  static async getMetrics(): Promise<{
    hitRate: number;
    missRate: number;
    memoryUsage: number;
    keyCount: number;
  }> {
    const stats = await cacheService.getStats();
    
    // These metrics would be calculated based on actual cache usage
    // For now, returning placeholder values
    return {
      hitRate: 0,
      missRate: 0,
      memoryUsage: parseInt(stats.info.match(/used_memory:(\d+)/)?.[1] || '0'),
      keyCount: stats.dbsize
    };
  }
}