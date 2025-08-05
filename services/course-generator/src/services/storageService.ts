/**
 * Storage Service
 * Ultimate ShunsukeModel Ecosystem
 * 
 * Multi-provider storage service with CDN support
 */

import fs from 'fs/promises';
import path from 'path';
import crypto from 'crypto';
import mime from 'mime-types';
import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand, HeadObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { AppError, ErrorCodes } from '../utils/errors';

export type StorageProvider = 'local' | 's3' | 'cloudflare';

export interface StorageConfig {
  provider: StorageProvider;
  local?: {
    basePath: string;
    publicUrl?: string;
  };
  s3?: {
    bucket: string;
    region: string;
    accessKeyId: string;
    secretAccessKey: string;
    endpoint?: string; // For S3-compatible services
    cdnUrl?: string;
  };
  cloudflare?: {
    accountId: string;
    accessKeyId: string;
    secretAccessKey: string;
    bucketName: string;
    publicUrl: string;
  };
}

export interface StorageFile {
  key: string;
  url: string;
  size: number;
  contentType: string;
  etag?: string;
  lastModified?: Date;
}

export interface UploadOptions {
  contentType?: string;
  metadata?: Record<string, string>;
  cacheControl?: string;
  expiresIn?: number; // For signed URLs
  public?: boolean;
}

export class StorageService {
  private config: StorageConfig;
  private s3Client?: S3Client;

  constructor(config?: StorageConfig) {
    this.config = config || this.getDefaultConfig();
    this.initializeProvider();
  }

  private getDefaultConfig(): StorageConfig {
    const provider = (process.env.STORAGE_PROVIDER as StorageProvider) || 'local';
    
    const config: StorageConfig = { provider };

    switch (provider) {
      case 'local':
        config.local = {
          basePath: process.env.STORAGE_LOCAL_PATH || './uploads',
          publicUrl: process.env.STORAGE_PUBLIC_URL || 'http://localhost:3002/uploads'
        };
        break;
      
      case 's3':
        config.s3 = {
          bucket: process.env.S3_BUCKET || '',
          region: process.env.S3_REGION || 'us-east-1',
          accessKeyId: process.env.S3_ACCESS_KEY_ID || '',
          secretAccessKey: process.env.S3_SECRET_ACCESS_KEY || '',
          endpoint: process.env.S3_ENDPOINT,
          cdnUrl: process.env.S3_CDN_URL
        };
        break;
      
      case 'cloudflare':
        config.cloudflare = {
          accountId: process.env.CLOUDFLARE_ACCOUNT_ID || '',
          accessKeyId: process.env.CLOUDFLARE_ACCESS_KEY_ID || '',
          secretAccessKey: process.env.CLOUDFLARE_SECRET_ACCESS_KEY || '',
          bucketName: process.env.CLOUDFLARE_BUCKET_NAME || '',
          publicUrl: process.env.CLOUDFLARE_PUBLIC_URL || ''
        };
        break;
    }

    return config;
  }

  private initializeProvider(): void {
    switch (this.config.provider) {
      case 's3':
        if (!this.config.s3) {
          throw new AppError('S3 configuration missing', ErrorCodes.CONFIG_ERROR);
        }
        this.s3Client = new S3Client({
          region: this.config.s3.region,
          credentials: {
            accessKeyId: this.config.s3.accessKeyId,
            secretAccessKey: this.config.s3.secretAccessKey
          },
          endpoint: this.config.s3.endpoint
        });
        break;
      
      case 'cloudflare':
        if (!this.config.cloudflare) {
          throw new AppError('Cloudflare configuration missing', ErrorCodes.CONFIG_ERROR);
        }
        // Cloudflare R2 uses S3-compatible API
        this.s3Client = new S3Client({
          region: 'auto',
          endpoint: `https://${this.config.cloudflare.accountId}.r2.cloudflarestorage.com`,
          credentials: {
            accessKeyId: this.config.cloudflare.accessKeyId,
            secretAccessKey: this.config.cloudflare.secretAccessKey
          }
        });
        break;
    }
  }

