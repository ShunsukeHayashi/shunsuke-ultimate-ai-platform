import { PrismaClient, PromptCategory, PromptTemplate, PromptUsage } from '../generated/prisma';

const prisma = new PrismaClient();

// Variable definition types
interface VariableDefinition {
  name: string;
  description: string;
  type: 'text' | 'number' | 'select' | 'boolean';
  default?: any;
  options?: string[]; // For select type
  required?: boolean;
}

interface CreateTemplateOptions {
  userId?: string;
  name: string;
  description?: string;
  category: PromptCategory;
  template: string;
  variables: VariableDefinition[];
  isPublic?: boolean;
}

interface UpdateTemplateOptions {
  name?: string;
  description?: string;
  template?: string;
  variables?: VariableDefinition[];
  isPublic?: boolean;
}

interface GeneratePromptOptions {
  templateId: string;
  userId: string;
  variables: Record<string, any>;
  courseId?: string;
}

export class PromptTemplateService {
  // Create a new prompt template
  async createTemplate(options: CreateTemplateOptions): Promise<PromptTemplate> {
    try {
      const template = await prisma.promptTemplate.create({
        data: {
          userId: options.userId,
          name: options.name,
          description: options.description,
          category: options.category,
          template: options.template,
          variables: options.variables as any,
          isPublic: options.isPublic || false,
        },
      });

      console.log('Prompt template created', { templateId: template.id, name: template.name });
      return template;
    } catch (error) {
      console.error('Failed to create prompt template', error);
      throw error;
    }
  }

  // Get all templates (user's and public)
  async getTemplates(userId?: string, category?: PromptCategory): Promise<PromptTemplate[]> {
    try {
      const where: any = {
        OR: [
          { isPublic: true },
          ...(userId ? [{ userId }] : []),
        ],
      };

      if (category) {
        where.category = category;
      }

      const templates = await prisma.promptTemplate.findMany({
        where,
        orderBy: [
          { isDefault: 'desc' },
          { createdAt: 'desc' },
        ],
      });

      return templates;
    } catch (error) {
      console.error('Failed to get prompt templates', error);
      throw error;
    }
  }

  // Get public templates only
  async getPublicTemplates(category?: PromptCategory): Promise<PromptTemplate[]> {
    try {
      const where: any = {
        isPublic: true,
      };

      if (category) {
        where.category = category;
      }

      const templates = await prisma.promptTemplate.findMany({
        where,
        orderBy: [
          { isDefault: 'desc' },
          { createdAt: 'desc' },
        ],
      });

      return templates;
    } catch (error) {
      console.error('Failed to get public templates', error);
      throw error;
    }
  }

  // Get a single template
  async getTemplate(templateId: string, userId?: string): Promise<PromptTemplate | null> {
    try {
      const template = await prisma.promptTemplate.findFirst({
        where: {
          id: templateId,
          OR: [
            { isPublic: true },
            ...(userId ? [{ userId }] : []),
          ],
        },
      });

      return template;
    } catch (error) {
      console.error('Failed to get prompt template', error);
      throw error;
    }
  }

  // Update a template
  async updateTemplate(
    templateId: string,
    userId: string,
    updates: UpdateTemplateOptions
  ): Promise<PromptTemplate> {
    try {
      // Verify ownership
      const existing = await prisma.promptTemplate.findFirst({
        where: { id: templateId, userId },
      });

      if (!existing) {
        throw new Error('Template not found or access denied');
      }

      const updateData: any = {
        ...updates,
        updatedAt: new Date(),
      };
      
      if (updates.variables) {
        updateData.variables = updates.variables;
      }
      
      const template = await prisma.promptTemplate.update({
        where: { id: templateId },
        data: updateData,
      });

      console.info('Prompt template updated', { templateId, userId });
      return template;
    } catch (error) {
      console.error('Failed to update prompt template', error);
      throw error;
    }
  }

  // Delete a template
  async deleteTemplate(templateId: string, userId: string): Promise<void> {
    try {
      // Verify ownership
      const template = await prisma.promptTemplate.findFirst({
        where: { id: templateId, userId },
      });

      if (!template) {
        throw new Error('Template not found or access denied');
      }

      await prisma.promptTemplate.delete({
        where: { id: templateId },
      });

      console.info('Prompt template deleted', { templateId, userId });
    } catch (error) {
      console.error('Failed to delete prompt template', error);
      throw error;
    }
  }

