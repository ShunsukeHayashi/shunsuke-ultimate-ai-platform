#!/usr/bin/env node
/**
 * Claude Configuration Sync Script
 * Synchronizes Claude settings between global and project configurations
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// Colors
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m'
};

const log = {
  info: (msg) => console.log(`${colors.blue}[SYNC]${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}[OK]${colors.reset} ${msg}`),
  warn: (msg) => console.log(`${colors.yellow}[WARN]${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}[ERROR]${colors.reset} ${msg}`)
};

const projectRoot = path.join(__dirname, '..');
const homeDir = os.homedir();
const globalClaudeDir = path.join(homeDir, '.claude');
const projectClaudeDir = path.join(projectRoot, '.claude');

// Sync functions
function syncSettings() {
  log.info('Syncing Claude settings...');
  
  const projectSettings = path.join(projectClaudeDir, 'settings.json');
  const globalSettings = path.join(globalClaudeDir, 'settings.json');
  
  if (fs.existsSync(projectSettings)) {
    // Read project settings
    const settings = JSON.parse(fs.readFileSync(projectSettings, 'utf8'));
    
    // Add project-specific MCP servers
    if (settings.mcpServers) {
      log.info(`Found ${Object.keys(settings.mcpServers).length} MCP servers`);
      
      // Update global Claude Desktop configuration
      updateClaudeDesktopConfig(settings.mcpServers);
    }
    
    log.success('Settings synchronized');
  } else {
    log.warn('No project settings found');
  }
}

function updateClaudeDesktopConfig(mcpServers) {
  const claudeDesktopConfig = path.join(
    homeDir,
    'Library',
    'Application Support',
    'Claude',
    'claude_desktop_config.json'
  );
  
  if (!fs.existsSync(claudeDesktopConfig)) {
    log.warn('Claude Desktop config not found');
    return;
  }
  
  try {
    const config = JSON.parse(fs.readFileSync(claudeDesktopConfig, 'utf8'));
    
    // Merge MCP servers
    config.mcpServers = config.mcpServers || {};
    
    Object.entries(mcpServers).forEach(([name, server]) => {
      const fullName = `shunsuke-${name}`;
      config.mcpServers[fullName] = {
        ...server,
        // Update paths to be absolute
        command: server.command,
        args: server.args.map(arg => 
          arg.startsWith('/') ? arg : path.join(projectRoot, arg)
        )
      };
      log.info(`Updated MCP server: ${fullName}`);
    });
    
    // Write back
    fs.writeFileSync(claudeDesktopConfig, JSON.stringify(config, null, 2));
    log.success('Claude Desktop config updated');
    
  } catch (error) {
    log.error(`Failed to update Claude Desktop config: ${error.message}`);
  }
}

function syncCommands() {
  log.info('Syncing slash commands...');
  
  const projectCommandsDir = path.join(projectClaudeDir, 'commands');
  const globalCommandsDir = path.join(globalClaudeDir, 'commands');
  
  if (!fs.existsSync(globalCommandsDir)) {
    fs.mkdirSync(globalCommandsDir, { recursive: true });
  }
  
  if (fs.existsSync(projectCommandsDir)) {
    const commands = fs.readdirSync(projectCommandsDir);
    
    commands.forEach(cmd => {
      if (cmd.endsWith('.md')) {
        const source = path.join(projectCommandsDir, cmd);
        const dest = path.join(globalCommandsDir, cmd);
        
        // Copy command to global
        fs.copyFileSync(source, dest);
        log.success(`Synced command: ${cmd}`);
      }
    });
  }
}

function syncAgents() {
  log.info('Syncing agent definitions...');
  
  const projectAgentsDir = path.join(projectClaudeDir, 'agents');
  const globalAgentsDir = path.join(globalClaudeDir, 'agents');
  
  if (!fs.existsSync(globalAgentsDir)) {
    fs.mkdirSync(globalAgentsDir, { recursive: true });
  }
  
  if (fs.existsSync(projectAgentsDir)) {
    const agents = fs.readdirSync(projectAgentsDir);
    
    agents.forEach(agent => {
      if (agent.endsWith('.md')) {
        const source = path.join(projectAgentsDir, agent);
        const dest = path.join(globalAgentsDir, agent);
        
        // Copy agent to global
        fs.copyFileSync(source, dest);
        log.success(`Synced agent: ${agent}`);
      }
    });
  }
}

function createSyncReport() {
  const report = {
    timestamp: new Date().toISOString(),
    project: 'shunsuke-ultimate-ai-platform',
    synced: {
      settings: true,
      commands: [],
      agents: [],
      mcpServers: []
    }
  };
  
  // List synced items
  const projectCommandsDir = path.join(projectClaudeDir, 'commands');
  if (fs.existsSync(projectCommandsDir)) {
    report.synced.commands = fs.readdirSync(projectCommandsDir)
      .filter(f => f.endsWith('.md'));
  }
  
  const projectAgentsDir = path.join(projectClaudeDir, 'agents');
  if (fs.existsSync(projectAgentsDir)) {
    report.synced.agents = fs.readdirSync(projectAgentsDir)
      .filter(f => f.endsWith('.md'));
  }
  
  // Save report
  const reportPath = path.join(projectRoot, '.claude-sync-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  log.success(`Sync report saved to ${reportPath}`);
}

// Main sync
function main() {
  console.log(`
${colors.blue}Claude Configuration Sync${colors.reset}
========================
`);

  try {
    syncSettings();
    syncCommands();
    syncAgents();
    createSyncReport();
    
    console.log(`
${colors.green}Sync completed successfully!${colors.reset}

Your Claude configuration has been synchronized.
Restart Claude Desktop to apply the changes.
`);
    
  } catch (error) {
    log.error(`Sync failed: ${error.message}`);
    process.exit(1);
  }
}

// Run sync
main();