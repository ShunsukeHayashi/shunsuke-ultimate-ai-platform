/**
 * Redis Cache Service
 * Ultimate ShunsukeModel Ecosystem
 */

import Redis from 'ioredis';
import { AppError, ErrorCodes } from '../utils/errors';

// Cache key prefixes
export const CacheKeys = {
  COURSE: 'course:',
  USER: 'user:',
  TEMPLATE: 'template:',
  SHARE: 'share:',
  ENROLLMENT: 'enrollment:',
  PROGRESS: 'progress:',
  ACTIVITY: 'activity:',
  STATS: 'stats:',
  SESSION: 'session:',
  GENERATED_CONTENT: 'generated:',
  WEB_CONTENT: 'web_content:',
} as const;

// Default TTL values (in seconds)
export const CacheTTL = {
  SHORT: 300, // 5 minutes
  MEDIUM: 3600, // 1 hour
  LONG: 86400, // 24 hours
  WEEK: 604800, // 7 days
} as const;

interface CacheOptions {
  ttl?: number;
  prefix?: string;
}

export class CacheService {
  private redis: Redis;
  private isConnected: boolean = false;

  constructor() {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    
    this.redis = new Redis(redisUrl, {
      retryStrategy: (times) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
      reconnectOnError: (err) => {
        const targetError = 'READONLY';
        if (err.message.includes(targetError)) {
          // Only reconnect when the error contains "READONLY"
          return true;
        }
        return false;
      },
      maxRetriesPerRequest: 3,
    });

    this.redis.on('connect', () => {
      console.log('🔗 Redis connected');
      this.isConnected = true;
    });

    this.redis.on('error', (err) => {
      console.error('Redis error:', err);
      this.isConnected = false;
    });

    this.redis.on('close', () => {
      console.log('Redis connection closed');
      this.isConnected = false;
    });
  }

  /**
   * Get value from cache
   */
  async get<T = any>(key: string): Promise<T | null> {
    if (!this.isConnected) {
      console.warn('Redis not connected, skipping cache get');
      return null;
    }

    try {
      const value = await this.redis.get(key);
      if (!value) return null;
      
      return JSON.parse(value) as T;
    } catch (error) {
      console.error(`Cache get error for key ${key}:`, error);
      return null;
    }
  }