  // Generate prompt from template
  async generatePrompt(options: GeneratePromptOptions): Promise<string> {
    try {
      const template = await this.getTemplate(options.templateId, options.userId);
      if (!template) {
        throw new Error('Template not found');
      }

      // Replace variables in template
      let prompt = template.template;
      const variables = (template.variables as unknown) as VariableDefinition[];
      const usedVariables: Record<string, any> = {};

      // Validate and replace variables
      for (const varDef of variables) {
        const value = options.variables[varDef.name] ?? varDef.default;
        
        if (varDef.required && !value) {
          throw new Error(`Required variable '${varDef.name}' not provided`);
        }

        if (value !== undefined) {
          const placeholder = `{{${varDef.name}}}`;
          prompt = prompt.replace(new RegExp(placeholder, 'g'), String(value));
          usedVariables[varDef.name] = value;
        }
      }

      // Log usage
      await prisma.promptUsage.create({
        data: {
          templateId: options.templateId,
          userId: options.userId,
          courseId: options.courseId,
          variables: usedVariables,
          prompt,
        },
      });

      return prompt;
    } catch (error) {
      console.error('Failed to generate prompt', error);
      throw error;
    }
  }

  // Get template usage statistics
  async getTemplateUsageStats(templateId: string, userId: string): Promise<{
    totalUsage: number;
    recentUsage: PromptUsage[];
    averageTokens: number;
    averageResponseTime: number;
  }> {
    try {
      // Verify access
      const template = await this.getTemplate(templateId, userId);
      if (!template || (!template.isPublic && template.userId !== userId)) {
        throw new Error('Template not found or access denied');
      }

      const [totalUsage, recentUsage, stats] = await Promise.all([
        prisma.promptUsage.count({
          where: { templateId },
        }),
        prisma.promptUsage.findMany({
          where: { templateId },
          orderBy: { createdAt: 'desc' },
          take: 10,
        }),
        prisma.promptUsage.aggregate({
          where: { 
            templateId,
            tokensUsed: { not: null },
            responseTime: { not: null },
          },
          _avg: {
            tokensUsed: true,
            responseTime: true,
          },
        }),
      ]);

      return {
        totalUsage,
        recentUsage,
        averageTokens: Math.round(stats._avg.tokensUsed || 0),
        averageResponseTime: Math.round(stats._avg.responseTime || 0),
      };
    } catch (error) {
      console.error('Failed to get template usage stats', error);
      throw error;
    }
  }

  // Initialize default templates
  async initializeDefaultTemplates(): Promise<void> {
    try {
      const defaultTemplates = [
        {
          name: 'デフォルトコース生成',
          description: 'コース全体を生成するための標準テンプレート',
          category: PromptCategory.COURSE_GENERATION,
          template: `あなたは{{instructorName}}という名前の{{field}}分野の専門講師です。
以下の条件でコースを作成してください：

分野: {{field}}
レベル: {{level}}
対象者: {{audience}}
言語: {{language}}

{{additionalRequirements}}

コース構造は以下の形式で生成してください：
- コース名
- コース概要
- モジュール（各モジュールにセクションとレッスンを含む）`,
          variables: [
            { name: 'instructorName', description: '講師名', type: 'text', default: 'AI講師', required: true },
            { name: 'field', description: '専門分野', type: 'text', required: true },
            { name: 'level', description: '難易度', type: 'select', options: ['初級', '中級', '上級'], default: '初級' },
            { name: 'audience', description: '対象者', type: 'text', default: '一般学習者' },
            { name: 'language', description: '言語', type: 'select', options: ['ja', 'en'], default: 'ja' },
            { name: 'additionalRequirements', description: '追加要件', type: 'text', required: false },
          ],
          isPublic: true,
          isDefault: true,
        },
        {
          name: 'レッスンスクリプト生成',
          description: 'レッスンの詳細スクリプトを生成',
          category: PromptCategory.SCRIPT_GENERATION,
          template: `あなたは{{instructorName}}です。{{tone}}のトーンで、{{lessonTitle}}について説明してください。

説明時間: 約{{duration}}分
含めるべき内容:
{{contentPoints}}

{{specialInstructions}}`,
          variables: [
            { name: 'instructorName', description: '講師名', type: 'text', required: true },
            { name: 'tone', description: 'トーン', type: 'select', options: ['フレンドリー', 'プロフェッショナル', 'カジュアル'], default: 'フレンドリー' },
            { name: 'lessonTitle', description: 'レッスンタイトル', type: 'text', required: true },
            { name: 'duration', description: '説明時間（分）', type: 'number', default: 5 },
            { name: 'contentPoints', description: '含めるべき内容', type: 'text', required: true },
            { name: 'specialInstructions', description: '特別な指示', type: 'text', required: false },
          ],
          isPublic: true,
          isDefault: true,
        },
      ];

      for (const templateData of defaultTemplates) {
        const existing = await prisma.promptTemplate.findFirst({
          where: {
            name: templateData.name,
            isDefault: true,
          },
        });

        if (!existing) {
          await prisma.promptTemplate.create({
            data: templateData as any,
          });
          console.info('Default template created', { name: templateData.name });
        }
      }
    } catch (error) {
      console.error('Failed to initialize default templates', error);
      throw error;
    }
  }
}

// Export singleton instance
export const promptTemplateService = new PromptTemplateService();