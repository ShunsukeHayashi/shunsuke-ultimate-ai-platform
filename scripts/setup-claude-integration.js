#!/usr/bin/env node
/**
 * Claude Code Integration Setup Script
 * Ultimate ShunsukeModel Ecosystem
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m'
};

const log = {
  info: (msg) => console.log(`${colors.blue}[INFO]${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}[SUCCESS]${colors.reset} ${msg}`),
  warn: (msg) => console.log(`${colors.yellow}[WARN]${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}[ERROR]${colors.reset} ${msg}`)
};

// Banner
console.log(`
${colors.bright}${colors.blue}
╔═══════════════════════════════════════════════════════════════╗
║     Claude Code Integration Setup for Shunsuke Platform       ║
╚═══════════════════════════════════════════════════════════════╝
${colors.reset}
`);

const projectRoot = path.join(__dirname, '..');

// Setup functions
function ensureDirectoryExists(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    log.info(`Created directory: ${dirPath}`);
  }
}

function createClaudeDirectories() {
  log.info('Creating Claude Code directories...');
  
  const dirs = [
    '.claude/commands',
    '.claude/agents',
    '.claude/hooks',
    'claude-integrations/yaml-context-mcp',
    'claude-integrations/shunsuke-scout-mcp',
    'claude-integrations/quality-guardian-mcp',
    'scripts',
    'packages',
    'apps',
    'services',
    'tools'
  ];
  
  dirs.forEach(dir => {
    ensureDirectoryExists(path.join(projectRoot, dir));
  });
  
  log.success('Claude directories created');
}

function copyGlobalSettings() {
  log.info('Syncing with global Claude settings...');
  
  const homeDir = process.env.HOME || process.env.USERPROFILE;
  const globalClaudeDir = path.join(homeDir, '.claude');
  
  if (fs.existsSync(globalClaudeDir)) {
    // Copy global commands if they exist
    const globalCommandsDir = path.join(globalClaudeDir, 'commands');
    if (fs.existsSync(globalCommandsDir)) {
      const commands = fs.readdirSync(globalCommandsDir);
      commands.forEach(cmd => {
        if (cmd.endsWith('.md')) {
          const content = fs.readFileSync(path.join(globalCommandsDir, cmd), 'utf8');
          // Prefix with shunsuke- if not already
          const newName = cmd.startsWith('shunsuke-') ? cmd : `shunsuke-${cmd}`;
          fs.writeFileSync(
            path.join(projectRoot, '.claude', 'commands', newName),
            content
          );
          log.info(`Imported command: ${newName}`);
        }
      });
    }
    
    log.success('Global settings synced');
  } else {
    log.warn('No global Claude settings found');
  }
}

function createValidationScript() {
  log.info('Creating validation scripts...');
  
  const validationScript = `#!/usr/bin/env node
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
    console.log(\`Skipping validation for \${ext} files\`);
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
  
  console.log(\`✓ Validation passed for \${path.basename(filePath)}\`);
  process.exit(0);
  
} catch (error) {
  console.error('Validation error:', error.message);
  process.exit(1);
}
`;

  fs.writeFileSync(
    path.join(projectRoot, 'scripts', 'validate-code-quality.js'),
    validationScript
  );
  
  // Make it executable
  fs.chmodSync(path.join(projectRoot, 'scripts', 'validate-code-quality.js'), '755');
  
  log.success('Validation scripts created');
}

function createSessionReportScript() {
  const reportScript = `#!/usr/bin/env node
/**
 * Session Report Generator
 * Generates a summary of Claude Code session activities
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const logFile = path.join(os.homedir(), '.shunsuke', 'claude-execution.log');
const reportDir = path.join(process.cwd(), 'reports');

// Ensure report directory exists
if (!fs.existsSync(reportDir)) {
  fs.mkdirSync(reportDir, { recursive: true });
}

// Generate report
const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
const reportFile = path.join(reportDir, \`session-report-\${timestamp}.md\`);

let report = \`# Claude Code Session Report
Generated: \${new Date().toISOString()}

## Session Summary
\`;

// Read execution log if exists
if (fs.existsSync(logFile)) {
  const logs = fs.readFileSync(logFile, 'utf8').split('\\n').filter(Boolean);
  const commands = logs.filter(log => log.includes('[SHUNSUKE]'));
  
  report += \`
### Commands Executed: \${commands.length}

\\\`\\\`\\\`
\${commands.slice(-10).join('\\n')}
\\\`\\\`\\\`
\`;
}

// Add git status
try {
  const gitStatus = require('child_process').execSync('git status --short', { encoding: 'utf8' });
  report += \`
### Git Changes
\\\`\\\`\\\`
\${gitStatus || 'No changes'}
\\\`\\\`\\\`
\`;
} catch (e) {
  // Ignore git errors
}

fs.writeFileSync(reportFile, report);
console.log(\`Session report generated: \${reportFile}\`);
`;

  fs.writeFileSync(
    path.join(projectRoot, 'scripts', 'generate-session-report.js'),
    reportScript
  );
  
  fs.chmodSync(path.join(projectRoot, 'scripts', 'generate-session-report.js'), '755');
  
  log.success('Session report generator created');
}

function createMonorepoHealthCheck() {
  const healthCheckScript = `#!/usr/bin/env node
/**
 * Monorepo Health Check
 * Validates the health of all workspaces
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🏥 Shunsuke Platform Monorepo Health Check\\n');

// Check workspace structure
const workspaceDirs = ['packages', 'apps', 'services', 'tools', 'claude-integrations'];
let healthy = true;

console.log('📁 Checking workspace structure...');
workspaceDirs.forEach(dir => {
  const exists = fs.existsSync(path.join(__dirname, '..', dir));
  console.log(\`  \${exists ? '✅' : '❌'} \${dir}\`);
  if (!exists) healthy = false;
});

// Check npm workspaces
console.log('\\n📦 Checking npm workspaces...');
try {
  const workspaces = execSync('npm ls --workspaces --json', { encoding: 'utf8' });
  const parsed = JSON.parse(workspaces);
  console.log(\`  ✅ Found \${Object.keys(parsed.dependencies || {}).length} workspaces\`);
} catch (e) {
  console.log('  ❌ Error checking workspaces');
  healthy = false;
}

// Check for common issues
console.log('\\n🔍 Checking for common issues...');
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
console.log('\\n📘 Checking TypeScript configuration...');
const tsConfigExists = fs.existsSync(path.join(__dirname, '..', 'tsconfig.json'));
console.log(\`  \${tsConfigExists ? '✅' : '❌'} Root tsconfig.json\`);

// Summary
console.log(\`\\n\${healthy ? '✅' : '❌'} Overall Health: \${healthy ? 'GOOD' : 'NEEDS ATTENTION'}\\n\`);
process.exit(healthy ? 0 : 1);
`;

  fs.writeFileSync(
    path.join(projectRoot, 'scripts', 'monorepo-health-check.js'),
    healthCheckScript
  );
  
  fs.chmodSync(path.join(projectRoot, 'scripts', 'monorepo-health-check.js'), '755');
  
  log.success('Monorepo health check created');
}

function updatePackageJson() {
  log.info('Updating root package.json scripts...');
  
  const packageJsonPath = path.join(projectRoot, 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  // Add additional scripts
  packageJson.scripts = {
    ...packageJson.scripts,
    'setup': 'node scripts/setup-claude-integration.js',
    'postinstall': 'npm run setup',
    'validate': 'turbo run lint typecheck test',
    'deploy': 'node deployment/scripts/deploy.sh',
    'monitor:health': 'node scripts/monorepo-health-check.js',
    'quality:report': 'turbo run test --coverage && node scripts/generate-quality-report.js',
    'logs:tail': 'tail -f logs/**/*.log'
  };
  
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  
  log.success('package.json updated');
}

