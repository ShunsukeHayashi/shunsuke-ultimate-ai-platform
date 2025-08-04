---
description: Monitor Shunsuke Platform health and performance metrics
---

# ShunsukeModel Monitoring

Check system health and metrics:

```bash
# Overall health check
npm run monitor:health

# Service-specific monitoring
npm run monitor:service -- command-tower

# Performance metrics
npm run monitor:performance

# Resource usage
npm run monitor:resources

# Real-time logs
npm run logs:tail -- --service=all

# Generate health report
npm run monitor:report -- --format=json
```

Monitoring includes:
- Service availability
- Response times
- Error rates
- Resource utilization
- Active connections
- Queue lengths
- Cache hit rates