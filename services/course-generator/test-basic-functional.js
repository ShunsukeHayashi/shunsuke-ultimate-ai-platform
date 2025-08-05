/**
 * Course Generator 基本機能テスト
 * UIとAPIの基本的な動作確認
 */

const axios = require('axios');

const API_URL = 'http://localhost:3002';
const UI_URL = 'http://localhost:3003';

// カラー出力
const log = {
  success: (msg) => console.log(`\x1b[32m✅ ${msg}\x1b[0m`),
  error: (msg) => console.log(`\x1b[31m❌ ${msg}\x1b[0m`),
  info: (msg) => console.log(`\x1b[34mℹ️  ${msg}\x1b[0m`),
  warning: (msg) => console.log(`\x1b[33m⚠️  ${msg}\x1b[0m`)
};

// 基本的なテスト
async function runBasicTests() {
  console.log('\n🧪 Course Generator 基本機能テスト\n');
  
  let testResults = {
    total: 0,
    passed: 0,
    failed: 0
  };
  
  // 1. APIサーバー接続テスト
  console.log('=== APIサーバー接続テスト ===');
  testResults.total++;
  try {
    const apiResponse = await axios.get(API_URL, { timeout: 5000 });
    if (apiResponse.status === 200) {
      log.success('APIサーバー接続: OK');
      log.info(`レスポンス: ${apiResponse.data.toString().substring(0, 100)}...`);
      testResults.passed++;
    }
  } catch (error) {
    log.error(`APIサーバー接続: 失敗 (${error.message})`);
    testResults.failed++;
  }
  
  // 2. UIサーバー接続テスト
  console.log('\n=== UIサーバー接続テスト ===');
  testResults.total++;
  try {
    const uiResponse = await axios.get(UI_URL, { timeout: 5000 });
    if (uiResponse.status === 200) {
      log.success('UIサーバー接続: OK');
      
      // HTMLコンテンツの確認
      const html = uiResponse.data;
      if (html.includes('Course Generator')) {
        log.success('Course Generatorタイトル: 確認');
      }
      if (html.includes('Ultimate AI Platform')) {
        log.success('プラットフォーム名: 確認');
      }
      testResults.passed++;
    }
  } catch (error) {
    log.error(`UIサーバー接続: 失敗 (${error.message})`);
    testResults.failed++;
  }
  
  // 3. 静的リソースのテスト
  console.log('\n=== 静的リソーステスト ===');
  const resources = [
    { path: '/assets/css/style.css', type: 'CSS' },
    { path: '/assets/js/app.js', type: 'JavaScript' }
  ];
  
  for (const resource of resources) {
    testResults.total++;
    try {
      const response = await axios.get(API_URL + resource.path, { timeout: 5000 });
      if (response.status === 200) {
        log.success(`${resource.type}ファイル: アクセス可能`);
        testResults.passed++;
      }
    } catch (error) {
      log.warning(`${resource.type}ファイル: ${error.response?.status || 'エラー'}`);
      testResults.failed++;
    }
  }
  
  // 4. メインページ要素の確認
  console.log('\n=== ページ要素確認 ===');
  testResults.total++;
  try {
    const pageResponse = await axios.get(API_URL);
    const pageContent = pageResponse.data;
    
    const expectedElements = [
      { text: 'ホーム', name: 'ホームリンク' },
      { text: 'コース', name: 'コースリンク' },
      { text: 'テンプレート', name: 'テンプレートリンク' },
      { text: 'ログイン', name: 'ログインボタン' },
      { text: '新規登録', name: '新規登録ボタン' },
      { text: 'AI搭載のコース生成プラットフォーム', name: 'メインタイトル' },
      { text: 'Gemini AI', name: 'AI機能説明' }
    ];
    
    let elementsFound = 0;
    expectedElements.forEach(element => {
      if (pageContent.includes(element.text)) {
        log.info(`${element.name}: ✓`);
        elementsFound++;
      } else {
        log.warning(`${element.name}: ✗`);
      }
    });
    
    if (elementsFound >= expectedElements.length * 0.7) {
      log.success(`ページ要素: ${elementsFound}/${expectedElements.length} 確認`);
      testResults.passed++;
    } else {
      log.error(`ページ要素: ${elementsFound}/${expectedElements.length} のみ`);
      testResults.failed++;
    }
  } catch (error) {
    log.error(`ページ要素確認: 失敗 (${error.message})`);
    testResults.failed++;
  }
  
  // 5. フォーム要素の確認
  console.log('\n=== フォーム要素テスト ===');
  testResults.total++;
  try {
    const formResponse = await axios.get(API_URL);
    const formContent = formResponse.data;
    
    const formElements = [
      'loginForm',
      'registerForm',
      'type="email"',
      'type="password"',
      'type="submit"'
    ];
    
    let formsFound = 0;
    formElements.forEach(element => {
      if (formContent.includes(element)) {
        formsFound++;
      }
    });
    
    log.info(`フォーム要素: ${formsFound}/${formElements.length} 検出`);
    if (formsFound >= 3) {
      log.success('フォーム構造: 基本要素確認');
      testResults.passed++;
    } else {
      log.error('フォーム構造: 不完全');
      testResults.failed++;
    }
  } catch (error) {
    log.error(`フォーム要素テスト: 失敗 (${error.message})`);
    testResults.failed++;
  }
  
  // 6. JavaScript機能の確認
  console.log('\n=== JavaScript機能確認 ===');
  testResults.total++;
  try {
    const jsResponse = await axios.get(API_URL);
    const jsContent = jsResponse.data;
    
    const jsFunctions = [
      'showLogin',
      'showRegister',
      'handleLogin',
      'handleRegister',
      'logout'
    ];
    
    let functionsFound = 0;
    jsFunctions.forEach(func => {
      if (jsContent.includes(func)) {
        functionsFound++;
      }
    });
    
    log.info(`JavaScript関数: ${functionsFound}/${jsFunctions.length} 検出`);
    if (functionsFound >= 3) {
      log.success('JavaScript機能: 実装確認');
      testResults.passed++;
    } else {
      log.warning('JavaScript機能: 一部のみ検出');
      testResults.failed++;
    }
  } catch (error) {
    log.error(`JavaScript機能確認: 失敗 (${error.message})`);
    testResults.failed++;
  }
  
  // テスト結果サマリー
  console.log('\n=== テスト結果サマリー ===');
  console.log(`総テスト数: ${testResults.total}`);
  console.log(`\x1b[32m成功: ${testResults.passed}\x1b[0m`);
  console.log(`\x1b[31m失敗: ${testResults.failed}\x1b[0m`);
  
  const successRate = (testResults.passed / testResults.total * 100).toFixed(1);
  console.log(`\n成功率: ${successRate}%`);
  
  if (successRate >= 70) {
    log.success('基本機能テスト: 合格 ✨');
  } else if (successRate >= 50) {
    log.warning('基本機能テスト: 要改善');
  } else {
    log.error('基本機能テスト: 不合格');
  }
  
  // パフォーマンス情報
  console.log('\n=== パフォーマンス情報 ===');
  const startTime = Date.now();
  try {
    await axios.get(API_URL);
    const loadTime = Date.now() - startTime;
    log.info(`ページロード時間: ${loadTime}ms`);
    
    if (loadTime < 500) {
      log.success('パフォーマンス: 優秀');
    } else if (loadTime < 1000) {
      log.warning('パフォーマンス: 普通');
    } else {
      log.error('パフォーマンス: 要改善');
    }
  } catch (error) {
    log.error('パフォーマンス測定: 失敗');
  }
}

// テスト実行
runBasicTests().catch(error => {
  console.error('\n\x1b[31mテスト実行エラー:\x1b[0m', error.message);
  process.exit(1);
});