function setupGitHooks() {
  log.info('Setting up git hooks...');
  
  const huskyConfig = {
    hooks: {
      'pre-commit': 'npm run validate',
      'pre-push': 'npm run test',
      'commit-msg': 'commitlint -E HUSKY_GIT_PARAMS'
    }
  };
  
  // Create .husky directory
  ensureDirectoryExists(path.join(projectRoot, '.husky'));
  
  // Create pre-commit hook
  const preCommitHook = `#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run validate
`;

  fs.writeFileSync(
    path.join(projectRoot, '.husky', 'pre-commit'),
    preCommitHook
  );
  
  fs.chmodSync(path.join(projectRoot, '.husky', 'pre-commit'), '755');
  
  log.success('Git hooks configured');
}

// Main setup flow
async function main() {
  try {
    createClaudeDirectories();
    copyGlobalSettings();
    createValidationScript();
    createSessionReportScript();
    createMonorepoHealthCheck();
    updatePackageJson();
    setupGitHooks();
    
    console.log(`
${colors.green}${colors.bright}
╔═══════════════════════════════════════════════════════════════╗
║                    Setup Complete! 🎉                         ║
╚═══════════════════════════════════════════════════════════════╝
${colors.reset}

Next steps:
1. Run: ${colors.bright}npm install${colors.reset}
2. Run: ${colors.bright}npm run monorepo:health${colors.reset}
3. Configure your Claude Desktop settings to include this project

Claude Code is now integrated with your Shunsuke Platform! 🚀
`);
    
  } catch (error) {
    log.error(`Setup failed: ${error.message}`);
    process.exit(1);
  }
}

// Run setup
main();