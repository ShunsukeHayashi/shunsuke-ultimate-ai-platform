MCPサーバーを起動・管理します: $ARGUMENTS

## 使用方法

- 引数なし: 利用可能なMCPサーバーを検出して情報表示
- `start` - サーバーを起動
- `dev` - 開発モードで起動（ホットリロード有効）
- `build` - サーバーをビルド
- `logs` - サーバーログを表示

## 実行内容

### サーバー検出
1. package.jsonからMCPサーバー設定を確認
@package.json

2. MCPサーバーファイルを探す
!find . -name "server.ts" -o -name "server.js" -o -name "index.ts" | grep -E "(server|src)" | grep -v node_modules | head -10

### 起動モードの判定
1. STDIOモード（標準）
   ```bash
   node server.js stdio
   ```

2. SSEモード（Server-Sent Events）
   ```bash
   node server.js sse --port 3000
   ```

### 環境変数の確認
@.env
@.env.example

### TypeScriptプロジェクトの場合
1. ビルドが必要かチェック
2. `npm run build` または `yarn build` を実行
3. `dist/` または `build/` ディレクトリから起動

### 開発時の推奨事項
- nodemonまたはts-node-devでホットリロード
- デバッグポートの設定（--inspect）
- ログレベルの設定（DEBUG=mcp:*）