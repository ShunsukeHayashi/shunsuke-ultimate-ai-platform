プロジェクトの不要なファイルをクリーンアップします。

## 実行内容

1. ビルド成果物を削除
!find . -type d -name "dist" -o -name "build" -o -name "out" -o -name "__pycache__" -o -name ".next" | grep -v node_modules | head -20

2. 一時ファイルを削除
   - `.DS_Store` (macOS)
   - `*.log` (ルートディレクトリのみ)
   - `coverage/` ディレクトリ
   - `.cache/` ディレクトリ

3. 削除前に確認を求める
   - 削除対象のファイル/ディレクトリをリスト表示
   - ユーザーの確認後に削除実行

4. Git の状態を確認
!git status --short

注意: node_modules、.git、.env ファイルは削除しません。