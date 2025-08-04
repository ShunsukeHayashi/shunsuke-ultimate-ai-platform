# CLAUDE.md - Ultimate ShunsukeModel Ecosystem

This file provides guidance to Claude Code when working with the Ultimate ShunsukeModel Ecosystem monorepo.

## Repository Structure

This is a monorepo containing the complete ShunsukeModel AI development platform:

```
shunsuke-ultimate-ai-platform/
├── apps/                      # User-facing applications
│   └── command-center/       # Central command interface
├── services/                  # Core microservices
│   ├── command-tower/        # Central orchestration
│   ├── agent-coordinator/    # Agent management
│   └── quality-guardian/     # Quality assurance
├── packages/                  # Shared libraries
│   ├── core/                # Core utilities
│   ├── ui/                  # UI components
│   ├── eslint-config/       # ESLint configuration
│   └── typescript-config/   # TypeScript configuration
├── tools/                     # Development tools
│   ├── quality-analyzer/    # Quality analysis
│   ├── doc-synthesizer/     # Documentation generation
│   └── performance-suite/   # Performance tools
├── claude-integrations/       # Claude-specific integrations
│   ├── yaml-context-mcp/    # Context extraction MCP
│   ├── shunsuke-scout-mcp/  # Code analysis MCP
│   └── quality-guardian-mcp/ # Quality validation MCP
└── deployment/               # Deployment configurations
    ├── docker-compose.yml   # Docker Compose setup
    ├── kubernetes/          # K8s manifests
    └── terraform/           # Infrastructure as code
```

## Development Commands

### Monorepo Management
```bash
# Install all dependencies
npm install

# Run development servers for all services
npm run dev

# Build all packages
npm run build

# Run tests across all workspaces
npm run test

# Check monorepo health
npm run monorepo:health
```

### Claude Integration
```bash
# Setup Claude integration
npm run claude:setup

# Sync Claude configuration
npm run claude:sync

# Validate code quality
npm run validate
```

### Service-Specific Commands
```bash
# Work with specific workspace
npm run dev --workspace=@shunsuke/command-tower
npm run test --workspace=@shunsuke/quality-analyzer
npm run build --workspace=@shunsuke/yaml-context-mcp
```

## Key Technologies

- **Monorepo Tool**: Turborepo
- **Package Manager**: npm workspaces
- **Languages**: TypeScript, Python
- **Frameworks**: Next.js (apps), Express (services)
- **Testing**: Jest, Pytest
- **Infrastructure**: Docker, Kubernetes, Terraform
- **CI/CD**: GitHub Actions
- **Quality**: ESLint, Prettier, TypeScript strict mode

## Development Workflow

1. **Feature Development**
   - Create feature branch from `main`
   - Use conventional commits
   - Write tests for new features
   - Ensure all quality checks pass

2. **Quality Standards**
   - Minimum 80% test coverage
   - All TypeScript strict checks must pass
   - Follow ESLint rules
   - Format with Prettier

3. **Claude Code Integration**
   - Custom slash commands available: `/shunsuke-analyze`, `/shunsuke-deploy`, `/shunsuke-monitor`
   - Hooks validate code quality before writes
   - MCP servers provide specialized functionality

## Architecture Principles

1. **Modular Design**: Each service has a single responsibility
2. **Shared Libraries**: Common functionality in packages/
3. **Type Safety**: TypeScript everywhere with strict mode
4. **Quality First**: Automated quality checks at every level
5. **Claude Integration**: Deep integration with Claude Code ecosystem

## Important Files

- `turbo.json` - Turborepo pipeline configuration
- `claude.config.json` - Claude Code integration settings
- `.claude/` - Claude-specific configurations
- `package.json` - Root package with workspace configuration

## Deployment

```bash
# Deploy to staging
npm run deploy -- staging

# Deploy to production
npm run deploy -- production

# Monitor deployment
npm run monitor:health
```

## Testing Strategy

- Unit tests for all packages
- Integration tests for services
- E2E tests for critical workflows
- Performance benchmarks
- Security scanning

## Common Tasks

### Adding a New Service
```bash
# Create new service directory
mkdir -p services/new-service

# Copy template
cp -r templates/service/* services/new-service/

# Update workspace
npm install
```

### Creating an MCP Server
```bash
# Use the MCP template
cp -r templates/mcp-server/* claude-integrations/new-mcp/

# Install dependencies
npm install --workspace=@shunsuke/new-mcp
```

### Running Quality Checks
```bash
# Full validation
npm run validate

# Specific checks
npm run lint
npm run typecheck
npm run test
```

## Troubleshooting

1. **Dependency Issues**: Run `npm dedupe` to remove duplicates
2. **Build Failures**: Check `turbo.json` pipeline dependencies
3. **Test Failures**: Run tests in isolation with `--workspace`
4. **Claude Integration**: Ensure `claude:sync` has been run

## Best Practices

1. Always run `npm run monorepo:health` before major changes
2. Use workspace commands for service-specific operations
3. Keep dependencies in the appropriate workspace
4. Follow the established patterns in existing code
5. Document new features and APIs

Remember: This is a production-grade platform. Quality and reliability are paramount.