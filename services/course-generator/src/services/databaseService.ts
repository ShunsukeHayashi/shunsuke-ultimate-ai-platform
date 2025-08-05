/**
 * Database Service using Prisma
 * Ultimate ShunsukeModel Ecosystem
 */

import { PrismaClient } from '../generated/prisma';
import { AppError, ErrorCodes } from '../utils/errors';

export class DatabaseService {
  private prisma: PrismaClient;
  
  constructor() {
    this.prisma = new PrismaClient({
      log: process.env.NODE_ENV === 'development' 
        ? ['query', 'info', 'warn', 'error']
        : ['error']
    });
  }
  
  /**
   * Get Prisma client instance
   */
  getClient(): PrismaClient {
    return this.prisma;
  }
  
  /**
   * Connect to database
   */
  async connect(): Promise<void> {
    try {
      await this.prisma.$connect();
      console.log('✅ Database connected successfully');
    } catch (error) {
      console.error('❌ Database connection failed:', error);
      // In development, continue without database
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️  Running in development mode without database connection');
        return;
      }
      throw new AppError(
        'Failed to connect to database',
        ErrorCodes.CONFIG_ERROR,
        error
      );
    }
  }
  
  /**
   * Disconnect from database
   */
  async disconnect(): Promise<void> {
    await this.prisma.$disconnect();
    console.log('Database disconnected');
  }
  
  /**
   * Check database health
   */
  async checkHealth(): Promise<boolean> {
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      return true;
    } catch (error) {
      return false;
    }
  }
  
  /**
   * Run migrations
   */
  async runMigrations(): Promise<void> {
    console.log('Running database migrations...');
    // In production, migrations should be run separately
    // This is just for development convenience
    if (process.env.NODE_ENV === 'development') {
      const { execSync } = require('child_process');
      execSync('npx prisma migrate dev', { stdio: 'inherit' });
    }
  }
  
  /**
   * Seed database with initial data
   */
  async seed(): Promise<void> {
    console.log('Seeding database...');
    
    // Check if we already have users
    const userCount = await this.prisma.user.count();
    if (userCount > 0) {
      console.log('Database already seeded');
      return;
    }
    
    // Create demo users
    const bcrypt = require('bcryptjs');
    
    await this.prisma.user.createMany({
      data: [
        {
          email: 'demo@example.com',
          name: 'Demo User',
          passwordHash: await bcrypt.hash('demo123', 10),
          role: 'USER'
        },
        {
          email: 'admin@example.com',
          name: 'Admin User',
          passwordHash: await bcrypt.hash('admin123', 10),
          role: 'ADMIN'
        }
      ]
    });
    
    console.log('✅ Database seeded successfully');
  }
}

// Export singleton instance
export const databaseService = new DatabaseService();