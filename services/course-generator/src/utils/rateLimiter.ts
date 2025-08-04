/**
 * Rate Limiter Utility
 * Ultimate ShunsukeModel Ecosystem
 */

export class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillInterval: number;
  private queue: Array<() => void> = [];

  constructor(maxTokens: number, refillInterval: number) {
    this.maxTokens = maxTokens;
    this.tokens = maxTokens;
    this.refillInterval = refillInterval;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<void> {
    this.refill();
    
    if (this.tokens > 0) {
      this.tokens--;
      return;
    }
    
    // Wait for next available token
    return new Promise((resolve) => {
      this.queue.push(resolve);
    });
  }

  private refill(): void {
    const now = Date.now();
    const timePassed = now - this.lastRefill;
    const tokensToAdd = Math.floor(timePassed / this.refillInterval) * this.maxTokens;
    
    if (tokensToAdd > 0) {
      this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd);
      this.lastRefill = now;
      
      // Process waiting requests
      while (this.tokens > 0 && this.queue.length > 0) {
        const resolve = this.queue.shift();
        if (resolve) {
          this.tokens--;
          resolve();
        }
      }
    }
  }

  reset(): void {
    this.tokens = this.maxTokens;
    this.lastRefill = Date.now();
    this.queue = [];
  }

  getAvailableTokens(): number {
    this.refill();
    return this.tokens;
  }
}