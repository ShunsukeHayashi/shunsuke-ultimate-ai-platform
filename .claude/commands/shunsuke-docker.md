Docker関連の操作を実行します: $ARGUMENTS

## 利用可能なサブコマンド

引数なしの場合は、Dockerfileの存在確認と基本的な情報を表示します。

### 引数による操作

- `build` - Dockerイメージをビルド
- `run` - コンテナを実行
- `compose` - docker-compose操作
- `clean` - 未使用のイメージとコンテナを削除
- `status` - 実行中のコンテナを表示

## 実行内容

1. Dockerfile/docker-compose.ymlの存在確認
!ls -la Dockerfile docker-compose.yml docker-compose.yaml 2>/dev/null || echo "Dockerファイルが見つかりません"

2. 引数に基づいて適切な操作を実行
   - `build`: `docker build -t project-name .`
   - `run`: `docker run -it project-name`
   - `compose`: `docker-compose up -d`
   - `clean`: `docker system prune -f`
   - `status`: `docker ps -a`

3. 操作結果を報告
   - ビルド成功/失敗
   - コンテナの状態
   - 削除されたリソース