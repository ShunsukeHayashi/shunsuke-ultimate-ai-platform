/**
 * Redis Service
 * Ultimate ShunsukeModel Ecosystem
 * 
 * High-performance caching with Redis
 */

import { createClient, RedisClientType } from 'redis';
import { AppError, ErrorCodes } from '../utils/errors';

export interface RedisConfig {
  url?: string;
  password?: string;
  db?: number;
  connectTimeout?: number;
  commandTimeout?: number;
  maxRetriesPerRequest?: number;
  retryStrategy?: (times: number) => number | null;
}

export class RedisService {
  private static instance: RedisService;
  private client: RedisClientType | null = null;
  private isConnected: boolean = false;
  private connectionPromise: Promise<void> | null = null;

  private constructor(private config: RedisConfig = {}) {}

  static getInstance(config?: RedisConfig): RedisService {
    if (!RedisService.instance) {
      RedisService.instance = new RedisService(config);
    }
    return RedisService.instance;
  }

  /**
   * Connect to Redis
   */
  async connect(): Promise<void> {
    if (this.isConnected && this.client) {
      return;
    }

    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = this._connect();
    return this.connectionPromise;
  }

  private async _connect(): Promise<void> {
    try {
      const redisUrl = this.config.url || process.env.REDIS_URL || 'redis://localhost:6379';
      
      this.client = createClient({
        url: redisUrl,
        password: this.config.password || process.env.REDIS_PASSWORD,
        database: this.config.db || 0,
        socket: {
          connectTimeout: this.config.connectTimeout || 5000
        }
      });

      // Error handlers
      this.client.on('error', (err) => {
        console.error('Redis Client Error:', err);
        this.isConnected = false;
      });

      this.client.on('connect', () => {
        console.log('Redis Client Connected');
        this.isConnected = true;
      });

      this.client.on('ready', () => {
        console.log('Redis Client Ready');
      });

      this.client.on('reconnecting', () => {
        console.log('Redis Client Reconnecting...');
      });

      await this.client.connect();
      this.isConnected = true;
    } catch (error) {
      this.connectionPromise = null;
      throw new AppError('Failed to connect to Redis', ErrorCodes.CACHE_ERROR, error);
    }
  }

  /**
   * Disconnect from Redis
   */
  async disconnect(): Promise<void> {
    if (!this.client) return;

    try {
      await this.client.quit();
      this.client = null;
      this.isConnected = false;
      this.connectionPromise = null;
    } catch (error) {
      console.error('Error disconnecting from Redis:', error);
    }
  }

  /**
   * Get value from cache
   */
  async get<T = any>(key: string): Promise<T | null> {
    await this.ensureConnection();
    
    try {
      const value = await this.client!.get(key);
      if (!value) return null;
      
      try {
        return JSON.parse(value);
      } catch {
        return value as any;
      }
    } catch (error) {
      console.error(`Redis GET error for key ${key}:`, error);
      return null;
    }
  }

