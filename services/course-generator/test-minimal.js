/**
 * Minimal API Test
 * Tests course generation with lesson script generation disabled
 */

const axios = require('axios');

async function testMinimalGeneration() {
  console.log('🧪 Testing Minimal Course Generation...\n');
  
  const testData = {
    sources: [{
      type: 'text',
      content: 'TypeScript basics'
    }],
    metadata: {
      course_title: 'Minimal Test',
      course_description: 'Minimal test',
      specialty_field: 'test',
      profession: 'Test',
      avatar: 'Test',
      tone_of_voice: 'Test'
    },
    options: {
      includeAudio: false,
      skipScriptGeneration: true // Skip script generation for faster test
    }
  };
  
  try {
    console.log('📤 Sending request...');
    
    const response = await axios.post('http://localhost:3002/api/generate-course', testData, {
      timeout: 30000 // 30 seconds
    });
    
    console.log('\n✅ Success!');
    console.log('Modules generated:', response.data.course.modules.length);
    console.log('Response keys:', Object.keys(response.data));
    
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    if (error.response) {
      console.error('Response:', error.response.data);
    }
  }
}

testMinimalGeneration();