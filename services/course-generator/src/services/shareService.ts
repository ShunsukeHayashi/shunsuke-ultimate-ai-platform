import { PrismaClient, SharePermission } from '../generated/prisma';
import crypto from 'crypto';
import bcrypt from 'bcryptjs';

export interface CreateShareOptions {
  courseId: string;
  userId: string;
  permission?: SharePermission;
  sharedWithEmail?: string;
  description?: string;
  expiresAt?: Date;
  maxViews?: number;
  password?: string;
}

export interface ShareAccess {
  shareToken: string;
  password?: string;
  accessedBy?: string;
  userAgent?: string;
}

class ShareService {
  private prisma: PrismaClient;

  constructor(prisma: PrismaClient) {
    this.prisma = prisma;
  }

  /**
   * Create a shareable link for a course
   */
  async createShare(options: CreateShareOptions) {
    const { courseId, userId, password, ...shareData } = options;

    // Verify the user owns the course
    const course = await this.prisma.course.findFirst({
      where: {
        id: courseId,
        userId: userId
      }
    });

    if (!course) {
      throw new Error('Course not found or unauthorized');
    }

    // Hash password if provided
    let hashedPassword: string | undefined;
    if (password) {
      hashedPassword = await bcrypt.hash(password, 10);
    }

    // Create the share
    const share = await this.prisma.courseShare.create({
      data: {
        courseId,
        sharedBy: userId,
        permission: shareData.permission || 'VIEW_ONLY',
        sharedWithEmail: shareData.sharedWithEmail,
        description: shareData.description,
        expiresAt: shareData.expiresAt,
        maxViews: shareData.maxViews,
        password: hashedPassword
      }
    });

    return {
      ...share,
      shareUrl: this.generateShareUrl(share.shareToken)
    };
  }

  /**
   * Get all shares for a user's courses
   */
  async getUserShares(userId: string) {
    const shares = await this.prisma.courseShare.findMany({
      where: {
        course: {
          userId: userId
        }
      },
      include: {
        course: {
          select: {
            id: true,
            title: true,
            description: true
          }
        },
        _count: {
          select: {
            accessLogs: true
          }
        }
      },
      orderBy: {
        createdAt: 'desc'
      }
    });

    return shares.map(share => ({
      ...share,
      shareUrl: this.generateShareUrl(share.shareToken),
      totalAccess: share._count.accessLogs
    }));
  }

  /**
   * Access a shared course
   */
  async accessShare(access: ShareAccess) {
    const { shareToken, password, accessedBy, userAgent } = access;

    // Find the share
    const share = await this.prisma.courseShare.findUnique({
      where: {
        shareToken
      },
      include: {
        course: {
          include: {
            user: {
              select: {
                id: true,
                name: true,
                email: true
              }
            }
          }
        }
      }
    });

    if (!share) {
      throw new Error('Share not found');
    }

    // Check if share is active
    if (!share.isActive) {
      throw new Error('Share is no longer active');
    }

    // Check expiration
    if (share.expiresAt && share.expiresAt < new Date()) {
      throw new Error('Share has expired');
    }

    // Check view limit
    if (share.maxViews && share.currentViews >= share.maxViews) {
      throw new Error('Share has reached maximum views');
    }

    // Check password
    if (share.password) {
      if (!password) {
        throw new Error('Password required');
      }
      const isPasswordValid = await bcrypt.compare(password, share.password);
      if (!isPasswordValid) {
        throw new Error('Invalid password');
      }
    }

    // Update share access
    await this.prisma.$transaction([
      // Log access
      this.prisma.shareAccessLog.create({
        data: {
          shareId: share.id,
          accessedBy,
          userAgent,
          action: 'view'
        }
      }),
      // Update share stats
      this.prisma.courseShare.update({
        where: {
          id: share.id
        },
        data: {
          currentViews: share.currentViews + 1,
          lastAccessedAt: new Date()
        }
      })
    ]);

    return {
      course: share.course,
      permission: share.permission,
      sharedBy: share.course.user
    };
  }

  /**
   * Update share settings
   */
  async updateShare(shareId: string, userId: string, updates: Partial<CreateShareOptions>) {
    // Verify ownership
    const share = await this.prisma.courseShare.findFirst({
      where: {
        id: shareId,
        course: {
          userId: userId
        }
      }
    });

    if (!share) {
      throw new Error('Share not found or unauthorized');
    }

    // Hash password if provided
    let hashedPassword: string | undefined | null = undefined;
    if ('password' in updates) {
      hashedPassword = updates.password ? await bcrypt.hash(updates.password, 10) : null;
    }

    const updatedShare = await this.prisma.courseShare.update({
      where: {
        id: shareId
      },
      data: {
        permission: updates.permission,
        sharedWithEmail: updates.sharedWithEmail,
        description: updates.description,
        expiresAt: updates.expiresAt,
        maxViews: updates.maxViews,
        password: hashedPassword !== undefined ? hashedPassword : undefined
      }
    });

    return {
      ...updatedShare,
      shareUrl: this.generateShareUrl(updatedShare.shareToken)
    };
  }

  /**
   * Delete a share
   */
  async deleteShare(shareId: string, userId: string) {
    // Verify ownership
    const share = await this.prisma.courseShare.findFirst({
      where: {
        id: shareId,
        course: {
          userId: userId
        }
      }
    });

    if (!share) {
      throw new Error('Share not found or unauthorized');
    }

    await this.prisma.courseShare.delete({
      where: {
        id: shareId
      }
    });

    return { success: true };
  }

  /**
   * Toggle share active status
   */
  async toggleShareStatus(shareId: string, userId: string) {
    // Verify ownership
    const share = await this.prisma.courseShare.findFirst({
      where: {
        id: shareId,
        course: {
          userId: userId
        }
      }
    });

    if (!share) {
      throw new Error('Share not found or unauthorized');
    }

    const updatedShare = await this.prisma.courseShare.update({
      where: {
        id: shareId
      },
      data: {
        isActive: !share.isActive
      }
    });

    return updatedShare;
  }

  /**
   * Get share access logs
   */
  async getShareAccessLogs(shareId: string, userId: string) {
    // Verify ownership
    const share = await this.prisma.courseShare.findFirst({
      where: {
        id: shareId,
        course: {
          userId: userId
        }
      }
    });

    if (!share) {
      throw new Error('Share not found or unauthorized');
    }

    const logs = await this.prisma.shareAccessLog.findMany({
      where: {
        shareId
      },
      orderBy: {
        createdAt: 'desc'
      },
      take: 100
    });

    return logs;
  }

  /**
   * Generate share URL
   */
  private generateShareUrl(shareToken: string): string {
    // In production, this should use environment variable for base URL
    const baseUrl = process.env.SHARE_BASE_URL || 'http://localhost:3000';
    return `${baseUrl}/share/${shareToken}`;
  }
}

export default ShareService;