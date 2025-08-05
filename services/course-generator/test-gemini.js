/**
 * Gemini API Test Script
 * Tests direct Gemini API connectivity
 */

const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

async function testGeminiAPI() {
  console.log('🧪 Testing Gemini API Connection...\n');
  
  const apiKey = process.env.GEMINI_API_KEY;
  console.log('API Key:', apiKey ? `${apiKey.substring(0, 10)}...` : 'NOT SET');
  
  if (!apiKey) {
    console.error('❌ GEMINI_API_KEY is not set in environment');
    return;
  }
  
  try {
    console.log('🔄 Initializing Gemini AI...');
    const genAI = new GoogleGenerativeAI(apiKey);
    
    console.log('🔄 Getting model...');
    const model = genAI.getGenerativeModel({ 
      model: 'gemini-1.5-pro',
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 100,
      }
    });
    
    console.log('🔄 Generating content...');
    const prompt = 'Write a one-sentence summary about TypeScript.';
    
    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();
    
    console.log('\n✅ Gemini API is working!');
    console.log('Response:', text);
    
  } catch (error) {
    console.error('\n❌ Gemini API Error:');
    console.error('Type:', error.constructor.name);
    console.error('Message:', error.message);
    
    if (error.response) {
      console.error('Response Status:', error.response.status);
      console.error('Response Data:', error.response.data);
    }
    
    if (error.message.includes('API key')) {
      console.error('\n💡 Tip: Check if your API key is valid and has the necessary permissions');
    }
  }
}

// Run test
testGeminiAPI();