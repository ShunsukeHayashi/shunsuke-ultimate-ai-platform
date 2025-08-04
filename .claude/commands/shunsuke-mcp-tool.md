新しいMCPツールを作成・管理します: $ARGUMENTS

## 使用方法

- `new <tool-name>` - 新しいツールを作成
- `list` - 既存のツールを一覧表示
- `test <tool-name>` - 特定のツールをテスト
- `docs` - ツールのドキュメントを生成

## 実行内容

### 新しいツールの作成 (`new`)

1. ツールディレクトリの作成
   ```
   src/tools/<tool-name>/
   ├── index.ts
   ├── schema.ts
   └── __tests__/
       └── <tool-name>.test.ts
   ```

2. 基本的なツールテンプレートを生成
   - 入力スキーマの定義
   - ツール実装の雛形
   - テストファイルの雛形

3. ツールの登録
   - tools/index.tsに新しいツールをエクスポート
   - server.tsにツールを登録

### 既存ツールの確認 (`list`)
!find . -path "*/tools/*" -name "*.ts" -o -name "*.js" | grep -v test | grep -v node_modules | head -20

### ツールのテスト (`test`)
1. 単体テストの実行
2. スキーマ検証
3. エラーハンドリングの確認

### ドキュメント生成 (`docs`)
1. ツールのスキーマからドキュメントを自動生成
2. 使用例の追加
3. README.mdの更新

## ツール作成のベストプラクティス

- 明確で説明的な名前を使用
- 入力パラメータの検証を徹底
- エラーメッセージを分かりやすく
- 単体テストを必ず作成
- TypeScriptの型を活用