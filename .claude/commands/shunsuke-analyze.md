---
description: Analyze code quality across all workspaces in the Shunsuke Platform monorepo
---

# ShunsukeModel Quality Analysis

Execute comprehensive quality analysis across all workspaces:

```bash
# Run quality analysis
npm run monorepo:health

# Analyze specific workspace
npm run analyze --workspace=@shunsuke/command-tower

# Generate quality report
npm run quality:report

# Check test coverage
npm run test:coverage

# Run security audit
npm audit --workspaces
```

The analysis includes:
- Code quality metrics
- Test coverage
- Dependency health
- Security vulnerabilities
- Performance benchmarks