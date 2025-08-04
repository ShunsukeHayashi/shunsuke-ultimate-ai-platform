# Project Setup Command

プロジェクトの初期セットアップを自動化するコマンドです。

## 実行内容

1. プロジェクト構造の分析
2. 必要な依存関係の確認とインストール
3. 環境設定ファイルの作成
4. 開発環境の初期化
5. Git設定の確認

## 使用方法

```
/project-setup [project-type] [project-name]
```

## パラメータ

- `project-type`: プロジェクトタイプ (node, python, go, rust, docker等)
- `project-name`: プロジェクト名（省略可）

## 処理フロー

以下の順序で処理を実行します：

### 1. プロジェクトタイプの検出・確認
- package.json, requirements.txt, go.mod, Cargo.toml等を確認
- パラメータが指定されている場合はそれを優先
- 不明な場合はユーザーに確認

### 2. 依存関係の確認
各プロジェクトタイプに応じて：
- **Node.js**: npm/yarn/pnpmの確認とpackage.jsonの解析
- **Python**: pip/poetry/condaの確認とrequirements.txtの解析
- **Go**: go modの確認と依存関係の取得
- **Rust**: cargoの確認とCargo.tomlの解析
- **Docker**: Dockerfile/docker-compose.ymlの確認

### 3. 環境設定
- .env.exampleから.envファイルの作成
- 設定テンプレートの適用
- IDE/エディタ設定ファイルの確認

### 4. 開発ツールの設定
- Linter/Formatter設定の確認
- Pre-commitフックの設定
- テスト環境の準備

### 5. 初期化実行
```bash
# Node.js例
npm install
npm run build  # buildスクリプトがある場合
npm test      # testスクリプトがある場合

# Python例  
pip install -r requirements.txt
python -m pytest  # テストがある場合

# Go例
go mod download
go build ./...
go test ./...

# Rust例
cargo build
cargo test
```

### 6. 設定確認レポート
- インストールされた依存関係のリスト
- 設定されたツールとバージョン
- 利用可能なスクリプト/コマンド
- 次のステップの提案

## トラブルシューティング

### よくある問題と解決策

1. **依存関係のバージョン競合**
   - 最新のlock fileを確認
   - キャッシュクリア（npm cache clean, pip cache purge等）
   - 仮想環境の再作成

2. **権限エラー**
   - sudo権限の確認
   - ユーザー権限でのインストール方法の提案

3. **ネットワークエラー**
   - プロキシ設定の確認
   - レジストリ設定の確認
   - オフラインモードの提案

## 設定例

### Node.js プロジェクト
```json
{
  "scripts": {
    "setup": "npm install && npm run build",
    "dev": "npm run start:dev",
    "test": "jest",
    "lint": "eslint .",
    "format": "prettier --write ."
  }
}
```

### Python プロジェクト  
```toml
[tool.poetry]
name = "project-name"
version = "0.1.0"

[tool.poetry.scripts]
setup = "poetry install && poetry run pytest"
dev = "poetry run python -m app"
test = "poetry run pytest"
lint = "poetry run flake8"
format = "poetry run black ."
```

このコマンドは、新しいプロジェクトでの開発開始を迅速化し、チーム間での環境の統一を支援します。