/**
 * Seed script for prompt templates
 * Ultimate ShunsukeModel Ecosystem
 */

import { PrismaClient } from '../src/generated/prisma';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding prompt templates...');

  // Course structure templates
  await prisma.promptTemplate.create({
    data: {
      name: 'ビジネススキル向上コース',
      description: 'ビジネススキルの向上に特化したコース構造を生成',
      category: 'COURSE_GENERATION',
      template: `
あなたは{{expertise}}の専門家です。以下の内容から実践的なビジネススキル向上コースを作成してください。

【重視する要素】
- {{focus_areas}}
- 実践的なケーススタディ
- アクションプランの提示

【ソースコンテンツ】
{{content}}

【コース情報】
- タイトル: {{course_title}}
- 説明: {{course_description}}
- 対象者: {{target_audience}}

JSONフォーマットで実践的なコース構造を出力してください。`,
      variables: [
        {
          name: 'expertise',
          label: '専門分野',
          type: 'text',
          required: true,
          defaultValue: 'ビジネスコンサルタント',
        },
        {
          name: 'focus_areas',
          label: '重点領域',
          type: 'select',
          required: true,
          options: ['リーダーシップ', 'コミュニケーション', '問題解決', '戦略的思考'],
          defaultValue: 'リーダーシップ',
        },
      ],
      isPublic: true,
      isDefault: false,
    },
  });

  await prisma.promptTemplate.create({
    data: {
      name: 'テクニカルスキル習得コース',
      description: 'プログラミングや技術系スキルの習得に最適化',
      category: 'COURSE_GENERATION',
      template: `
あなたは{{tech_stack}}のエキスパートです。初心者から上級者まで段階的に学べるテクニカルコースを設計してください。

【学習パス】
- 基礎概念の理解
- ハンズオン演習
- {{project_type}}の実装
- ベストプラクティス

【ソースコンテンツ】
{{content}}

【追加要件】
{{additional_requirements}}

実践的で段階的な学習ができるコース構造をJSON形式で出力してください。`,
      variables: [
        {
          name: 'tech_stack',
          label: '技術スタック',
          type: 'text',
          required: true,
          placeholder: '例: React, Node.js, Python',
        },
        {
          name: 'project_type',
          label: 'プロジェクトタイプ',
          type: 'select',
          required: true,
          options: ['Webアプリケーション', 'モバイルアプリ', 'API開発', 'データ分析'],
          defaultValue: 'Webアプリケーション',
        },
        {
          name: 'additional_requirements',
          label: '追加要件',
          type: 'textarea',
          required: false,
          placeholder: '特に重視したい内容や含めたいトピック',
        },
      ],
      isPublic: true,
      isDefault: false,
    },
  });

  // Lesson script templates
  await prisma.promptTemplate.create({
    data: {
      name: 'エンゲージング講義スタイル',
      description: '聞き手を引き込む対話的な講義スクリプトを生成',
      category: 'SCRIPT_GENERATION',
      template: `
あなたは{{personality}}として知られる{{metadata.profession}}です。

【レッスン情報】
- タイトル: {{lesson.lesson_title}}
- 長さ: {{lesson.script_length_minutes}}分
- モジュール: {{moduleContext.name}}

【講義スタイル】
- {{teaching_style}}
- 具体例を{{example_frequency}}含める
- {{interaction_type}}を促す

以下の構成で魅力的なスクリプトを作成してください：

1. フック（聞き手の興味を引く導入）
2. 本編（{{content_structure}}）
3. 実践的なアドバイス
4. 次回への期待を高める締めくくり

自然な話し言葉で、{{metadata.tone_of_voice}}を意識して書いてください。`,
      variables: [
        {
          name: 'personality',
          label: '講師のキャラクター',
          type: 'text',
          required: true,
          defaultValue: '親しみやすいメンター',
        },
        {
          name: 'teaching_style',
          label: '教授スタイル',
          type: 'select',
          required: true,
          options: ['ストーリーテリング型', '実践重視型', '理論解説型', 'ケーススタディ型'],
          defaultValue: 'ストーリーテリング型',
        },
        {
          name: 'example_frequency',
          label: '具体例の頻度',
          type: 'select',
          required: true,
          options: ['多めに', '適度に', '必要最小限'],
          defaultValue: '適度に',
        },
        {
          name: 'interaction_type',
          label: 'インタラクションタイプ',
          type: 'select',
          required: true,
          options: ['質問を投げかける', '考える時間を与える', '実践を促す'],
          defaultValue: '質問を投げかける',
        },
        {
          name: 'content_structure',
          label: 'コンテンツ構成',
          type: 'text',
          required: false,
          defaultValue: 'ステップバイステップの説明',
        },
      ],
      isPublic: true,
      isDefault: true,
    },
  });

  console.log('Prompt templates seeded successfully!');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });