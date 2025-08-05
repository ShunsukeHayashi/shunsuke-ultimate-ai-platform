/**
 * Course Generator 機能テストスイート
 * 主要機能の統合テスト
 */

const axios = require('axios');
const FormData = require('form-data');

const API_BASE_URL = 'http://localhost:3002';
const TEST_USER = {
  email: `test-${Date.now()}@example.com`, // Use unique email
  password: 'testPassword123',
  name: 'Test User'
};

// カラー出力用のヘルパー
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

const log = {
  success: (msg) => console.log(`${colors.green}✅ ${msg}${colors.reset}`),
  error: (msg) => console.log(`${colors.red}❌ ${msg}${colors.reset}`),
  info: (msg) => console.log(`${colors.blue}ℹ️  ${msg}${colors.reset}`),
  warning: (msg) => console.log(`${colors.yellow}⚠️  ${msg}${colors.reset}`)
};

// テストレポート
const testReport = {
  total: 0,
  passed: 0,
  failed: 0,
  errors: []
};

// テスト実行ヘルパー
async function runTest(testName, testFn) {
  testReport.total++;
  try {
    await testFn();
    testReport.passed++;
    log.success(`${testName}`);
  } catch (error) {
    testReport.failed++;
    testReport.errors.push({ test: testName, error: error.message });
    log.error(`${testName}: ${error.message}`);
  }
}

// APIクライアント
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// セッションを保持
let authToken = null;
let userId = null;

// テスト実装
async function testHealthCheck() {
  const response = await api.get('/api/health');
  if (response.status !== 200) {
    throw new Error(`Expected status 200, got ${response.status}`);
  }
  if (!response.data.status === 'healthy') {
    throw new Error('API is not healthy');
  }
}

async function testUserRegistration() {
  const response = await api.post('/api/auth/register', TEST_USER);
  if (response.status !== 200) {
    throw new Error(`Expected status 200, got ${response.status}`);
  }
  
  if (!response.data.user || !response.data.tokens) {
    throw new Error('User or tokens not returned in registration response');
  }
  
  userId = response.data.user.id;
  authToken = response.data.tokens.accessToken;
  api.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
}

async function testUserLogin() {
  const response = await api.post('/api/auth/login', {
    email: TEST_USER.email,
    password: TEST_USER.password
  });
  
  if (!response.data.tokens || !response.data.tokens.accessToken) {
    throw new Error('No access token received');
  }
  
  authToken = response.data.tokens.accessToken;
  userId = response.data.user.id;
  api.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
}

async function testGetProfile() {
  const response = await api.get('/api/users/profile');
  
  if (response.data.email !== TEST_USER.email) {
    throw new Error('Profile email mismatch');
  }
}

async function testCreateCourse() {
  const courseData = {
    title: 'Test Course - JavaScript基礎',
    topic: 'JavaScript プログラミング基礎',
    difficulty: 'beginner',
    language: 'ja',
    generateContent: true
  };
  
  const response = await api.post('/api/courses', courseData);
  
  if (!response.data.id) {
    throw new Error('Course ID not returned');
  }
  
  return response.data.id;
}

async function testGetCourses() {
  const response = await api.get('/api/courses');
  
  if (!Array.isArray(response.data)) {
    throw new Error('Expected array of courses');
  }
  
  if (response.data.length === 0) {
    log.warning('No courses found');
  }
}

async function testPromptTemplates() {
  // テンプレート一覧取得
  const listResponse = await api.get('/api/prompt-templates');
  
  if (!Array.isArray(listResponse.data)) {
    throw new Error('Expected array of templates');
  }
  
  // 新しいテンプレート作成
  const templateData = {
    name: 'Test Template',
    description: 'テスト用プロンプトテンプレート',
    template: 'Create a course about {{topic}} for {{level}} learners',
    variables: ['topic', 'level'],
    category: 'COURSE_GENERATION',
    isPublic: false
  };
  
  const createResponse = await api.post('/api/prompt-templates', templateData);
  
  if (!createResponse.data.template || !createResponse.data.template.id) {
    throw new Error('Template ID not returned');
  }
  
  return createResponse.data.template.id;
}

async function testWebCrawling() {
  const crawlData = {
    url: 'https://example.com',
    maxDepth: 1
  };
  
  try {
    const response = await api.post('/api/web-crawler/crawl', crawlData);
    
    if (!response.data.content) {
      throw new Error('No content returned from crawler');
    }
  } catch (error) {
    if (error.response?.status === 429) {
      log.warning('Rate limit reached for web crawler');
    } else {
      throw error;
    }
  }
}

