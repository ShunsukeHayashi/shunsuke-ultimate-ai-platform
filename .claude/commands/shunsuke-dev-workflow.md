# Development Workflow Command

開発ワークフローを統合管理するコマンドです。Git操作、コード品質チェック、自動化タスクを効率化します。

## 実行内容

1. Git状態の確認と操作
2. コード品質チェック（Lint/Format）
3. テスト実行
4. ビルド・デプロイ準備
5. 自動コミット・プッシュ

## 使用方法

```
/dev-workflow [action] [options]
```

## アクション一覧

### 1. 状態確認 (status)
```
/dev-workflow status
```
- Git status確認
- 変更ファイル一覧
- ブランチ情報
- 未コミット変更の概要

### 2. コード品質チェック (lint)
```
/dev-workflow lint [--fix]
```
- Linterによるコード検査
- Formatterによる自動整形
- 型チェック（TypeScript/Python等）
- --fixオプションで自動修正

### 3. テスト実行 (test)
```
/dev-workflow test [--coverage] [--watch]
```
- 単体テスト実行
- 統合テスト実行
- カバレッジレポート生成
- --watchオプションでファイル監視

### 4. ビルド (build)
```
/dev-workflow build [--production]
```
- アプリケーションビルド
- 依存関係の最適化
- 本番用設定適用

### 5. 自動コミット (commit)
```
/dev-workflow commit [--message="description"]
```
- ステージング状況確認
- 自動コミットメッセージ生成
- GPG署名適用
- プッシュ実行

### 6. ブランチ管理 (branch)
```
/dev-workflow branch [create|switch|merge] [branch-name]
```
- ブランチ作成・切り替え
- マージ操作
- 競合解決支援

## プロジェクトタイプ別の設定

### Node.js/TypeScript
```json
{
  "scripts": {
    "lint": "eslint . --ext .ts,.js --fix",
    "format": "prettier --write .",
    "test": "jest --coverage",
    "build": "tsc && webpack --mode production",
    "type-check": "tsc --noEmit"
  },
  "dev-workflow": {
    "lint-command": "npm run lint",
    "test-command": "npm test",
    "build-command": "npm run build",
    "format-command": "npm run format"
  }
}
```

### Python
```toml
[tool.poetry.scripts]
lint = "flake8 && mypy ."
format = "black . && isort ."
test = "pytest --cov=src"
build = "poetry build"

[tool.dev-workflow]
lint-command = "poetry run lint"
test-command = "poetry run test"
build-command = "poetry run build"
format-command = "poetry run format"
```

### Go
```go
//go:build dev-workflow

// dev-workflow設定
var config = DevWorkflowConfig{
    LintCommand:   "golangci-lint run",
    TestCommand:   "go test ./... -v -cover",
    BuildCommand:  "go build ./...",
    FormatCommand: "go fmt ./...",
}
```

### Rust
```toml
[package.metadata.dev-workflow]
lint-command = "cargo clippy -- -D warnings"
test-command = "cargo test"
build-command = "cargo build --release"
format-command = "cargo fmt"
```

## 自動化フロー例

### 1. プリコミットフロー
```bash
/dev-workflow lint --fix
/dev-workflow test
/dev-workflow commit --message="feat: new feature implementation"
```

### 2. CI/CD準備フロー
```bash
/dev-workflow status
/dev-workflow lint
/dev-workflow test --coverage
/dev-workflow build --production
```

### 3. ホットフィックスフロー
```bash
/dev-workflow branch create hotfix/urgent-fix
# 修正作業
/dev-workflow lint --fix
/dev-workflow test
/dev-workflow commit --message="hotfix: critical bug fix"
/dev-workflow branch merge main
```

## Git統合機能

### コミットメッセージの自動生成
変更内容を解析して適切なコミットメッセージを提案：
- `feat:` 新機能追加
- `fix:` バグ修正
- `docs:` ドキュメント変更
- `style:` コードスタイル変更
- `refactor:` リファクタリング
- `test:` テスト追加・修正
- `chore:` その他の変更

### ブランチ命名規則
- `feature/機能名`
- `bugfix/バグ修正内容`
- `hotfix/緊急修正内容`
- `release/バージョン番号`

## 品質チェック統合

### 1. コードスタイル
- **JavaScript/TypeScript**: ESLint + Prettier
- **Python**: Black + isort + flake8
- **Go**: gofmt + golangci-lint
- **Rust**: rustfmt + clippy

### 2. 型チェック
- **TypeScript**: tsc --noEmit
- **Python**: mypy
- **Go**: 組み込み型システム
- **Rust**: 組み込み型システム

### 3. セキュリティチェック
- **Node.js**: npm audit
- **Python**: safety, bandit
- **Go**: gosec
- **Rust**: cargo audit

## 統計・レポート機能

### コード変更統計
```
変更統計:
- 追加: 150行
- 削除: 75行
- 変更ファイル: 12個
- テストカバレッジ: 85% (+3%)
```

### パフォーマンス指標
```
ビルド時間: 2.3秒 (-0.5秒)
テスト実行時間: 15.2秒 (+1.2秒)
Lintエラー: 0個 (-5個)
```

## 設定ファイル例

### .dev-workflow.json
```json
{
  "hooks": {
    "pre-commit": ["lint --fix", "test"],
    "pre-push": ["lint", "test --coverage", "build"]
  },
  "commit": {
    "auto-stage": true,
    "generate-message": true,
    "sign-commits": true
  },
  "notifications": {
    "success": true,
    "failure": true,
    "slack-webhook": "https://hooks.slack.com/..."
  }
}
```

このコマンドは、開発プロセス全体を統合し、品質の高いコード開発とスムーズなチーム協業を支援します。