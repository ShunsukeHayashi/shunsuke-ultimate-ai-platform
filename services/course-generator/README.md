# Course Generator Service

AI-powered course content generation service for the Ultimate ShunsukeModel Ecosystem.

## Overview

This service provides intelligent course generation capabilities using Google's Gemini AI. It can:

- Extract content from various sources (URLs, text, files)
- Generate structured course content with AI
- Create audio narration for lessons
- Export courses in multiple formats (JSON, Markdown, HTML, PDF, SCORM, ZIP)

## Features

- 🤖 **AI-Powered Generation**: Uses Gemini AI to create course structures and scripts
- 🌐 **Web Crawling**: Extract content from websites automatically
- 🎙️ **Audio Generation**: Text-to-speech for lesson narration
- 📦 **Multi-Format Export**: JSON, Markdown, HTML, PDF, SCORM, ZIP
- ⚡ **Rate Limiting**: Built-in rate limiting for external APIs
- 🔒 **Security**: Helmet, CORS, input validation

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

## API Endpoints

### Health Check
```http
GET /health
```

### Generate Course
```http
POST /api/generate-course
Content-Type: application/json

{
  "sources": [
    {
      "type": "url",
      "content": "https://example.com/tutorial"
    },
    {
      "type": "text",
      "content": "Course content here..."
    }
  ],
  "metadata": {
    "course_title": "Advanced TypeScript",
    "course_description": "Master TypeScript features",
    "specialty_field": "Web Development",
    "profession": "Software Engineer",
    "avatar": "Tech Instructor",
    "tone_of_voice": "Professional and friendly"
  },
  "options": {
    "includeAudio": true,
    "language": "ja",
    "audioVoice": "ja-JP-Standard-A"
  }
}
```

### Export Course
```http
POST /api/export-course
Content-Type: application/json

{
  "course": { /* course object */ },
  "scripts": { /* lesson scripts */ },
  "audioFiles": { /* base64 audio data */ },
  "exportOptions": {
    "format": "zip",
    "includeAudio": true,
    "includeScripts": true,
    "includeMetadata": true
  }
}
```

### Crawl URLs
```http
POST /api/crawl-urls
Content-Type: application/json

{
  "urls": ["https://example.com"],
  "settings": {
    "maxDepth": 2,
    "maxPagesPerDomain": 20
  }
}
```

### Get Available Voices
```http
GET /api/voices?provider=google
```

### Clear Cache
```http
POST /api/clear-cache
Content-Type: application/json

{
  "type": "all" // "all" | "audio" | "context" | "crawler"
}
```

## Architecture

```
course-generator/
├── src/
│   ├── index.ts          # Express server
│   ├── services/         # Core services
│   │   ├── geminiService.ts    # AI generation
│   │   ├── contextAgent.ts     # Content extraction
│   │   ├── webCrawlerService.ts # Web crawling
│   │   ├── audioService.ts      # Audio generation
│   │   └── exportService.ts     # Export handling
│   ├── types/            # TypeScript types
│   └── utils/            # Utilities
└── test/                 # Test files
```

## Development

```bash
# Run tests
npm test

# Type checking
npm run typecheck

# Linting
npm run lint

# Format code
npm run format
```

## Deployment

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | 3002 |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `CORS_ORIGIN` | Allowed CORS origins | * |
| `AUDIO_CACHE_DIR` | Audio cache directory | ./audio_cache |
| `EXPORT_DIR` | Export directory | ./exports |

## Integration with Ultimate AI Platform

This service is part of the Ultimate ShunsukeModel Ecosystem and integrates with:

- **Command Tower**: Central orchestration
- **Quality Guardian**: Content quality assurance
- **Claude Code**: AI-powered development assistance

## Contributing

1. Follow the established code patterns
2. Write tests for new features
3. Update documentation
4. Submit PR with @claude review

## License

Part of the Ultimate ShunsukeModel Ecosystem. See root LICENSE file.