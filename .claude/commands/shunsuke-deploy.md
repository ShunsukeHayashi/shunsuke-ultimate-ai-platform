---
description: Deploy Shunsuke Platform services to specified environment
---

# ShunsukeModel Deployment

Deploy services with specified configuration:

```bash
# Deploy to staging
npm run deploy -- staging

# Deploy to production with dry run
npm run deploy -- production --dry-run

# Deploy specific service
npm run deploy -- staging --service=command-tower

# Full deployment with monitoring
npm run deploy -- production --with-monitoring

# Rollback deployment
npm run deploy:rollback -- production --version=1.0.0
```

Available deployment targets:
- `staging` - Staging environment
- `production` - Production environment
- `dev` - Development environment

Options:
- `--dry-run` - Simulate deployment without making changes
- `--service=<name>` - Deploy specific service only
- `--with-monitoring` - Include monitoring stack
- `--skip-tests` - Skip test execution (not recommended)