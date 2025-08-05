# Course Generator Service - Production Deployment Guide

## 概要

このガイドでは、Course Generator Serviceを本番環境にデプロイする手順を説明します。本サービスは100%の機能テスト成功率を達成し、完全なDocker化とRedisキャッシング統合により本番環境での安定稼働が可能です。

## 前提条件

### 必須要件
- Docker 20.10+ & Docker Compose 2.0+
- PostgreSQL 16+
- Redis 7+
- SSL証明書（Let's Encrypt推奨）
- ドメイン名
- Gemini API Key

### 推奨スペック
- **最小構成**: 2 vCPU, 4GB RAM, 20GB SSD
- **推奨構成**: 4 vCPU, 8GB RAM, 50GB SSD
- **大規模構成**: 8+ vCPU, 16GB+ RAM, 100GB+ SSD

## デプロイメントオプション

### オプション1: VPS/専用サーバー（推奨）

#### 1. サーバー準備

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose git nginx certbot python3-certbot-nginx

# Docker権限設定
sudo usermod -aG docker $USER
```

#### 2. プロジェクトのクローン

```bash
git clone https://github.com/your-username/shunsuke-ultimate-ai-platform.git
cd shunsuke-ultimate-ai-platform/services/course-generator
```

#### 3. 環境変数の設定

```bash
# .env.productionファイルを作成
cat > .env.production << EOF
# Server Configuration
NODE_ENV=production
PORT=3002
CORS_ORIGIN=https://your-domain.com,https://www.your-domain.com

# Database
DATABASE_URL=postgresql://postgres:your-secure-password@postgres:5432/course_generator_db

# Redis
REDIS_URL=redis://default:your-redis-password@redis:6379

# Authentication
JWT_SECRET=$(openssl rand -base64 32)

# AI Services
GEMINI_API_KEY=your-gemini-api-key

# Storage
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./uploads
STORAGE_PUBLIC_URL=https://your-domain.com/uploads

# Service Limits
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60000
MAX_CRAWL_DEPTH=3
MAX_PAGES_PER_DOMAIN=50

# Logging
LOG_LEVEL=info
EOF

# 権限設定
chmod 600 .env.production
```

#### 4. SSL証明書の取得

```bash
# Let's Encryptを使用
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# 証明書をコピー
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
```

#### 5. 本番用docker-compose.ymlの準備

```bash
# 本番用設定を環境変数ファイルから読み込むよう修正
cp docker-compose.yml docker-compose.prod.yml
sed -i 's/.env/.env.production/g' docker-compose.prod.yml
```

#### 6. デプロイ

```bash
# イメージのビルドと起動
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# データベースマイグレーション実行
docker-compose -f docker-compose.prod.yml exec api npx prisma migrate deploy

# シードデータ投入（初回のみ）
docker-compose -f docker-compose.prod.yml exec api npx prisma db seed

# ログ確認
docker-compose -f docker-compose.prod.yml logs -f

# ステータス確認
docker-compose -f docker-compose.prod.yml ps

# ヘルスチェック
curl https://your-domain.com/api/health
```

### オプション2: クラウドプラットフォーム

#### Railway.app

1. [Railway](https://railway.app)にサインアップ
2. GitHubリポジトリを接続
3. 環境変数を設定
4. PostgreSQLとRedisサービスを追加
5. デプロイ

```toml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "services/course-generator/Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

#### Fly.io

1. Fly CLIをインストール
2. アプリケーションを作成

```bash
fly launch --path services/course-generator
fly postgres create
fly redis create
fly secrets set GEMINI_API_KEY=your_key JWT_SECRET=your_secret
fly deploy
```

### オプション3: Docker Hubを使用したデプロイ

#### 1. Docker Hubへのプッシュ

```bash
# Docker Hubにログイン
docker login

# イメージのビルドとタグ付け
docker build -t your-dockerhub-username/course-generator:latest .
docker tag your-dockerhub-username/course-generator:latest your-dockerhub-username/course-generator:v1.0.0

# Docker Hubにプッシュ
docker push your-dockerhub-username/course-generator:latest
docker push your-dockerhub-username/course-generator:v1.0.0
```

