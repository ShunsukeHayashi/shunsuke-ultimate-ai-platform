MCP (Model Context Protocol) 関連の操作を実行します: $ARGUMENTS

## 利用可能なサブコマンド

- `init` - 新しいMCPプロジェクトを初期化
- `server` - MCPサーバーの起動・管理
- `tool` - MCPツールの作成・管理
- `test` - MCPツールのテスト実行
- `inspect` - MCPサーバーの情報を確認

## 実行内容

### 引数なしの場合
現在のプロジェクトがMCP対応かチェックして情報を表示

1. MCP設定ファイルの確認
@package.json
@mcp.json
@.mcp/config.json

2. MCPサーバーの検出
!find . -name "server.ts" -o -name "server.js" -o -name "mcp-server*" | grep -v node_modules | head -10

### `init` - MCPプロジェクトの初期化
1. プロジェクトタイプの選択（TypeScript/JavaScript）
2. 必要な依存関係をインストール
3. 基本的なサーバー構造を作成

### `server` - サーバー管理
1. サーバーの起動方法を確認
2. 環境変数の設定確認
3. 起動コマンドの実行

### `tool` - ツール管理
1. 新しいツールのテンプレート作成
2. ツールの登録と設定
3. ツールのドキュメント生成

### `test` - テスト実行
1. MCPツールのユニットテスト
2. 統合テストの実行
3. サーバーとの接続テスト