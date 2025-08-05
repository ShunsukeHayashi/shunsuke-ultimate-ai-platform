/**
 * Authentication Middleware
 * Ultimate ShunsukeModel Ecosystem
 */

import { Request, Response, NextFunction } from 'express';
import { AuthServiceDb } from '../services/authServiceDb';
import { JWTPayload, UserRole } from '../types/auth';
import { AppError, ErrorCodes } from '../utils/errors';

// Extend Express Request type
declare global {
  namespace Express {
    interface Request {
      user?: JWTPayload;
    }
  }
}

const authService = new AuthServiceDb();

/**
 * Verify JWT token middleware
 */
export const authenticate = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    // Get token from header
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      throw new AppError('No authorization header', ErrorCodes.AUTHENTICATION_ERROR);
    }
    
    // Extract token
    const token = authHeader.startsWith('Bearer ') 
      ? authHeader.slice(7) 
      : authHeader;
    
    // Verify token
    const payload = await authService.verifyToken(token);
    
    // Attach user to request
    req.user = payload;
    
    next();
  } catch (error) {
    res.status(401).json({
      success: false,
      error: {
        code: ErrorCodes.AUTHENTICATION_ERROR,
        message: 'Authentication failed'
      }
    });
  }
};

/**
 * Check user role middleware
 */
export const authorize = (...roles: ('admin' | 'user')[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      res.status(401).json({
        success: false,
        error: {
          code: ErrorCodes.AUTHENTICATION_ERROR,
          message: 'Not authenticated'
        }
      });
      return;
    }
    
    if (!roles.includes(req.user.role)) {
      res.status(403).json({
        success: false,
        error: {
          code: ErrorCodes.AUTHORIZATION_ERROR,
          message: 'Insufficient permissions'
        }
      });
      return;
    }
    
    next();
  };
};

/**
 * Optional authentication middleware
 * Attaches user if token is present, but doesn't require it
 */
export const optionalAuth = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const authHeader = req.headers.authorization;
    if (authHeader) {
      const token = authHeader.startsWith('Bearer ') 
        ? authHeader.slice(7) 
        : authHeader;
      
      const payload = await authService.verifyToken(token);
      req.user = payload;
    }
  } catch (error) {
    // Ignore errors - this is optional auth
  }
  
  next();
};