#### 2. 本番サーバーでのデプロイ

```bash
# docker-compose.ymlを更新
sed -i 's|build: .|image: your-dockerhub-username/course-generator:latest|g' docker-compose.prod.yml

# 最新イメージを取得して起動
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### オプション4: GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    paths:
      - 'services/course-generator/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./services/course-generator
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/course-generator:latest
            ${{ secrets.DOCKER_USERNAME }}/course-generator:${{ github.sha }}
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/course-generator
            docker-compose pull
            docker-compose up -d
            docker system prune -f
```

### オプション5: Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: course-generator-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: course-generator-api
  template:
    metadata:
      labels:
        app: course-generator-api
    spec:
      containers:
      - name: api
        image: ghcr.io/your-username/course-generator:latest
        ports:
        - containerPort: 3002
        env:
        - name: NODE_ENV
          value: "production"
        envFrom:
        - secretRef:
            name: course-generator-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 3002
          initialDelaySeconds: 30
          periodSeconds: 10
```

## フロントエンドのデプロイ

### Vercel（推奨）

1. [Vercel](https://vercel.com)にサインアップ
2. GitHubリポジトリをインポート
3. ルートディレクトリを`apps/course-generator-ui`に設定
4. 環境変数を設定：
   - `NEXT_PUBLIC_API_URL`: APIサーバーのURL

```bash
# Vercel CLI使用時
vercel --cwd apps/course-generator-ui
```

### Netlify

```toml
# netlify.toml
[build]
  base = "apps/course-generator-ui"
  command = "npm run build"
  publish = ".next"

[build.environment]
  NEXT_PUBLIC_API_URL = "https://api.your-domain.com"
```

## モニタリングとメンテナンス

### ヘルスチェックとステータス監視

```bash
# APIヘルスチェック（基本）
curl https://api.your-domain.com/health

# 詳細なAPIヘルスチェック
curl https://api.your-domain.com/api/health

# Redisキャッシュ統計
curl -H "Authorization: Bearer $TOKEN" https://api.your-domain.com/api/cache-stats

# データベース接続確認
docker-compose exec api npx prisma db pull

# 全サービスのステータス確認
docker-compose ps
```

### パフォーマンスモニタリング

```bash
# リソース使用状況
docker stats

# APIレスポンスタイム測定
for i in {1..10}; do
  time curl -s https://api.your-domain.com/api/health > /dev/null
done

# Redis性能確認
docker-compose exec redis redis-cli --stat
```

### ログ監視

```bash
# すべてのログ（リアルタイム）
docker-compose logs -f

# 特定のサービス
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f nginx

# エラーログのみ抽出
docker-compose logs api | grep -E "ERROR|error|Error"

# 特定の時間範囲のログ
docker-compose logs --since="2024-01-01T00:00:00" --until="2024-01-02T00:00:00" api
```

### バックアップとリストア

#### データベースバックアップ

```bash
# 手動バックアップ
docker-compose exec postgres pg_dump -U postgres course_generator_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 圧縮バックアップ
docker-compose exec postgres pg_dump -U postgres course_generator_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Redisバックアップ
docker-compose exec redis redis-cli BGSAVE
docker cp course_generator_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

#### 自動バックアップスクリプト

```bash
#!/bin/bash
# /opt/scripts/backup.sh

BACKUP_DIR="/backup/course-generator"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
docker-compose -f /opt/course-generator/docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres course_generator_db | gzip > $BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Redis backup
docker-compose -f /opt/course-generator/docker-compose.prod.yml exec -T redis redis-cli BGSAVE
sleep 5
docker cp course_generator_redis:/data/dump.rdb $BACKUP_DIR/redis_$(date +%Y%m%d_%H%M%S).rdb

# Upload files backup
tar -czf $BACKUP_DIR/uploads_$(date +%Y%m%d_%H%M%S).tar.gz /opt/course-generator/uploads

# Clean old backups
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Optional: Upload to S3
# aws s3 sync $BACKUP_DIR s3://your-backup-bucket/course-generator/
```

#### Cron設定

```bash
# 自動バックアップ設定
crontab -e

# 毎日午前2時にバックアップ
0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1

# 毎週日曜日に完全バックアップ
0 3 * * 0 /opt/scripts/full-backup.sh >> /var/log/backup.log 2>&1
```

