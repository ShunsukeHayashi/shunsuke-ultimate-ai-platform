# Test & Deploy Command

テスト実行とデプロイメントを統合管理するコマンドです。CI/CDパイプラインとの連携も含まれます。

## 実行内容

1. 各種テストの実行と結果分析
2. デプロイメント環境の準備
3. ビルド・パッケージング
4. デプロイメント実行
5. 動作確認とロールバック対応

## 使用方法

```
/test-deploy [action] [environment] [options]
```

## テスト関連アクション

### 1. 単体テスト (unit)
```
/test-deploy unit [--coverage] [--verbose] [--watch]
```
- 単体テストスイート実行
- コードカバレッジ計測
- テスト結果の詳細表示
- ファイル変更監視モード

### 2. 統合テスト (integration)
```
/test-deploy integration [--services] [--database]
```
- 外部サービス連携テスト
- データベース連携テスト
- API統合テスト
- End-to-Endテスト

### 3. パフォーマンステスト (performance)
```
/test-deploy performance [--load] [--stress]
```
- 負荷テスト実行
- ストレステスト実行
- レスポンス時間計測
- リソース使用量監視

### 4. セキュリティテスト (security)
```
/test-deploy security [--vulnerability] [--penetration]
```
- 脆弱性スキャン
- 侵入テスト
- セキュリティ監査
- 依存関係の安全性チェック

## デプロイメント関連アクション

### 1. 環境準備 (prepare)
```
/test-deploy prepare [development|staging|production]
```
- インフラストラクチャ確認
- 環境変数設定
- データベースマイグレーション
- 依存サービス確認

### 2. ビルド (build)
```
/test-deploy build [--environment=production] [--optimize]
```
- アプリケーションビルド
- アセット最適化
- コンテナイメージ作成
- 成果物の検証

### 3. デプロイ (deploy)
```
/test-deploy deploy [environment] [--rollback-on-failure] [--canary]
```
- アプリケーションデプロイ
- カナリアリリース
- Blue-Green デプロイメント
- 自動ロールバック設定

### 4. 検証 (verify)
```
/test-deploy verify [environment] [--health-check] [--smoke-test]
```
- デプロイ後ヘルスチェック
- スモークテスト実行
- 監視システム確認
- パフォーマンス検証

## 環境別設定

### Development Environment
```yaml
development:
  database: local_postgres
  services:
    - redis:local
    - elasticsearch:local
  env_vars:
    NODE_ENV: development
    DEBUG: true
  deploy:
    type: docker-compose
    file: docker-compose.dev.yml
```

### Staging Environment  
```yaml
staging:
  database: staging_postgres
  services:
    - redis:staging
    - elasticsearch:staging
  env_vars:
    NODE_ENV: staging
    DEBUG: false
  deploy:
    type: kubernetes
    namespace: staging
    replicas: 2
```

### Production Environment
```yaml
production:
  database: production_postgres_cluster
  services:
    - redis:production_cluster
    - elasticsearch:production_cluster
  env_vars:
    NODE_ENV: production
    DEBUG: false
  deploy:
    type: kubernetes
    namespace: production
    replicas: 5
    strategy: rolling-update
```

## CI/CDパイプライン統合

### GitHub Actions連携
```yaml
name: Test and Deploy
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          /test-deploy unit --coverage
          /test-deploy integration
          /test-deploy security --vulnerability

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          /test-deploy prepare staging
          /test-deploy build --environment=staging
          /test-deploy deploy staging --canary
          /test-deploy verify staging

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: |
          /test-deploy prepare production
          /test-deploy build --environment=production --optimize
          /test-deploy deploy production --rollback-on-failure
          /test-deploy verify production --health-check
```

### GitLab CI連携
```yaml
stages:
  - test
  - build
  - deploy-staging
  - deploy-production

test:
  stage: test
  script:
    - /test-deploy unit --coverage --verbose
    - /test-deploy integration --services
    - /test-deploy performance --load
  artifacts:
    reports:
      coverage: coverage.xml
      junit: test-results.xml

build:
  stage: build
  script:
    - /test-deploy build --environment=${CI_ENVIRONMENT_NAME}
  artifacts:
    paths:
      - dist/
      - Dockerfile

deploy-staging:
  stage: deploy-staging
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - /test-deploy deploy staging --canary
    - /test-deploy verify staging --smoke-test
  only:
    - develop

deploy-production:
  stage: deploy-production
  environment:
    name: production
    url: https://example.com
  script:
    - /test-deploy deploy production --rollback-on-failure
    - /test-deploy verify production --health-check
  only:
    - main
  when: manual
```

## テスト設定例

### Jest (Node.js/TypeScript)
```json
{
  "scripts": {
    "test:unit": "jest --testPathPattern=__tests__/unit",
    "test:integration": "jest --testPathPattern=__tests__/integration",
    "test:e2e": "jest --testPathPattern=__tests__/e2e",
    "test:coverage": "jest --coverage",
    "test:watch": "jest --watch"
  },
  "jest": {
    "collectCoverageFrom": [
      "src/**/*.{ts,js}",
      "!src/**/*.d.ts"
    ],
    "coverageThreshold": {
      "global": {
        "branches": 80,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

### Pytest (Python)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=80"
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/venv/*"]
```

### Go Test
```go
//go:build test

package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
)

// Unit test configuration
var unitTestConfig = TestConfig{
    Parallel: true,
    Verbose:  true,
    Coverage: true,
    Timeout:  "30s",
}

// Integration test configuration  
var integrationTestConfig = TestConfig{
    Parallel: false,
    Verbose:  true,
    Coverage: false,
    Timeout:  "5m",
    Tags:     "integration",
}
```

## デプロイメント戦略

### 1. Rolling Update
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### 2. Blue-Green Deployment
```yaml
strategy:
  type: BlueGreen
  blueGreen:
    activeService: app-active
    previewService: app-preview
    autoPromotionEnabled: false
```

### 3. Canary Deployment
```yaml
strategy:
  type: Canary
  canary:
    steps:
    - setWeight: 10
    - pause: {duration: 1h}
    - setWeight: 50
    - pause: {duration: 30m}
    - setWeight: 100
```

## 監視とアラート

### ヘルスチェック設定
```yaml
healthCheck:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### アラート設定
```yaml
alerts:
  - name: deployment-failure
    condition: deployment_status == "failed"
    channels: ["slack", "email"]
  - name: high-error-rate
    condition: error_rate > 5%
    channels: ["pagerduty"]
  - name: performance-degradation
    condition: response_time > 2s
    channels: ["slack"]
```

## ロールバック機能

### 自動ロールバック
```bash
# デプロイメント失敗時の自動ロールバック
/test-deploy deploy production --rollback-on-failure --health-check-timeout=300s

# パフォーマンス劣化時の自動ロールバック
/test-deploy deploy production --rollback-on-performance-degradation --threshold=2s
```

### 手動ロールバック
```bash
# 直前のバージョンにロールバック
/test-deploy rollback production --to-previous

# 特定のバージョンにロールバック
/test-deploy rollback production --to-version=v1.2.3

# 特定のコミットにロールバック
/test-deploy rollback production --to-commit=abc123def
```

このコマンドは、テストからデプロイメントまでの全工程を統合管理し、高品質で安全なリリースプロセスを実現します。