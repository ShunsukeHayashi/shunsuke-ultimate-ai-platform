# MCP Server Setup Command

Model Context Protocol (MCP) サーバーのセットアップを自動化するコマンドです。

## 実行内容

1. 利用可能なMCPサーバーの検出
2. 依存関係の確認とインストール
3. 設定ファイルの生成
4. サーバーの起動と動作確認
5. Claude Code/Desktopの設定更新

## 使用方法

```
/mcp-setup [server-type] [--scope=local|project|user]
```

## パラメータ

- `server-type`: セットアップするMCPサーバータイプ
- `--scope`: 設定スコープ（local, project, user）

## サポートするMCPサーバー

### 1. GitHub MCP Server
```bash
# Docker版（推奨）
claude mcp add github --scope user -e GITHUB_PERSONAL_ACCESS_TOKEN=your_token -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server

# SSE版（OAuth認証）
claude mcp add --transport sse github https://api.githubcopilot.com/mcp/
```

### 2. Lark OpenAPI MCP Server
```bash
# ローカル実行版
claude mcp add lark-base --scope project /Users/shunsuke/Dev/organized/mcp-servers/lark-openapi-mcp-enhanced/bundles/start-bundle.sh base

# 各種サービス別設定
claude mcp add lark-docs --scope project -- bash start-bundle.sh docs
claude mcp add lark-genesis --scope project -- bash start-bundle.sh genesis
```

### 3. Dify Workflow MCP Server
```bash
# Python実行版
claude mcp add dify-workflow --scope user -e PYTHONPATH=/path/to/dify -- python simple_mcp_server.py --stdio
```

### 4. Google Apps Script MCP Server
```bash
# Node.js実行版
claude mcp add gas-interpreter --scope user -e GAS_INTERPRETER_API_URL=http://localhost:8002/execute-script -- node dist/server.js
```

### 5. Context Engineering MCP Server
```bash
# Shell script実行版
claude mcp add context-engineering --scope project -- bash scripts/run-mcp-server.sh
```

## 自動設定フロー

### 1. サーバータイプ検出
現在のディレクトリから以下を検出：
- package.json (Node.js MCP)
- requirements.txt (Python MCP) 
- go.mod (Go MCP)
- Dockerfile (Docker MCP)
- mcp.json/.mcp.json (設定ファイル)

### 2. 依存関係チェック
各サーバータイプに応じて：
- **Docker**: Docker Desktopの起動確認
- **Node.js**: npm/yarn/pnpmとNode.jsバージョン
- **Python**: pip/poetry/condaとPythonバージョン
- **Go**: Goコンパイラとgomodules

### 3. 環境変数設定
必要な環境変数の確認と設定：
- API Keys (GitHub PAT, Lark App ID/Secret等)
- Service URLs
- Authentication tokens
- Configuration paths

### 4. 設定ファイル生成
```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-path",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "${ENV_VAR_NAME:-default_value}"
      }
    }
  }
}
```

### 5. 動作確認
```bash
# サーバーリスト表示
claude mcp list

# 特定サーバーの詳細確認
claude mcp get server-name

# 接続テスト
/mcp
```

## 設定スコープ詳細

### Local Scope (default)
- 現在のプロジェクトでのみ利用
- 個人設定・実験的設定に適用
- チームと共有されない

### Project Scope  
- `.mcp.json`ファイルに保存
- バージョン管理でチームと共有
- プロジェクト固有のツール・サービス

### User Scope
- 全プロジェクトで利用可能
- ユーザー個人の設定
- 開発ツール・ユーティリティに適用

## トラブルシューティング

### 1. Docker関連エラー
```bash
# Docker状態確認
docker --version
docker run hello-world

# イメージプル
docker pull ghcr.io/github/github-mcp-server
```

### 2. 認証エラー
```bash
# 環境変数確認
echo $GITHUB_PERSONAL_ACCESS_TOKEN
echo $LARK_APP_ID

# OAuth認証
/mcp
# -> 認証メニューで再認証
```

### 3. ポート競合
```bash
# ポート使用状況確認
lsof -i :8002
lsof -i :9002

# 代替ポート使用
claude mcp add server-name -e PORT=8003 ...
```

### 4. 権限エラー
```bash
# 実行権限確認
chmod +x /path/to/script.sh

# ファイル所有者確認
ls -la /path/to/config/
```

## カスタムMCPサーバーの追加

### 新しいサーバーの設定例
```bash
# JSONから直接追加
claude mcp add-json custom-server '{
  "type": "stdio",
  "command": "/path/to/server",
  "args": ["--stdio"],
  "env": {
    "API_KEY": "${CUSTOM_API_KEY}"
  }
}'

# Claude Desktopからインポート
claude mcp add-from-claude-desktop
```

このコマンドは、MCP環境の構築を簡素化し、開発者がすぐに外部ツールとの統合を開始できるようにします。