# export-course

生成したコースを指定の形式でエクスポートします。

## 使用方法

```
/export-course [format] [course-id]
```

## 形式オプション

- `json` - JSON形式
- `markdown` - Markdown形式
- `html` - HTML形式
- `pdf` - PDF形式
- `scorm` - SCORM形式（LMS用）
- `zip` - ZIP圧縮ファイル

## 例

```
/export-course zip latest
/export-course markdown course-123
/export-course scorm
```

## 実装

```javascript
// Parse arguments
const [format = 'zip', courseId = 'latest'] = $ARGUMENTS.split(' ');

// Get course data (assuming it's stored somewhere)
const course = await getCourseData(courseId);

if (!course) {
  console.error('❌ Course not found');
  return;
}

// Export course
const response = await fetch('http://localhost:3002/api/export-course', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    course: course.data,
    scripts: course.scripts || {},
    audioFiles: course.audioFiles || {},
    exportOptions: {
      format,
      includeAudio: true,
      includeScripts: true,
      includeMetadata: true
    }
  })
});

const result = await response.json();

if (result.success) {
  console.log(`✅ Course exported successfully!`);
  console.log(`Format: ${result.export.format}`);
  console.log(`File: ${result.export.filePath}`);
  console.log(`Size: ${(result.export.fileSize / 1024 / 1024).toFixed(2)} MB`);
} else {
  console.error('❌ Failed to export course:', result.error.message);
}
```