#### リストア手順

```bash
# データベースリストア
gunzip -c backup_20240105_020000.sql.gz | docker-compose exec -T postgres psql -U postgres course_generator_db

# Redisリストア
docker cp redis_backup_20240105_020000.rdb course_generator_redis:/data/dump.rdb
docker-compose restart redis

# アップロードファイルリストア
tar -xzf uploads_20240105_020000.tar.gz -C /
```

### アップデートとゼロダウンタイムデプロイ

#### 基本的なアップデート

```bash
# 最新コードを取得
git pull origin main

# イメージの再ビルド
docker-compose -f docker-compose.prod.yml build

# ローリングアップデート
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api
```

#### ゼロダウンタイムデプロイ

```bash
#!/bin/bash
# /opt/scripts/zero-downtime-deploy.sh

# 新しいコンテナを別名で起動
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=2 api

# 新しいコンテナのヘルスチェックを待つ
echo "Waiting for new container to be healthy..."
sleep 30

# ヘルスチェック
NEW_CONTAINER=$(docker ps --format "table {{.Names}}" | grep api | tail -1)
for i in {1..30}; do
  if docker exec $NEW_CONTAINER curl -f http://localhost:3002/health > /dev/null 2>&1; then
    echo "New container is healthy"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 2
done

# nginxの設定を更新して新しいコンテナにトラフィックを向ける
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# 古いコンテナを停止
OLD_CONTAINER=$(docker ps --format "table {{.Names}}" | grep api | head -1)
docker stop $OLD_CONTAINER
docker rm $OLD_CONTAINER

# スケールを元に戻す
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=1 api
```

#### Blue-Greenデプロイメント

```bash
# Blue環境（現在の本番）
docker-compose -f docker-compose.blue.yml up -d

# Green環境（新バージョン）を準備
docker-compose -f docker-compose.green.yml build
docker-compose -f docker-compose.green.yml up -d

# Green環境のテスト
curl http://localhost:3003/api/health

# トラフィックをGreenに切り替え
sed -i 's/proxy_pass http:\/\/blue/proxy_pass http:\/\/green/g' nginx.conf
docker-compose -f docker-compose.nginx.yml restart nginx

# Blue環境を停止
docker-compose -f docker-compose.blue.yml down
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. ポート競合

```bash
# 使用中のポート確認
sudo lsof -i :3002
sudo lsof -i :5432
sudo lsof -i :6379

# 競合するプロセスを停止
sudo kill -9 $(sudo lsof -t -i:3002)

# またはポート番号を変更
sed -i 's/3002:3002/3003:3002/g' docker-compose.prod.yml
```

#### 2. メモリ不足

```bash
# Docker設定を調整
docker-compose down
docker system prune -a

# メモリ使用状況確認
free -h
docker system df

# Dockerのメモリ制限を設定
# docker-compose.yml に追加:
# services:
#   api:
#     mem_limit: 2g
#     mem_reservation: 1g
```

#### 3. データベース接続エラー

```bash
# PostgreSQL接続テスト
docker-compose exec postgres psql -U postgres -c "SELECT 1"

# 接続文字列の確認
docker-compose exec api printenv DATABASE_URL

# マイグレーションの再実行
docker-compose exec api npx prisma migrate reset --force
```

#### 4. Redis接続エラー

```bash
# Redis接続テスト
docker-compose exec redis redis-cli ping

# Redisメモリ使用状況
docker-compose exec redis redis-cli info memory

# Redisのフラッシュ（注意：全データ削除）
docker-compose exec redis redis-cli FLUSHALL
```

#### 5. SSL証明書エラー

```bash
# 証明書の状態確認
sudo certbot certificates

# 証明書の更新
sudo certbot renew --dry-run  # テスト
sudo certbot renew             # 実際の更新

# 証明書の自動更新設定
echo "0 0,12 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab > /dev/null
```

#### 6. APIレスポンスが遅い

```bash
# キャッシュの確認
curl -H "Authorization: Bearer $TOKEN" https://api.your-domain.com/api/cache-stats