  /**
   * Upload a file
   */
  async upload(
    filePath: string,
    key: string,
    options: UploadOptions = {}
  ): Promise<StorageFile> {
    const normalizedKey = this.normalizeKey(key);
    
    switch (this.config.provider) {
      case 'local':
        return this.uploadLocal(filePath, normalizedKey, options);
      
      case 's3':
        return this.uploadS3(filePath, normalizedKey, options);
      
      case 'cloudflare':
        return this.uploadCloudflare(filePath, normalizedKey, options);
      
      default:
        throw new AppError('Invalid storage provider', ErrorCodes.CONFIG_ERROR);
    }
  }

  /**
   * Upload buffer directly
   */
  async uploadBuffer(
    buffer: Buffer,
    key: string,
    options: UploadOptions = {}
  ): Promise<StorageFile> {
    const normalizedKey = this.normalizeKey(key);
    
    switch (this.config.provider) {
      case 'local':
        return this.uploadBufferLocal(buffer, normalizedKey, options);
      
      case 's3':
        return this.uploadBufferS3(buffer, normalizedKey, options);
      
      case 'cloudflare':
        return this.uploadBufferCloudflare(buffer, normalizedKey, options);
      
      default:
        throw new AppError('Invalid storage provider', ErrorCodes.CONFIG_ERROR);
    }
  }

  /**
   * Get file URL
   */
  async getUrl(key: string, options: { expiresIn?: number } = {}): Promise<string> {
    const normalizedKey = this.normalizeKey(key);
    
    switch (this.config.provider) {
      case 'local':
        return this.getLocalUrl(normalizedKey);
      
      case 's3':
        return this.getS3Url(normalizedKey, options);
      
      case 'cloudflare':
        return this.getCloudflareUrl(normalizedKey, options);
      
      default:
        throw new AppError('Invalid storage provider', ErrorCodes.CONFIG_ERROR);
    }
  }

  /**
   * Delete a file
   */
  async delete(key: string): Promise<void> {
    const normalizedKey = this.normalizeKey(key);
    
    switch (this.config.provider) {
      case 'local':
        return this.deleteLocal(normalizedKey);
      
      case 's3':
        return this.deleteS3(normalizedKey);
      
      case 'cloudflare':
        return this.deleteCloudflare(normalizedKey);
      
      default:
        throw new AppError('Invalid storage provider', ErrorCodes.CONFIG_ERROR);
    }
  }

  /**
   * Check if file exists
   */
  async exists(key: string): Promise<boolean> {
    const normalizedKey = this.normalizeKey(key);
    
    switch (this.config.provider) {
      case 'local':
        return this.existsLocal(normalizedKey);
      
      case 's3':
        return this.existsS3(normalizedKey);
      
      case 'cloudflare':
        return this.existsCloudflare(normalizedKey);
      
      default:
        throw new AppError('Invalid storage provider', ErrorCodes.CONFIG_ERROR);
    }
  }

  // Local storage implementation
  private async uploadLocal(
    filePath: string,
    key: string,
    options: UploadOptions
  ): Promise<StorageFile> {
    if (!this.config.local) {
      throw new AppError('Local storage not configured', ErrorCodes.CONFIG_ERROR);
    }

    const destPath = path.join(this.config.local.basePath, key);
    const destDir = path.dirname(destPath);

    // Create directory if not exists
    await fs.mkdir(destDir, { recursive: true });

    // Copy file
    await fs.copyFile(filePath, destPath);

    const stats = await fs.stat(destPath);
    const contentType = options.contentType || mime.lookup(key) || 'application/octet-stream';

    return {
      key,
      url: this.getLocalUrl(key),
      size: stats.size,
      contentType,
      lastModified: stats.mtime
    };
  }

