#!/usr/bin/env node
/**
 * Monorepo Health Check
 * Validates the health of all workspaces
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🏥 Shunsuke Platform Monorepo Health Check\n');

// Check workspace structure
const workspaceDirs = ['packages', 'apps', 'services', 'tools', 'claude-integrations'];
let healthy = true;

console.log('📁 Checking workspace structure...');
workspaceDirs.forEach(dir => {
  const exists = fs.existsSync(path.join(__dirname, '..', dir));
  console.log(`  ${exists ? '✅' : '❌'} ${dir}`);
  if (!exists) healthy = false;
});

// Check npm workspaces
console.log('\n📦 Checking npm workspaces...');
try {
  const workspaces = execSync('npm ls --workspaces --json', { encoding: 'utf8' });
  const parsed = JSON.parse(workspaces);
  console.log(`  ✅ Found ${Object.keys(parsed.dependencies || {}).length} workspaces`);
} catch (e) {
  console.log('  ❌ Error checking workspaces');
  healthy = false;
}

// Check for common issues
console.log('\n🔍 Checking for common issues...');
try {
  // Check for duplicate dependencies
  const duplicates = execSync('npm dedupe --dry-run', { encoding: 'utf8' });
  if (duplicates.includes('removed')) {
    console.log('  ⚠️  Duplicate dependencies found (run npm dedupe)');
  } else {
    console.log('  ✅ No duplicate dependencies');
  }
} catch (e) {
  console.log('  ❌ Error checking duplicates');
}

// Check TypeScript
console.log('\n📘 Checking TypeScript configuration...');
const tsConfigExists = fs.existsSync(path.join(__dirname, '..', 'tsconfig.json'));
console.log(`  ${tsConfigExists ? '✅' : '❌'} Root tsconfig.json`);

// Summary
console.log(`\n${healthy ? '✅' : '❌'} Overall Health: ${healthy ? 'GOOD' : 'NEEDS ATTENTION'}\n`);
process.exit(healthy ? 0 : 1);
