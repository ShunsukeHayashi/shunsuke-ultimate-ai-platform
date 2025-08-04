# Claude Integrations

This directory contains Claude-specific integrations for the Ultimate ShunsukeModel Ecosystem.

## MCP Servers

### 1. yaml-context-mcp
YAML Context Engineering MCP Server - Extracts and organizes hierarchical context from various sources.

```bash
cd yaml-context-mcp
npm install
npm run build
npm run dev
```

### 2. shunsuke-scout-mcp
Code reconnaissance and analysis MCP server.

```bash
cd shunsuke-scout-mcp
npm install
npm run build
npm run dev
```

### 3. quality-guardian-mcp
Quality analysis and validation MCP server.

```bash
cd quality-guardian-mcp
npm install
npm run build
npm run dev
```

## Configuration

Each MCP server can be configured through:
1. Environment variables
2. Configuration files
3. Claude Desktop settings

## Development

To create a new MCP server:

```bash
npm run create:mcp-server -- <server-name>
```

This will scaffold a new MCP server with:
- TypeScript configuration
- MCP protocol implementation
- Test setup
- Documentation template

## Testing

Run tests for all MCP servers:

```bash
npm run test --workspaces
```

## Deployment

MCP servers are automatically registered with Claude Desktop when you run:

```bash
npm run claude:sync
```