  private async uploadBufferLocal(
    buffer: Buffer,
    key: string,
    options: UploadOptions
  ): Promise<StorageFile> {
    if (!this.config.local) {
      throw new AppError('Local storage not configured', ErrorCodes.CONFIG_ERROR);
    }

    const destPath = path.join(this.config.local.basePath, key);
    const destDir = path.dirname(destPath);

    // Create directory if not exists
    await fs.mkdir(destDir, { recursive: true });

    // Write buffer
    await fs.writeFile(destPath, buffer);

    const contentType = options.contentType || mime.lookup(key) || 'application/octet-stream';

    return {
      key,
      url: this.getLocalUrl(key),
      size: buffer.length,
      contentType,
      lastModified: new Date()
    };
  }

  private getLocalUrl(key: string): string {
    if (!this.config.local) {
      throw new AppError('Local storage not configured', ErrorCodes.CONFIG_ERROR);
    }
    return `${this.config.local.publicUrl}/${key}`;
  }

  private async deleteLocal(key: string): Promise<void> {
    if (!this.config.local) {
      throw new AppError('Local storage not configured', ErrorCodes.CONFIG_ERROR);
    }

    const filePath = path.join(this.config.local.basePath, key);
    
    try {
      await fs.unlink(filePath);
    } catch (error: any) {
      if (error.code !== 'ENOENT') {
        throw new AppError('Failed to delete file', ErrorCodes.STORAGE_ERROR, error);
      }
    }
  }

