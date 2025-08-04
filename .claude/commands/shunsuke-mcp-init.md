新しいMCPサーバープロジェクトを初期化します。

## プロジェクトタイプの選択

1. **TypeScript** (推奨)
   - 型安全性
   - 最新のJavaScript機能
   - 優れた開発体験

2. **JavaScript**
   - シンプルなセットアップ
   - 追加のビルドステップ不要

## 初期化手順

1. プロジェクトディレクトリの作成
!mkdir -p mcp-server-$ARGUMENTS && cd mcp-server-$ARGUMENTS

2. package.jsonの初期化
   ```json
   {
     "name": "mcp-server-$ARGUMENTS",
     "version": "0.1.0",
     "description": "MCP server for $ARGUMENTS",
     "main": "dist/index.js",
     "scripts": {
       "build": "tsc",
       "dev": "ts-node-dev --respawn src/server.ts",
       "start": "node dist/server.js"
     }
   }
   ```

3. 必要な依存関係のインストール
   - @modelcontextprotocol/sdk
   - TypeScriptの場合: typescript, ts-node-dev, @types/node

4. 基本的なディレクトリ構造の作成
   ```
   .
   ├── src/
   │   ├── server.ts
   │   ├── tools/
   │   │   └── index.ts
   │   └── types/
   ├── tests/
   ├── .env.example
   ├── .gitignore
   ├── tsconfig.json
   └── README.md
   ```

5. サンプルサーバーコードの生成

6. 開発環境のセットアップ確認
   - VSCode設定
   - ESLint/Prettier設定
   - Git初期化