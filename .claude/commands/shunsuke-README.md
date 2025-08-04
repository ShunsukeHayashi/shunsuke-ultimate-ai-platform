# Claude Code Custom Commands

Claude Code用にカスタマイズされたスラッシュコマンド集です。開発効率を大幅に向上させるためのワークフロー自動化コマンドを提供します。

## コマンド一覧

### 1. `/project-setup` - プロジェクト初期セットアップ
プロジェクトの初期化と環境構築を自動化

```bash
/project-setup node my-project    # Node.jsプロジェクト
/project-setup python            # Pythonプロジェクト（自動検出）
/project-setup docker            # Dockerプロジェクト
```

**主な機能:**
- プロジェクトタイプの自動検出
- 依存関係のインストール
- 環境設定ファイルの生成
- 開発ツールの初期化

### 2. `/mcp-setup` - MCP サーバー設定
Model Context Protocol サーバーの追加と設定を自動化

```bash
/mcp-setup github --scope=user              # GitHub MCP Server
/mcp-setup lark-base --scope=project        # Lark MCP Server
/mcp-setup --list                           # 利用可能なサーバー一覧
```

**主な機能:**
- 各種MCPサーバーの自動セットアップ
- 認証設定の支援
- スコープ管理（local/project/user）
- 動作確認とトラブルシューティング

### 3. `/dev-workflow` - 開発ワークフロー管理
Git操作、コード品質チェック、自動化タスクを統合管理

```bash
/dev-workflow status                         # プロジェクト状態確認
/dev-workflow lint --fix                     # コード品質チェック
/dev-workflow test --coverage                # テスト実行
/dev-workflow commit --message="feat: new"  # 自動コミット
```

**主な機能:**
- Git操作の自動化
- Lint/Format/型チェック
- 自動コミットメッセージ生成
- ブランチ管理とマージ

### 4. `/test-deploy` - テスト＆デプロイ管理
テスト実行からデプロイメントまでを統合管理

```bash
/test-deploy unit --coverage                 # 単体テスト
/test-deploy integration --services          # 統合テスト
/test-deploy deploy staging --canary         # カナリアデプロイ
/test-deploy verify production --health      # 本番検証
```

**主な機能:**
- 多層テスト実行
- 環境別デプロイメント
- CI/CD パイプライン統合
- 自動ロールバック機能

### 5. `/doc-generator` - ドキュメント自動生成
プロジェクトドキュメントの生成と維持を自動化

```bash
/doc-generator api --spec=openapi            # API ドキュメント
/doc-generator readme --template=detailed    # README 生成
/doc-generator architecture --diagrams       # アーキテクチャ図
/doc-generator guide --interactive           # ユーザーガイド
```

**主な機能:**
- APIドキュメント自動生成
- README/設定ファイル生成
- アーキテクチャ図作成
- 多言語対応ドキュメント

## 作成されたファイル一覧

```
~/.claude/commands/
├── project-setup.md      # プロジェクト初期セットアップ
├── mcp-setup.md          # MCP サーバー設定
├── dev-workflow.md       # 開発ワークフロー管理
├── test-deploy.md        # テスト＆デプロイ管理
├── doc-generator.md      # ドキュメント自動生成
└── README.md            # このファイル
```

## 使用方法

Claude Codeで `/` を入力すると、カスタムコマンドがオートコンプリートに表示されます。

## 特徴

- **統合ワークフロー**: 開発からデプロイまでの全工程をカバー
- **プロジェクトタイプ対応**: Node.js, Python, Go, Rust等に対応
- **MCP統合**: GitHub, Lark等のMCPサーバーとの連携
- **自動化重視**: 繰り返し作業の自動化と効率化
- **品質保証**: テスト、Lint、セキュリティチェックの統合

これらのコマンドにより、Claude Codeでの開発効率が大幅に向上します。