async function testExportCourse(courseId) {
  if (!courseId) {
    log.warning('No course ID available for export test');
    return;
  }
  
  const formats = ['json', 'markdown', 'pdf'];
  
  for (const format of formats) {
    try {
      const response = await api.get(`/api/courses/${courseId}/export?format=${format}`, {
        responseType: format === 'pdf' ? 'arraybuffer' : 'json'
      });
      
      if (response.status !== 200) {
        throw new Error(`Export failed for format: ${format}`);
      }
      
      log.info(`Export ${format}: Success`);
    } catch (error) {
      if (error.response?.status === 404) {
        log.warning(`Export format ${format} not implemented`);
      } else {
        throw error;
      }
    }
  }
}

async function testCourseSharing(courseId) {
  if (!courseId) {
    log.warning('No course ID available for sharing test');
    return;
  }
  
  // コース共有を作成
  const response = await api.post(`/api/courses/${courseId}/share`);
  
  if (!response.data.share || !response.data.share.shareToken) {
    throw new Error('Share token not returned');
  }
  
  // 共有リンクでアクセス
  const shareResponse = await api.get(`/api/share/${response.data.share.shareToken}`);
  
  if (!shareResponse.data.course || shareResponse.data.course.id !== courseId) {
    throw new Error('Shared course ID mismatch');
  }
}

async function testProgressTracking(courseId) {
  if (!courseId) {
    log.warning('No course ID available for progress test');
    return;
  }
  
  const progressData = {
    courseId,
    lessonId: 'lesson-1',
    progress: 50,
    completed: false
  };
  
  const response = await api.post('/api/progress', progressData);
  
  if (response.data.progress !== 50) {
    throw new Error('Progress not saved correctly');
  }
}

// メインテスト実行
async function runAllTests() {
  console.log('\n🧪 Course Generator 機能テスト開始\n');
  
  // 1. 基本的なAPIテスト
  console.log(colors.blue + '=== 基本APIテスト ===' + colors.reset);
  await runTest('ヘルスチェック', testHealthCheck);
  
  // 2. 認証テスト
  console.log(colors.blue + '\n=== 認証機能テスト ===' + colors.reset);
  await runTest('ユーザー登録', testUserRegistration);
  await runTest('ユーザーログイン', testUserLogin);
  await runTest('プロフィール取得', testGetProfile);
  
  // 3. コース機能テスト
  console.log(colors.blue + '\n=== コース機能テスト ===' + colors.reset);
  let courseId = null;
  await runTest('コース作成', async () => {
    courseId = await testCreateCourse();
    log.info(`Created course ID: ${courseId}`);
  });
  await runTest('コース一覧取得', testGetCourses);
  
  // 4. プロンプトテンプレート
  console.log(colors.blue + '\n=== テンプレート機能テスト ===' + colors.reset);
  await runTest('プロンプトテンプレート', testPromptTemplates);
  
  // 5. ウェブクローリング
  console.log(colors.blue + '\n=== クローリング機能テスト ===' + colors.reset);
  await runTest('ウェブクローリング', testWebCrawling);
  
  // 6. エクスポート機能
  console.log(colors.blue + '\n=== エクスポート機能テスト ===' + colors.reset);
  await runTest('コースエクスポート', () => testExportCourse(courseId));
  
  // 7. 共有機能
  console.log(colors.blue + '\n=== 共有機能テスト ===' + colors.reset);
  await runTest('コース共有', () => testCourseSharing(courseId));
  
  // 8. 進捗管理
  console.log(colors.blue + '\n=== 進捗管理テスト ===' + colors.reset);
  await runTest('進捗トラッキング', () => testProgressTracking(courseId));
  
  // テストレポート
  console.log(colors.blue + '\n=== テスト結果サマリー ===' + colors.reset);
  console.log(`総テスト数: ${testReport.total}`);
  console.log(`${colors.green}成功: ${testReport.passed}${colors.reset}`);
  console.log(`${colors.red}失敗: ${testReport.failed}${colors.reset}`);
  
  if (testReport.errors.length > 0) {
    console.log(colors.red + '\n失敗したテスト:' + colors.reset);
    testReport.errors.forEach(err => {
      console.log(`  - ${err.test}: ${err.error}`);
    });
  }
  
  // 成功率
  const successRate = (testReport.passed / testReport.total * 100).toFixed(1);
  console.log(`\n成功率: ${successRate}%`);
  
  // 終了コード
  process.exit(testReport.failed > 0 ? 1 : 0);
}

// エラーハンドリング
process.on('unhandledRejection', (error) => {
  console.error(colors.red + 'Unhandled rejection:' + colors.reset, error);
  process.exit(1);
});

// テスト実行
runAllTests().catch(error => {
  console.error(colors.red + 'Test execution failed:' + colors.reset, error);
  process.exit(1);
});