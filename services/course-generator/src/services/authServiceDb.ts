/**
 * Authentication Service with Database
 * Ultimate ShunsukeModel Ecosystem
 */

import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { PrismaClient, User as PrismaUser, UserRole } from '../generated/prisma';
import { 
  User,
  LoginCredentials, 
  RegisterData, 
  JWTPayload, 
  AuthTokens,
  AuthResponse 
} from '../types/auth';
import { AppError, ErrorCodes } from '../utils/errors';
import { databaseService } from './databaseService';

export class AuthServiceDb {
  private prisma: PrismaClient;
  private jwtSecret: string;
  private jwtExpiry: string = '7d';
  private refreshExpiry: string = '30d';
  
  constructor() {
    this.prisma = databaseService.getClient();
    this.jwtSecret = process.env.JWT_SECRET || 'default-secret-change-in-production';
    
    if (!process.env.JWT_SECRET) {
      console.warn('⚠️  JWT_SECRET not set in environment variables. Using default secret.');
    }
  }
  
  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    // Check if user already exists
    const existingUser = await this.prisma.user.findUnique({
      where: { email: data.email }
    });
    
    if (existingUser) {
      throw new AppError('User already exists', ErrorCodes.VALIDATION_ERROR);
    }
    
    // Hash password
    const passwordHash = await bcrypt.hash(data.password, 10);
    
    // Create new user
    const newUser = await this.prisma.user.create({
      data: {
        email: data.email,
        name: data.name,
        passwordHash
      }
    });
    
    // Generate tokens
    const tokens = await this.generateTokens(newUser);
    
    // Return response without password
    const { passwordHash: _, ...userWithoutPassword } = newUser;
    return {
      user: this.convertPrismaUserToUser(userWithoutPassword),
      tokens
    };
  }
  
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Find user
    const user = await this.prisma.user.findUnique({
      where: { email: credentials.email }
    });
    
    if (!user) {
      throw new AppError('Invalid credentials', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Verify password
    const isValidPassword = await bcrypt.compare(credentials.password, user.passwordHash);
    if (!isValidPassword) {
      throw new AppError('Invalid credentials', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Check if user is active
    if (!user.isActive) {
      throw new AppError('Account is disabled', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Update last login
    await this.prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() }
    });
    
    // Generate tokens
    const tokens = await this.generateTokens(user);
    
    // Return response without password
    const { passwordHash: _, ...userWithoutPassword } = user;
    return {
      user: this.convertPrismaUserToUser(userWithoutPassword),
      tokens
    };
  }
  
  /**
   * Verify JWT token
   */
  async verifyToken(token: string): Promise<JWTPayload> {
    try {
      const decoded = jwt.verify(token, this.jwtSecret) as JWTPayload;
      return decoded;
    } catch (error) {
      throw new AppError('Invalid token', ErrorCodes.AUTHENTICATION_ERROR);
    }
  }
  
  /**
   * Get user by ID
   */
  async getUserById(userId: string): Promise<User | null> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId }
    });
    
    if (!user) return null;
    
    const { passwordHash, ...userWithoutPassword } = user;
    return this.convertPrismaUserToUser(userWithoutPassword);
  }
  
  /**
   * Get all users (admin only)
   */
  async getAllUsers(): Promise<Omit<User, 'passwordHash'>[]> {
    const users = await this.prisma.user.findMany({
      orderBy: { createdAt: 'desc' }
    });
    
    return users.map(user => {
      const { passwordHash, ...userWithoutPassword } = user;
      return this.convertPrismaUserToUser(userWithoutPassword);
    });
  }
  
  /**
   * Generate JWT tokens
   */
  private async generateTokens(user: PrismaUser): Promise<AuthTokens> {
    const payload = {
      userId: user.id,
      email: user.email,
      role: user.role.toLowerCase()
    };
    
    const accessToken = jwt.sign(payload, this.jwtSecret, {
      expiresIn: this.jwtExpiry
    } as jwt.SignOptions);
    
    // Store refresh token in database
    const refreshTokenPayload = { 
      userId: user.id, 
      type: 'refresh',
      timestamp: Date.now(),
      random: Math.random().toString(36).substring(2)
    };
    const refreshToken = jwt.sign(refreshTokenPayload, this.jwtSecret, {
      expiresIn: this.refreshExpiry
    } as jwt.SignOptions);
    
    await this.prisma.refreshToken.create({
      data: {
        token: refreshToken,
        userId: user.id,
        expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days
      }
    });
    
    return {
      accessToken,
      expiresIn: 7 * 24 * 60 * 60 // 7 days in seconds
    };
  }
  
  /**
   * Convert Prisma User to API User type
   */
  private convertPrismaUserToUser(user: Omit<PrismaUser, 'passwordHash'>): Omit<User, 'passwordHash'> {
    return {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role.toLowerCase() as 'user' | 'admin',
      isActive: user.isActive,
      createdAt: user.createdAt.toISOString(),
      updatedAt: user.updatedAt.toISOString(),
      lastLoginAt: user.lastLoginAt?.toISOString()
    };
  }
  
  /**
   * Clean up expired refresh tokens
   */
  async cleanupExpiredTokens(): Promise<void> {
    await this.prisma.refreshToken.deleteMany({
      where: {
        expiresAt: {
          lt: new Date()
        }
      }
    });
  }
}