  /**
   * Set value in cache
   */
  async set<T = any>(
    key: string, 
    value: T, 
    options: CacheOptions = {}
  ): Promise<boolean> {
    if (!this.isConnected) {
      console.warn('Redis not connected, skipping cache set');
      return false;
    }

    try {
      const { ttl = CacheTTL.MEDIUM } = options;
      const serialized = JSON.stringify(value);
      
      if (ttl > 0) {
        await this.redis.setex(key, ttl, serialized);
      } else {
        await this.redis.set(key, serialized);
      }
      
      return true;
    } catch (error) {
      console.error(`Cache set error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Delete value from cache
   */
  async delete(key: string): Promise<boolean> {
    if (!this.isConnected) {
      console.warn('Redis not connected, skipping cache delete');
      return false;
    }

    try {
      const result = await this.redis.del(key);
      return result > 0;
    } catch (error) {
      console.error(`Cache delete error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Delete multiple keys by pattern
   */
  async deletePattern(pattern: string): Promise<number> {
    if (!this.isConnected) {
      console.warn('Redis not connected, skipping cache delete pattern');
      return 0;
    }

    try {
      const keys = await this.redis.keys(pattern);
      if (keys.length === 0) return 0;
      
      const result = await this.redis.del(...keys);
      return result;
    } catch (error) {
      console.error(`Cache delete pattern error for ${pattern}:`, error);
      return 0;
    }
  }

  /**
   * Check if key exists
   */
  async exists(key: string): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      const result = await this.redis.exists(key);
      return result === 1;
    } catch (error) {
      console.error(`Cache exists error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Set expiration on existing key
   */
  async expire(key: string, ttl: number): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      const result = await this.redis.expire(key, ttl);
      return result === 1;
    } catch (error) {
      console.error(`Cache expire error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Get remaining TTL for key
   */
  async ttl(key: string): Promise<number> {
    if (!this.isConnected) {
      return -1;
    }

    try {
      return await this.redis.ttl(key);
    } catch (error) {
      console.error(`Cache ttl error for key ${key}:`, error);
      return -1;
    }
  }

  /**
   * Increment value
   */
  async incr(key: string, amount: number = 1): Promise<number> {
    if (!this.isConnected) {
      throw new AppError('Redis not connected', ErrorCodes.SERVICE_UNAVAILABLE);
    }

    try {
      if (amount === 1) {
        return await this.redis.incr(key);
      } else {
        return await this.redis.incrby(key, amount);
      }
    } catch (error) {
      console.error(`Cache incr error for key ${key}:`, error);
      throw new AppError('Failed to increment cache value', ErrorCodes.CACHE_ERROR);
    }
  }

  /**
   * Decrement value
   */
  async decr(key: string, amount: number = 1): Promise<number> {
    if (!this.isConnected) {
      throw new AppError('Redis not connected', ErrorCodes.SERVICE_UNAVAILABLE);
    }

    try {
      if (amount === 1) {
        return await this.redis.decr(key);
      } else {
        return await this.redis.decrby(key, amount);
      }
    } catch (error) {
      console.error(`Cache decr error for key ${key}:`, error);
      throw new AppError('Failed to decrement cache value', ErrorCodes.CACHE_ERROR);
    }
  }

  /**
   * Add to set
   */
  async sadd(key: string, ...members: string[]): Promise<number> {
    if (!this.isConnected) {
      return 0;
    }

    try {
      return await this.redis.sadd(key, ...members);
    } catch (error) {
      console.error(`Cache sadd error for key ${key}:`, error);
      return 0;
    }
  }

  /**
   * Remove from set
   */
  async srem(key: string, ...members: string[]): Promise<number> {
    if (!this.isConnected) {
      return 0;
    }

    try {
      return await this.redis.srem(key, ...members);
    } catch (error) {
      console.error(`Cache srem error for key ${key}:`, error);
      return 0;
    }
  }

  /**
   * Get all members of set
   */
  async smembers(key: string): Promise<string[]> {
    if (!this.isConnected) {
      return [];
    }

    try {
      return await this.redis.smembers(key);
    } catch (error) {
      console.error(`Cache smembers error for key ${key}:`, error);
      return [];
    }
  }

  /**
   * Check if member exists in set
   */
  async sismember(key: string, member: string): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      const result = await this.redis.sismember(key, member);
      return result === 1;
    } catch (error) {
      console.error(`Cache sismember error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Push to list
   */
  async lpush(key: string, ...values: string[]): Promise<number> {
    if (!this.isConnected) {
      return 0;
    }

    try {
      return await this.redis.lpush(key, ...values);
    } catch (error) {
      console.error(`Cache lpush error for key ${key}:`, error);
      return 0;
    }
  }

  /**
   * Get list range
   */
  async lrange(key: string, start: number, stop: number): Promise<string[]> {
    if (!this.isConnected) {
      return [];
    }

    try {
      return await this.redis.lrange(key, start, stop);
    } catch (error) {
      console.error(`Cache lrange error for key ${key}:`, error);
      return [];
    }
  }

  /**
   * Trim list
   */
  async ltrim(key: string, start: number, stop: number): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      await this.redis.ltrim(key, start, stop);
      return true;
    } catch (error) {
      console.error(`Cache ltrim error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Clear all cache
   */
  async clear(): Promise<void> {
    if (!this.isConnected) {
      console.warn('Redis not connected, skipping cache clear');
      return;
    }

    try {
      await this.redis.flushdb();
      console.log('Cache cleared');
    } catch (error) {
      console.error('Cache clear error:', error);
    }
  }

  /**
   * Disconnect from Redis
   */
  async disconnect(): Promise<void> {
    if (this.redis) {
      await this.redis.quit();
      this.isConnected = false;
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<{
    connected: boolean;
    dbsize: number;
    info: string;
  }> {
    if (!this.isConnected) {
      return {
        connected: false,
        dbsize: 0,
        info: 'Not connected',
      };
    }

    try {
      const dbsize = await this.redis.dbsize();
      const info = await this.redis.info();
      
      return {
        connected: true,
        dbsize,
        info,
      };
    } catch (error) {
      console.error('Cache stats error:', error);
      return {
        connected: false,
        dbsize: 0,
        info: 'Error getting stats',
      };
    }
  }

  /**
   * Execute cache operation with fallback
   */
  async getOrSet<T>(
    key: string,
    fetchFn: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    // Try to get from cache first
    const cached = await this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    // Fetch fresh data
    const data = await fetchFn();
    
    // Store in cache
    await this.set(key, data, options);
    
    return data;
  }
}

// Export singleton instance
export const cacheService = new CacheService();