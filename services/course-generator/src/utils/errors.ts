/**
 * Error Handling Utilities
 * Ultimate ShunsukeModel Ecosystem
 */

export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public originalError?: any,
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'AppError';
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      stack: this.stack
    };
  }
}

export const ErrorCodes = {
  // Configuration errors
  CONFIG_ERROR: 'CONFIG_ERROR',
  MISSING_API_KEY: 'MISSING_API_KEY',
  INVALID_CONFIG: 'INVALID_CONFIG',
  
  // AI errors
  AI_GENERATION_ERROR: 'AI_GENERATION_ERROR',
  AI_RATE_LIMIT: 'AI_RATE_LIMIT',
  AI_QUOTA_EXCEEDED: 'AI_QUOTA_EXCEEDED',
  
  // Content errors
  CONTENT_EXTRACTION_ERROR: 'CONTENT_EXTRACTION_ERROR',
  INVALID_URL: 'INVALID_URL',
  CONTENT_NOT_FOUND: 'CONTENT_NOT_FOUND',
  
  // Processing errors
  PARSE_ERROR: 'PARSE_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  PROCESSING_ERROR: 'PROCESSING_ERROR',
  
  // Export errors
  EXPORT_ERROR: 'EXPORT_ERROR',
  UNSUPPORTED_FORMAT: 'UNSUPPORTED_FORMAT',
  
  // Storage errors
  STORAGE_ERROR: 'STORAGE_ERROR',
  QUOTA_EXCEEDED: 'QUOTA_EXCEEDED',
  
  // Network errors
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  
  // Auth errors
  AUTH_ERROR: 'AUTH_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  
  // Not found
  NOT_FOUND: 'NOT_FOUND',
  
  // Cache errors
  CACHE_ERROR: 'CACHE_ERROR',
  
  // Service availability
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  
  // Database errors
  DATABASE_ERROR: 'DATABASE_ERROR'
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

export function isAppError(error: any): error is AppError {
  return error instanceof AppError;
}

export function handleError(error: any): AppError {
  if (isAppError(error)) {
    return error;
  }
  
  // Handle specific error types
  if (error.code === 'ECONNREFUSED') {
    return new AppError(
      'サービスに接続できません',
      ErrorCodes.NETWORK_ERROR,
      error,
      503
    );
  }
  
  if (error.code === 'ETIMEDOUT') {
    return new AppError(
      'リクエストがタイムアウトしました',
      ErrorCodes.TIMEOUT_ERROR,
      error,
      504
    );
  }
  
  if (error.response?.status === 429) {
    return new AppError(
      'レート制限に達しました。しばらくお待ちください',
      ErrorCodes.AI_RATE_LIMIT,
      error,
      429
    );
  }
  
  if (error.response?.status === 401) {
    return new AppError(
      '認証が必要です',
      ErrorCodes.UNAUTHORIZED,
      error,
      401
    );
  }
  
  if (error.response?.status === 403) {
    return new AppError(
      'アクセスが拒否されました',
      ErrorCodes.FORBIDDEN,
      error,
      403
    );
  }
  
  // Default error
  return new AppError(
    error.message || '予期しないエラーが発生しました',
    ErrorCodes.PROCESSING_ERROR,
    error,
    500
  );
}