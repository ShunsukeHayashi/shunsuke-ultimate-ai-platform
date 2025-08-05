/**
 * Simple API Test
 * Tests the course generation API with minimal data
 */

const axios = require('axios');

async function testSimpleGeneration() {
  console.log('🧪 Testing Simple Course Generation...\n');
  
  const testData = {
    sources: [{
      type: 'text',
      content: 'This is a test content for course generation.'
    }],
    metadata: {
      course_title: 'Test Course',
      course_description: 'A simple test course',
      specialty_field: 'testing',
      profession: 'Tester',
      avatar: 'Test Avatar',
      tone_of_voice: 'Simple'
    }
  };
  
  try {
    console.log('📤 Sending request to API...');
    console.log('Request data:', JSON.stringify(testData, null, 2));
    
    const startTime = Date.now();
    
    const response = await axios.post('http://localhost:3002/api/generate-course', testData, {
      timeout: 180000, // 3 minutes timeout
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;
    
    console.log('\n✅ Success!');
    console.log(`Duration: ${duration} seconds`);
    console.log('Response:', JSON.stringify(response.data, null, 2));
    
  } catch (error) {
    console.error('\n❌ Error occurred:');
    
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    } else if (error.request) {
      console.error('No response received');
      console.error('Request:', error.config);
    } else {
      console.error('Error:', error.message);
    }
    
    if (error.code === 'ECONNABORTED') {
      console.error('\n⏱️  Request timed out after 3 minutes');
      console.error('The API might be stuck processing the request');
    }
  }
}

// Check if API is running first
async function checkHealth() {
  try {
    const response = await axios.get('http://localhost:3002/health');
    console.log('✅ API is healthy:', response.data);
    return true;
  } catch (error) {
    console.error('❌ API is not running or not healthy');
    return false;
  }
}

// Run tests
async function main() {
  const isHealthy = await checkHealth();
  
  if (!isHealthy) {
    console.error('\n⚠️  Please start the API server first:');
    console.error('cd /Users/shunsuke/Dev/Dev_Claude/shunsuke-ultimate-ai-platform/services/course-generator');
    console.error('npm run dev');
    process.exit(1);
  }
  
  console.log('\n');
  await testSimpleGeneration();
}

main();