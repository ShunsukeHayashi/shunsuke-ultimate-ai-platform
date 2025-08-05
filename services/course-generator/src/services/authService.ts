/**
 * Authentication Service - Simplified Version
 * Ultimate ShunsukeModel Ecosystem
 */

import { 
  User, 
  UserRole, 
  LoginCredentials, 
  RegisterData, 
  JWTPayload, 
  AuthTokens,
  AuthResponse 
} from '../types/auth';
import { AppError, ErrorCodes } from '../utils/errors';

export class AuthService {
  // In-memory user store (for demo purposes)
  private users: Map<string, User> = new Map();
  
  constructor() {
    // Initialize with demo users
    this.initializeDemoUsers();
  }
  
  /**
   * Initialize demo users
   */
  private initializeDemoUsers() {
    const demoUser: User = {
      id: '1',
      email: 'demo@example.com',
      name: 'Demo User',
      passwordHash: 'demo123', // In production, this should be hashed
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isActive: true,
      role: 'user' as const
    };
    
    const adminUser: User = {
      id: '2',
      email: 'admin@example.com',
      name: 'Admin User',
      passwordHash: 'admin123', // In production, this should be hashed
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isActive: true,
      role: 'admin' as const
    };
    
    this.users.set(demoUser.email, demoUser);
    this.users.set(adminUser.email, adminUser);
  }
  
  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    // Check if user already exists
    if (this.users.has(data.email)) {
      throw new AppError('User already exists', ErrorCodes.VALIDATION_ERROR);
    }
    
    // Create new user
    const newUser: User = {
      id: Date.now().toString(),
      email: data.email,
      name: data.name,
      passwordHash: data.password, // In production, hash this
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isActive: true,
      role: 'user' as const
    };
    
    // Save user
    this.users.set(newUser.email, newUser);
    
    // Generate tokens
    const tokens = this.generateTokens(newUser);
    
    // Return response
    const { passwordHash: _, ...userWithoutPassword } = newUser;
    return {
      user: userWithoutPassword,
      tokens
    };
  }
  
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Find user
    const user = this.users.get(credentials.email);
    if (!user) {
      throw new AppError('Invalid credentials', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Simple password check (in production, use bcrypt)
    if (user.passwordHash !== credentials.password) {
      throw new AppError('Invalid credentials', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Check if user is active
    if (!user.isActive) {
      throw new AppError('Account is disabled', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Update last login
    user.lastLoginAt = new Date().toISOString();
    this.users.set(user.email, user);
    
    // Generate tokens
    const tokens = this.generateTokens(user);
    
    // Return response
    const { passwordHash: _, ...userWithoutPassword } = user;
    return {
      user: userWithoutPassword,
      tokens
    };
  }
  
  /**
   * Verify JWT token (simplified)
   */
  async verifyToken(token: string): Promise<JWTPayload> {
    // For demo purposes, just decode the base64 token
    try {
      const decoded = JSON.parse(Buffer.from(token, 'base64').toString());
      return decoded as JWTPayload;
    } catch (error) {
      throw new AppError('Invalid token', ErrorCodes.AUTHENTICATION_ERROR);
    }
  }
  
  /**
   * Get user by ID
   */
  async getUserById(userId: string): Promise<User | null> {
    for (const user of this.users.values()) {
      if (user.id === userId) {
        return user;
      }
    }
    return null;
  }
  
  /**
   * Generate JWT tokens (simplified)
   */
  private generateTokens(user: User): AuthTokens {
    const payload: JWTPayload = {
      userId: user.id,
      email: user.email,
      role: user.role
    };
    
    // For demo purposes, just base64 encode the payload
    const accessToken = Buffer.from(JSON.stringify(payload)).toString('base64');
    
    return {
      accessToken,
      expiresIn: 7 * 24 * 60 * 60 // 7 days in seconds
    };
  }
  
  /**
   * Get all users (admin only)
   */
  async getAllUsers(): Promise<Omit<User, 'passwordHash'>[]> {
    const users: Omit<User, 'passwordHash'>[] = [];
    
    for (const user of this.users.values()) {
      const { passwordHash, ...userWithoutPassword } = user;
      users.push(userWithoutPassword);
    }
    
    return users;
  }
}