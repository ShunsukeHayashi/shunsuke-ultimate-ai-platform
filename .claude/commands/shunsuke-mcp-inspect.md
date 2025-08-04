MCPサーバーやクライアントの設定を検査・診断します。

## 検査項目

### 1. Claude Desktop設定の確認
@~/Library/Application Support/Claude/claude_desktop_config.json

### 2. プロジェクトのMCP設定
- package.jsonのMCP関連設定
- .mcp/config.json
- 環境変数設定（.env）

### 3. MCPサーバーの検出
!find . -name "server.ts" -o -name "server.js" -o -name "*mcp*" | grep -v node_modules | head -20

### 4. 依存関係の確認
- @modelcontextprotocol/sdkのバージョン
- peer dependenciesの互換性
- 不足している依存関係

### 5. サーバー起動の診断
1. 起動コマンドの確認
2. 必要な環境変数の確認
3. ポートの競合チェック（SSEモードの場合）

### 6. ツールの検証
- 登録されているツールの一覧
- スキーマの妥当性チェック
- 命名規則の確認

### 7. 一般的な問題の検出
- TypeScriptのビルドエラー
- 循環依存
- 未使用のインポート
- セキュリティの問題（APIキーのハードコーディング等）

## 診断レポート
検査結果をまとめて以下を報告：
- ✅ 正常な項目
- ⚠️ 警告事項
- ❌ エラー項目
- 💡 改善提案