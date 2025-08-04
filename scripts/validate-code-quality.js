#!/usr/bin/env node
/**
 * Code Quality Validation Script
 * Validates code before Claude Code writes
 */

const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];

if (!filePath) {
  console.log('No file path provided');
  process.exit(0);
}

// Basic validation
try {
  const ext = path.extname(filePath);
  const validExtensions = ['.ts', '.tsx', '.js', '.jsx', '.json', '.md'];
  
  if (!validExtensions.includes(ext)) {
    console.log(`Skipping validation for ${ext} files`);
    process.exit(0);
  }
  
  // Check if file is in node_modules
  if (filePath.includes('node_modules')) {
    console.error('ERROR: Cannot modify files in node_modules');
    process.exit(1);
  }
  
  // Check if file is in .git
  if (filePath.includes('.git/')) {
    console.error('ERROR: Cannot modify git internal files');
    process.exit(1);
  }
  
  console.log(`✓ Validation passed for ${path.basename(filePath)}`);
  process.exit(0);
  
} catch (error) {
  console.error('Validation error:', error.message);
  process.exit(1);
}
