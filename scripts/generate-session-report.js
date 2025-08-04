#!/usr/bin/env node
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
const reportFile = path.join(reportDir, `session-report-${timestamp}.md`);

let report = `# Claude Code Session Report
Generated: ${new Date().toISOString()}

## Session Summary
`;

// Read execution log if exists
if (fs.existsSync(logFile)) {
  const logs = fs.readFileSync(logFile, 'utf8').split('\n').filter(Boolean);
  const commands = logs.filter(log => log.includes('[SHUNSUKE]'));
  
  report += `
### Commands Executed: ${commands.length}

\`\`\`
${commands.slice(-10).join('\n')}
\`\`\`
`;
}

// Add git status
try {
  const gitStatus = require('child_process').execSync('git status --short', { encoding: 'utf8' });
  report += `
### Git Changes
\`\`\`
${gitStatus || 'No changes'}
\`\`\`
`;
} catch (e) {
  // Ignore git errors
}

fs.writeFileSync(reportFile, report);
console.log(`Session report generated: ${reportFile}`);