# Slow queryの確認
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10"

# インデックスの追加
docker-compose exec api npx prisma db execute --file add-indexes.sql
```

### パフォーマンスチューニング

1. **PostgreSQL最適化**
   ```sql
   -- postgresql.conf
   shared_buffers = 256MB
   effective_cache_size = 1GB
   maintenance_work_mem = 64MB
   ```

2. **Redis設定**
   ```conf
   # redis.conf
   maxmemory 2gb
   maxmemory-policy allkeys-lru
   ```

## セキュリティ対策

### 基本的なセキュリティ設定

```bash
# ファイアウォール設定
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# 環境変数の保護
chmod 600 .env.production
chown $USER:$USER .env.production

# Dockerソケットの保護
sudo chmod 660 /var/run/docker.sock
```

### セキュリティベストプラクティス

1. **定期的なアップデート**
   ```bash
   # システムアップデート
   sudo apt update && sudo apt upgrade -y
   
   # Dockerイメージの更新
   docker-compose pull
   docker-compose up -d
   
   # 依存関係の脆弱性チェック
   docker-compose exec api npm audit
   ```

2. **アクセス制限**
   ```bash
   # IP制限（nginx.conf）
   location /api/admin {
       allow 192.168.1.0/24;
       deny all;
   }
   ```

3. **ログ監視**
   ```bash
   # 不審なアクセスの監視
   tail -f /var/log/nginx/access.log | grep -E "403|404|500"
   
   # fail2banの設定
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

## 本番環境チェックリスト

### デプロイ前

- [ ] 全ての環境変数が正しく設定されている
- [ ] SSL証明書が有効である
- [ ] データベースのバックアップが設定されている
- [ ] ログローテーションが設定されている
- [ ] モニタリングが設定されている
- [ ] ファイアウォールが適切に設定されている
- [ ] 機能テストが100%成功している

### デプロイ後

- [ ] ヘルスチェックが成功している
- [ ] 全てのAPIエンドポイントが応答している
- [ ] ログにエラーが出ていない
- [ ] パフォーマンスが期待通りである
- [ ] セキュリティスキャンが完了している
- [ ] バックアップが正常に動作している
- [ ] 監視アラートが設定されている

## 推奨される監視ツール

1. **Prometheus + Grafana**
   ```yaml
   # docker-compose.monitoring.yml
   services:
     prometheus:
       image: prom/prometheus
       volumes:
         - ./prometheus.yml:/etc/prometheus/prometheus.yml
       ports:
         - "9090:9090"
   
     grafana:
       image: grafana/grafana
       ports:
         - "3000:3000"
   ```

2. **ELK Stack（ログ管理）**
   ```bash
   docker run -d --name elasticsearch elasticsearch:7.17.0
   docker run -d --name logstash logstash:7.17.0
   docker run -d --name kibana kibana:7.17.0
   ```

3. **Uptime Kuma（稼働監視）**
   ```bash
   docker run -d --name uptime-kuma -p 3001:3001 louislam/uptime-kuma:1
   ```

## サポートとリソース

### ドキュメント
- [README](./README.md) - サービスの概要と基本的な使い方
- [API Documentation](./API.md) - 詳細なAPIリファレンス
- [Architecture Guide](./ARCHITECTURE.md) - システム設計の詳細

### コミュニティサポート
- [GitHub Issues](https://github.com/your-username/shunsuke-ultimate-ai-platform/issues)
- [Discord Server](https://discord.gg/your-invite)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/course-generator)

### 商用サポート
エンタープライズサポートが必要な場合は、以下にお問い合わせください：
- Email: support@your-domain.com
- Slack: your-workspace.slack.com

### 緊急時の対応

1. **サービス停止時**
   ```bash
   # 全サービスの再起動
   docker-compose restart
   
   # 個別サービスの再起動
   docker-compose restart api
   ```

2. **データ破損時**
   ```bash
   # 最新のバックアップからリストア
   ./scripts/restore-latest.sh
   ```

3. **セキュリティインシデント**
   - 即座にサービスを停止
   - ログを保全
   - セキュリティチームに連絡

---

最終更新: 2025年8月5日
バージョン: 1.0.0