  private async existsLocal(key: string): Promise<boolean> {
    if (!this.config.local) {
      throw new AppError('Local storage not configured', ErrorCodes.CONFIG_ERROR);
    }

    const filePath = path.join(this.config.local.basePath, key);
    
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  // S3 storage implementation
  private async uploadS3(
    filePath: string,
    key: string,
    options: UploadOptions
  ): Promise<StorageFile> {
    const buffer = await fs.readFile(filePath);
    return this.uploadBufferS3(buffer, key, options);
  }

  private async uploadBufferS3(
    buffer: Buffer,
    key: string,
    options: UploadOptions
  ): Promise<StorageFile> {
    if (!this.config.s3 || !this.s3Client) {
      throw new AppError('S3 not configured', ErrorCodes.CONFIG_ERROR);
    }

    const contentType = options.contentType || mime.lookup(key) || 'application/octet-stream';
    const etag = crypto.createHash('md5').update(buffer).digest('hex');

    const command = new PutObjectCommand({
      Bucket: this.config.s3.bucket,
      Key: key,
      Body: buffer,
      ContentType: contentType,
      CacheControl: options.cacheControl || 'public, max-age=31536000',
      Metadata: options.metadata
    });

    await this.s3Client.send(command);

    return {
      key,
      url: await this.getS3Url(key, { expiresIn: options.expiresIn }),
      size: buffer.length,
      contentType,
      etag,
      lastModified: new Date()
    };
  }

  private async getS3Url(key: string, options: { expiresIn?: number } = {}): Promise<string> {
    if (!this.config.s3 || !this.s3Client) {
      throw new AppError('S3 not configured', ErrorCodes.CONFIG_ERROR);
    }

    // Use CDN URL if available and no expiration needed
    if (this.config.s3.cdnUrl && !options.expiresIn) {
      return `${this.config.s3.cdnUrl}/${key}`;
    }

    // Generate signed URL if expiration needed
    if (options.expiresIn) {
      const command = new GetObjectCommand({
        Bucket: this.config.s3.bucket,
        Key: key
      });
      
      return await getSignedUrl(this.s3Client, command, {
        expiresIn: options.expiresIn
      });
    }

    // Default public URL
    return `https://${this.config.s3.bucket}.s3.${this.config.s3.region}.amazonaws.com/${key}`;
  }

  private async deleteS3(key: string): Promise<void> {
    if (!this.config.s3 || !this.s3Client) {
      throw new AppError('S3 not configured', ErrorCodes.CONFIG_ERROR);
    }

    const command = new DeleteObjectCommand({
      Bucket: this.config.s3.bucket,
      Key: key
    });

    await this.s3Client.send(command);
  }

  private async existsS3(key: string): Promise<boolean> {
    if (!this.config.s3 || !this.s3Client) {
      throw new AppError('S3 not configured', ErrorCodes.CONFIG_ERROR);
    }

    try {
      const command = new HeadObjectCommand({
        Bucket: this.config.s3.bucket,
        Key: key
      });
      
      await this.s3Client.send(command);
      return true;
    } catch {
      return false;
    }
  }

  // Cloudflare R2 implementation (uses S3-compatible API)
  private async uploadCloudflare(
    filePath: string,
    key: string,
    options: UploadOptions
  ): Promise<StorageFile> {
    const buffer = await fs.readFile(filePath);
    return this.uploadBufferCloudflare(buffer, key, options);
  }

  private async uploadBufferCloudflare(
    buffer: Buffer,
    key: string,
    options: UploadOptions
  ): Promise<StorageFile> {
    if (!this.config.cloudflare || !this.s3Client) {
      throw new AppError('Cloudflare R2 not configured', ErrorCodes.CONFIG_ERROR);
    }

    const contentType = options.contentType || mime.lookup(key) || 'application/octet-stream';
    const etag = crypto.createHash('md5').update(buffer).digest('hex');

    const command = new PutObjectCommand({
      Bucket: this.config.cloudflare.bucketName,
      Key: key,
      Body: buffer,
      ContentType: contentType,
      CacheControl: options.cacheControl || 'public, max-age=31536000',
      Metadata: options.metadata
    });

    await this.s3Client.send(command);

    return {
      key,
      url: `${this.config.cloudflare.publicUrl}/${key}`,
      size: buffer.length,
      contentType,
      etag,
      lastModified: new Date()
    };
  }

  private async getCloudflareUrl(key: string, options: { expiresIn?: number } = {}): Promise<string> {
    if (!this.config.cloudflare) {
      throw new AppError('Cloudflare R2 not configured', ErrorCodes.CONFIG_ERROR);
    }

    // Cloudflare R2 public URL
    return `${this.config.cloudflare.publicUrl}/${key}`;
  }

  private async deleteCloudflare(key: string): Promise<void> {
    if (!this.config.cloudflare || !this.s3Client) {
      throw new AppError('Cloudflare R2 not configured', ErrorCodes.CONFIG_ERROR);
    }

    const command = new DeleteObjectCommand({
      Bucket: this.config.cloudflare.bucketName,
      Key: key
    });

    await this.s3Client.send(command);
  }

  private async existsCloudflare(key: string): Promise<boolean> {
    if (!this.config.cloudflare || !this.s3Client) {
      throw new AppError('Cloudflare R2 not configured', ErrorCodes.CONFIG_ERROR);
    }

    try {
      const command = new HeadObjectCommand({
        Bucket: this.config.cloudflare.bucketName,
        Key: key
      });
      
      await this.s3Client.send(command);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Normalize storage key
   */
  private normalizeKey(key: string): string {
    // Remove leading slashes
    return key.replace(/^\/+/, '');
  }

  /**
   * Get storage info
   */
  getStorageInfo(): {
    provider: StorageProvider;
    configured: boolean;
    cdnEnabled: boolean;
  } {
    const configured = this.isConfigured();
    const cdnEnabled = this.isCdnEnabled();

    return {
      provider: this.config.provider,
      configured,
      cdnEnabled
    };
  }

  private isConfigured(): boolean {
    switch (this.config.provider) {
      case 'local':
        return !!(this.config.local?.basePath);
      
      case 's3':
        return !!(this.config.s3?.bucket && this.config.s3?.accessKeyId);
      
      case 'cloudflare':
        return !!(this.config.cloudflare?.bucketName && this.config.cloudflare?.accessKeyId);
      
      default:
        return false;
    }
  }

  private isCdnEnabled(): boolean {
    switch (this.config.provider) {
      case 's3':
        return !!(this.config.s3?.cdnUrl);
      
      case 'cloudflare':
        return true; // Cloudflare R2 includes CDN
      
      default:
        return false;
    }
  }
}

// Export singleton instance
export const storageService = new StorageService();