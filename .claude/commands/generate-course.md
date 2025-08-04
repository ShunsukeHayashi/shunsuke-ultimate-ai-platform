# generate-course

AI Course Generatorを使用してコースを生成します。

## 使用方法

```
/generate-course [URL or テキスト]
```

## 例

```
/generate-course https://docs.example.com/tutorial
/generate-course TypeScriptの高度な型システムについて
```

## 動作

1. 指定されたソース（URLまたはテキスト）からコンテンツを抽出
2. Gemini AIを使用してコース構造を生成
3. 各レッスンのスクリプトを作成
4. 音声ナレーションを生成（オプション）
5. エクスポート可能な形式で保存

## 実装

```javascript
// Parse arguments
const args = $ARGUMENTS.trim();
let sources = [];

if (args.startsWith('http')) {
  sources.push({ type: 'url', content: args });
} else {
  sources.push({ type: 'text', content: args });
}

// Generate course
const response = await fetch('http://localhost:3002/api/generate-course', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sources,
    metadata: {
      course_title: `${args.slice(0, 50)}... Generated Course`,
      course_description: 'AI-generated course content',
      specialty_field: 'Technology',
      profession: 'Technical Instructor',
      avatar: 'AI Assistant',
      tone_of_voice: 'Professional and friendly'
    },
    options: {
      includeAudio: false,
      language: 'ja'
    }
  })
});

const result = await response.json();

if (result.success) {
  console.log('✅ Course generated successfully!');
  console.log(`Title: ${result.course.metadata.course_title}`);
  console.log(`Modules: ${result.course.modules.length}`);
  console.log(`Total lessons: ${result.course.modules.reduce((acc, m) => 
    acc + m.sections.reduce((acc2, s) => acc2 + s.lessons.length, 0), 0)}`);
} else {
  console.error('❌ Failed to generate course:', result.error.message);
}
```