  /**
   * Set value in cache
   */
  async set(
    key: string, 
    value: any, 
    options?: { 
      ttl?: number; // Time to live in seconds
      nx?: boolean; // Only set if not exists
      xx?: boolean; // Only set if exists
    }
  ): Promise<boolean> {
    await this.ensureConnection();
    
    try {
      const serialized = typeof value === 'string' ? value : JSON.stringify(value);
      const setOptions: any = {};
      
      if (options?.ttl) {
        setOptions.EX = options.ttl;
      }
      
      if (options?.nx) {
        setOptions.NX = true;
      } else if (options?.xx) {
        setOptions.XX = true;
      }
      
      const result = await this.client!.set(key, serialized, setOptions);
      return result === 'OK';
    } catch (error) {
      console.error(`Redis SET error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Delete key from cache
   */
  async delete(key: string | string[]): Promise<number> {
    await this.ensureConnection();
    
    try {
      const keys = Array.isArray(key) ? key : [key];
      if (keys.length === 0) return 0;
      
      return await this.client!.del(keys);
    } catch (error) {
      console.error(`Redis DELETE error:`, error);
      return 0;
    }
  }

  /**
   * Check if key exists
   */
  async exists(key: string): Promise<boolean> {
    await this.ensureConnection();
    
    try {
      const result = await this.client!.exists(key);
      return result === 1;
    } catch (error) {
      console.error(`Redis EXISTS error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Set expiration on key
   */
  async expire(key: string, seconds: number): Promise<boolean> {
    await this.ensureConnection();
    
    try {
      const result = await this.client!.expire(key, seconds);
      return Boolean(result);
    } catch (error) {
      console.error(`Redis EXPIRE error for key ${key}:`, error);
      return false;
    }
  }

  /**
   * Get TTL for key
   */
  async ttl(key: string): Promise<number> {
    await this.ensureConnection();
    
    try {
      return await this.client!.ttl(key);
    } catch (error) {
      console.error(`Redis TTL error for key ${key}:`, error);
      return -1;
    }
  }

  /**
   * Increment counter
   */
  async incr(key: string, by: number = 1): Promise<number> {
    await this.ensureConnection();
    
    try {
      if (by === 1) {
        return await this.client!.incr(key);
      } else {
        return await this.client!.incrBy(key, by);
      }
    } catch (error) {
      console.error(`Redis INCR error for key ${key}:`, error);
      throw new AppError('Failed to increment counter', ErrorCodes.CACHE_ERROR, error);
    }
  }

  /**
   * Add to set
   */
  async sAdd(key: string, members: string | string[]): Promise<number> {
    await this.ensureConnection();
    
    try {
      const values = Array.isArray(members) ? members : [members];
      return await this.client!.sAdd(key, values);
    } catch (error) {
      console.error(`Redis SADD error for key ${key}:`, error);
      return 0;
    }
  }

  /**
   * Get set members
   */
  async sMembers(key: string): Promise<string[]> {
    await this.ensureConnection();
    
    try {
      return await this.client!.sMembers(key);
    } catch (error) {
      console.error(`Redis SMEMBERS error for key ${key}:`, error);
      return [];
    }
  }

  /**
   * Remove from set
   */
  async sRem(key: string, members: string | string[]): Promise<number> {
    await this.ensureConnection();
    
    try {
      const values = Array.isArray(members) ? members : [members];
      return await this.client!.sRem(key, values);
    } catch (error) {
      console.error(`Redis SREM error for key ${key}:`, error);
      return 0;
    }
  }

  /**
   * Hash operations
   */
  async hSet(key: string, field: string, value: any): Promise<number> {
    await this.ensureConnection();
    
    try {
      const serialized = typeof value === 'string' ? value : JSON.stringify(value);
      return await this.client!.hSet(key, field, serialized);
    } catch (error) {
      console.error(`Redis HSET error for key ${key}:`, error);
      return 0;
    }
  }

  async hGet(key: string, field: string): Promise<any> {
    await this.ensureConnection();
    
    try {
      const value = await this.client!.hGet(key, field);
      if (!value) return null;
      
      try {
        return JSON.parse(value);
      } catch {
        return value;
      }
    } catch (error) {
      console.error(`Redis HGET error for key ${key}:`, error);
      return null;
    }
  }

  async hGetAll(key: string): Promise<Record<string, any>> {
    await this.ensureConnection();
    
    try {
      const hash = await this.client!.hGetAll(key);
      const result: Record<string, any> = {};
      
      for (const [field, value] of Object.entries(hash)) {
        try {
          result[field] = JSON.parse(value);
        } catch {
          result[field] = value;
        }
      }
      
      return result;
    } catch (error) {
      console.error(`Redis HGETALL error for key ${key}:`, error);
      return {};
    }
  }

  /**
   * Clear all keys with pattern
   */
  async clearPattern(pattern: string): Promise<number> {
    await this.ensureConnection();
    
    try {
      const keys = await this.client!.keys(pattern);
      if (keys.length === 0) return 0;
      
      return await this.client!.del(keys);
    } catch (error) {
      console.error(`Redis clear pattern error for ${pattern}:`, error);
      return 0;
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<{
    connected: boolean;
    memoryUsage?: number;
    totalKeys?: number;
    hitRate?: number;
  }> {
    if (!this.isConnected || !this.client) {
      return { connected: false };
    }

    try {
      const info = await this.client.info('memory');
      const dbSize = await this.client.dbSize();
      
      // Parse memory usage from info string
      const memoryMatch = info.match(/used_memory:(\d+)/);
      const memoryUsage = memoryMatch ? parseInt(memoryMatch[1]) : undefined;
      
      return {
        connected: true,
        memoryUsage,
        totalKeys: dbSize
      };
    } catch (error) {
      console.error('Error getting Redis stats:', error);
      return { connected: this.isConnected };
    }
  }

  /**
   * Ensure connection is established
   */
  private async ensureConnection(): Promise<void> {
    if (!this.isConnected || !this.client) {
      await this.connect();
    }
  }

  /**
   * Check if Redis is available
   */
  static isAvailable(): boolean {
    return !!(process.env.REDIS_URL || process.env.REDIS_HOST);
  }
}

// Export singleton instance
export const redisService = RedisService.getInstance();