/**
 * Integration Test Script
 * Tests the Course Generator UI and API integration
 */

const axios = require('axios');

const API_BASE = 'http://localhost:3002';
const UI_BASE = 'http://localhost:3003';

// Color codes for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testHealthCheck() {
  log('\n📋 Testing API Health Check...', 'cyan');
  try {
    const response = await axios.get(`${API_BASE}/health`);
    if (response.data.status === 'healthy') {
      log('✅ API is healthy', 'green');
      log(`   Version: ${response.data.version}`, 'green');
      return true;
    }
  } catch (error) {
    log('❌ API health check failed', 'red');
    console.error(error.message);
    return false;
  }
}

async function testUIAccess() {
  log('\n📋 Testing UI Access...', 'cyan');
  try {
    const response = await axios.get(UI_BASE);
    if (response.status === 200) {
      log('✅ UI is accessible', 'green');
      return true;
    }
  } catch (error) {
    log('❌ UI access failed', 'red');
    console.error(error.message);
    return false;
  }
}

async function testCourseGeneration() {
  log('\n📋 Testing Course Generation...', 'cyan');
  
  const testData = {
    sources: [{
      type: 'text',
      content: 'TypeScriptは、JavaScriptに静的型付けを追加したプログラミング言語です。マイクロソフトによって開発され、大規模なアプリケーション開発に適しています。'
    }],
    metadata: {
      course_title: 'TypeScript入門講座',
      course_description: 'TypeScriptの基礎を学ぶ入門コース',
      specialty_field: 'web-development',
      profession: 'シニアエンジニア',
      avatar: '経験豊富な技術メンター',
      tone_of_voice: 'フレンドリーで分かりやすく、技術的な内容も噛み砕いて説明する',
      target_audience: '初級〜中級のWeb開発者',
      difficulty_level: 'beginner'
    },
    options: {
      includeAudio: false,
      language: 'ja'
    }
  };

  try {
    log('📤 Sending course generation request...', 'yellow');
    const response = await axios.post(`${API_BASE}/api/generate-course`, testData);
    
    if (response.data.success) {
      log('✅ Course generated successfully!', 'green');
      log(`   Title: ${response.data.course.metadata.course_title}`, 'green');
      log(`   Modules: ${response.data.course.modules.length}`, 'green');
      
      let totalLessons = 0;
      response.data.course.modules.forEach(module => {
        module.sections.forEach(section => {
          totalLessons += section.lessons.length;
        });
      });
      log(`   Total Lessons: ${totalLessons}`, 'green');
      
      return response.data.course;
    }
  } catch (error) {
    log('❌ Course generation failed', 'red');
    console.error(error.response?.data || error.message);
    return null;
  }
}

async function testSSEConnection() {
  log('\n📋 Testing SSE Connection...', 'cyan');
  
  const testData = {
    sources: [{
      type: 'text',
      content: 'React Hooksの基本的な使い方について説明します。'
    }],
    metadata: {
      course_title: 'React Hooks基礎',
      course_description: 'React Hooksの基本を学ぶ',
      specialty_field: 'web-development',
      profession: 'フロントエンドエンジニア',
      avatar: 'React専門家',
      tone_of_voice: '実践的でわかりやすい'
    }
  };

  const params = new URLSearchParams({
    data: JSON.stringify(testData)
  });

  return new Promise((resolve) => {
    log('📡 Establishing SSE connection...', 'yellow');
    
    const EventSource = require('eventsource');
    const eventSource = new EventSource(`${API_BASE}/api/generate-course-stream?${params}`);
    
    let progressUpdates = 0;
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.progress) {
        progressUpdates++;
        log(`   Progress: ${data.progress.phase} - ${data.progress.message}`, 'blue');
      }
      
      if (data.success) {
        log('✅ SSE stream completed successfully', 'green');
        log(`   Progress updates received: ${progressUpdates}`, 'green');
        eventSource.close();
        resolve(true);
      }
      
      if (data.error) {
        log('❌ SSE stream error', 'red');
        console.error(data.error);
        eventSource.close();
        resolve(false);
      }
    };
    
    eventSource.onerror = (error) => {
      log('❌ SSE connection error', 'red');
      console.error(error);
      eventSource.close();
      resolve(false);
    };
    
    // Timeout after 60 seconds
    setTimeout(() => {
      eventSource.close();
      log('⚠️  SSE test timeout after 60 seconds', 'yellow');
      resolve(false);
    }, 60000);
  });
}

async function testExportFunctionality(course) {
  log('\n📋 Testing Export Functionality...', 'cyan');
  
  if (!course) {
    log('⚠️  No course available for export test', 'yellow');
    return false;
  }

  const exportData = {
    course: course,
    scripts: {},
    audioFiles: {},
    exportOptions: {
      format: 'json',
      includeScripts: true,
      includeMetadata: true
    }
  };

  try {
    log('📤 Testing JSON export...', 'yellow');
    const response = await axios.post(`${API_BASE}/api/export-course`, exportData);
    
    if (response.data.success) {
      log('✅ Export successful', 'green');
      log(`   Format: ${response.data.export.format}`, 'green');
      log(`   File path: ${response.data.export.filePath}`, 'green');
      return true;
    }
  } catch (error) {
    log('❌ Export failed', 'red');
    console.error(error.response?.data || error.message);
    return false;
  }
}

async function runAllTests() {
  log('\n🚀 Starting Integration Tests for Course Generator', 'cyan');
  log('=' .repeat(50), 'cyan');
  
  let passedTests = 0;
  let totalTests = 5;
  
  // Test 1: API Health Check
  if (await testHealthCheck()) passedTests++;
  
  // Test 2: UI Access
  if (await testUIAccess()) passedTests++;
  
  // Test 3: Course Generation
  const generatedCourse = await testCourseGeneration();
  if (generatedCourse) passedTests++;
  
  // Test 4: SSE Connection
  if (await testSSEConnection()) passedTests++;
  
  // Test 5: Export Functionality
  if (await testExportFunctionality(generatedCourse)) passedTests++;
  
  // Summary
  log('\n' + '=' .repeat(50), 'cyan');
  log('📊 Test Summary', 'cyan');
  log(`   Total Tests: ${totalTests}`, 'cyan');
  log(`   Passed: ${passedTests}`, passedTests === totalTests ? 'green' : 'yellow');
  log(`   Failed: ${totalTests - passedTests}`, totalTests - passedTests > 0 ? 'red' : 'green');
  
  if (passedTests === totalTests) {
    log('\n✅ All tests passed! The integration is working correctly.', 'green');
  } else {
    log('\n⚠️  Some tests failed. Please check the logs above.', 'yellow');
  }
  
  process.exit(passedTests === totalTests ? 0 : 1);
}

// Run tests
runAllTests().catch(error => {
  log('\n❌ Test runner error:', 'red');
  console.error(error);
  process.exit(1);
});