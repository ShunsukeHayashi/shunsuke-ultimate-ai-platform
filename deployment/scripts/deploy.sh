#!/bin/bash
# シュンスケ式デプロイメントスクリプト - Ultimate ShunsukeModel Ecosystem
# 本番環境への安全で確実なデプロイメントを実行

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ロゴ表示
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║     _   _ _ _   _                 _        ___  ___           ║
║    | | | | | |_(_)_ __ ___   __ _| |_ ___ |  \/  |           ║
║    | | | | | __| | '_ ` _ \ / _` | __/ _ \| |\/| |           ║
║    | |_| | | |_| | | | | | | (_| | ||  __/| |  | |           ║
║     \___/|_|\__|_|_| |_| |_|\__,_|\__\___||_|  |_|           ║
║                                                               ║
║          ShunsukeModel Ecosystem Deployment Tool              ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# 設定
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DEPLOYMENT_DIR="$SCRIPT_DIR/.."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$DEPLOYMENT_DIR/logs/deploy_${TIMESTAMP}.log"

# デプロイメントモード
DEPLOY_MODE="${1:-docker}"  # docker, kubernetes, terraform
ENVIRONMENT="${2:-staging}"  # staging, production
DRY_RUN="${3:-false}"

# ログディレクトリ作成
mkdir -p "$DEPLOYMENT_DIR/logs"

# ログ関数
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)
            echo -e "${GREEN}[INFO]${NC} ${message}"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} ${message}"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} ${message}"
            ;;
        *)
            echo -e "[${level}] ${message}"
            ;;
    esac
    
    echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# エラーハンドラー
error_exit() {
    log ERROR "$1"
    exit 1
}

# 前提条件チェック
check_prerequisites() {
    log INFO "Checking prerequisites..."
    
    # 必須コマンドチェック
    local required_commands=()
    
    case $DEPLOY_MODE in
        docker)
            required_commands=("docker" "docker-compose")
            ;;
        kubernetes)
            required_commands=("kubectl" "helm")
            ;;
        terraform)
            required_commands=("terraform" "aws")
            ;;
    esac
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error_exit "Required command '$cmd' not found. Please install it first."
        fi
    done
    
    log INFO "All prerequisites satisfied ✓"
}

# 環境変数ロード
load_environment() {
    local env_file="$DEPLOYMENT_DIR/.env.${ENVIRONMENT}"
    
    if [ -f "$env_file" ]; then
        log INFO "Loading environment from $env_file"
        set -a
        source "$env_file"
        set +a
    else
        log WARN "Environment file $env_file not found. Using defaults."
    fi
}

# ビルド実行
build_images() {
    log INFO "Building Docker images..."
    
    local services=(
        "core/command-tower"
        "orchestration"
        "tools/quality-analyzer"
        "tools/doc-synthesizer"
        "tools/performance-suite"
    )
    
    for service in "${services[@]}"; do
        local service_path="$PROJECT_ROOT/$service"
        local service_name=$(basename "$service" | tr '[:upper:]' '[:lower:]' | tr '-' '_')
        
        if [ -f "$service_path/Dockerfile" ]; then
            log INFO "Building $service_name..."
            
            if [ "$DRY_RUN" = "true" ]; then
                log INFO "[DRY RUN] Would build: docker build -t shunsuke-platform/$service_name:latest $service_path"
            else
                docker build -t "shunsuke-platform/$service_name:latest" \
                    -t "shunsuke-platform/$service_name:$TIMESTAMP" \
                    "$service_path" || error_exit "Failed to build $service_name"
            fi
        else
            log WARN "Dockerfile not found for $service"
        fi
    done
    
    log INFO "Image build completed ✓"
}

# Docker Compose デプロイ
deploy_docker_compose() {
    log INFO "Deploying with Docker Compose..."
    
    cd "$DEPLOYMENT_DIR"
    
    # ヘルスチェック
    if [ "$DRY_RUN" = "true" ]; then
        log INFO "[DRY RUN] Would run: docker-compose up -d"
    else
        docker-compose up -d || error_exit "Docker Compose deployment failed"
        
        # サービスが起動するまで待機
        log INFO "Waiting for services to be healthy..."
        sleep 30
        
        # ヘルスチェック
        docker-compose ps
    fi
    
    log INFO "Docker Compose deployment completed ✓"
}

# Kubernetes デプロイ
deploy_kubernetes() {
    log INFO "Deploying to Kubernetes..."
    
    # 名前空間作成
    if [ "$DRY_RUN" = "true" ]; then
        log INFO "[DRY RUN] Would create namespace: shunsuke-platform"
    else
        kubectl create namespace shunsuke-platform --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    # ConfigMapとSecret作成
    create_k8s_configs
    
    # デプロイメント適用
    local k8s_dir="$DEPLOYMENT_DIR/kubernetes"
    
    if [ "$DRY_RUN" = "true" ]; then
        log INFO "[DRY RUN] Would apply Kubernetes manifests"
        kubectl apply -f "$k8s_dir" --dry-run=client
    else
        kubectl apply -f "$k8s_dir" || error_exit "Kubernetes deployment failed"
        
        # デプロイメント状態確認
        kubectl -n shunsuke-platform rollout status deployment/command-tower
        kubectl -n shunsuke-platform rollout status deployment/agent-coordinator
        kubectl -n shunsuke-platform rollout status statefulset/quality-guardian
    fi
    
    log INFO "Kubernetes deployment completed ✓"
}

# Kubernetes設定作成
create_k8s_configs() {
    log INFO "Creating Kubernetes configurations..."
    
    # ConfigMap作成
    kubectl create configmap command-tower-config \
        --from-file="$PROJECT_ROOT/core/command-tower/config" \
        -n shunsuke-platform \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Secret作成（環境変数から）
    kubectl create secret generic postgres-secret \
        --from-literal=url="${POSTGRES_URL:-postgresql://postgres:postgres@postgres:5432/shunsuke_db}" \
        -n shunsuke-platform \
        --dry-run=client -o yaml | kubectl apply -f -
    
    kubectl create secret generic redis-secret \
        --from-literal=url="${REDIS_URL:-redis://redis:6379}" \
        -n shunsuke-platform \
        --dry-run=client -o yaml | kubectl apply -f -
}

# Terraform デプロイ
deploy_terraform() {
    log INFO "Deploying with Terraform..."
    
    cd "$DEPLOYMENT_DIR/terraform"
    
    # Terraform初期化
    if [ ! -d ".terraform" ]; then
        log INFO "Initializing Terraform..."
        terraform init || error_exit "Terraform init failed"
    fi
    
    # プラン作成
    log INFO "Creating Terraform plan..."
    terraform plan -out="tfplan_${TIMESTAMP}" || error_exit "Terraform plan failed"
    
    if [ "$DRY_RUN" = "true" ]; then
        log INFO "[DRY RUN] Terraform plan created. Would apply with: terraform apply tfplan_${TIMESTAMP}"
    else
        # 承認確認
        echo -e "${YELLOW}Do you want to apply this plan? (yes/no)${NC}"
        read -r response
        
        if [ "$response" = "yes" ]; then
            terraform apply "tfplan_${TIMESTAMP}" || error_exit "Terraform apply failed"
            log INFO "Terraform deployment completed ✓"
        else
            log WARN "Terraform deployment cancelled by user"
        fi
    fi
}

# ヘルスチェック実行
run_health_checks() {
    log INFO "Running health checks..."
    
    case $DEPLOY_MODE in
        docker)
            # Docker Composeサービスチェック
            local services=("command-tower" "agent-coordinator" "quality-guardian" "doc-synthesizer")
            
            for service in "${services[@]}"; do
                if docker-compose ps | grep -q "$service.*Up.*healthy"; then
                    log INFO "✓ $service is healthy"
                else
                    log WARN "✗ $service is not healthy"
                fi
            done
            ;;
            
        kubernetes)
            # Kubernetesポッドチェック
            kubectl -n shunsuke-platform get pods
            kubectl -n shunsuke-platform get services
            ;;
            
        terraform)
            # AWS リソースチェック
            aws eks describe-cluster --name shunsuke-platform-eks --query 'cluster.status' || true
            ;;
    esac
}

# スモークテスト実行
run_smoke_tests() {
    log INFO "Running smoke tests..."
    
    # Command Tower API テスト
    local api_url=""
    
    case $DEPLOY_MODE in
        docker)
            api_url="http://localhost:8080"
            ;;
        kubernetes)
            api_url=$(kubectl -n shunsuke-platform get service command-tower-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
            api_url="http://${api_url}:8080"
            ;;
    esac
    
    if [ -n "$api_url" ]; then
        log INFO "Testing Command Tower API at $api_url"
        
        # ヘルスエンドポイントテスト
        if curl -f -s "$api_url/health" > /dev/null; then
            log INFO "✓ Command Tower health check passed"
        else
            log WARN "✗ Command Tower health check failed"
        fi
    fi
}

# ロールバック機能
rollback() {
    log WARN "Rolling back deployment..."
    
    case $DEPLOY_MODE in
        docker)
            docker-compose down
            # 前のバージョンのイメージに戻す
            ;;
        kubernetes)
            kubectl -n shunsuke-platform rollout undo deployment/command-tower
            kubectl -n shunsuke-platform rollout undo deployment/agent-coordinator
            ;;
        terraform)
            # Terraformの場合は手動で前の状態に戻す必要がある
            log WARN "Terraform rollback requires manual intervention"
            ;;
    esac
}

# クリーンアップ
cleanup() {
    log INFO "Cleaning up temporary files..."
    
    # 古いログファイルを削除（30日以上）
    find "$DEPLOYMENT_DIR/logs" -name "*.log" -mtime +30 -delete
    
    # Terraformプランファイルを削除（7日以上）
    find "$DEPLOYMENT_DIR/terraform" -name "tfplan_*" -mtime +7 -delete
}

# メイン処理
main() {
    log INFO "Starting deployment process..."
    log INFO "Mode: $DEPLOY_MODE, Environment: $ENVIRONMENT, Dry Run: $DRY_RUN"
    
    # 前提条件チェック
    check_prerequisites
    
    # 環境変数ロード
    load_environment
    
    # ビルド実行（Dockerモードの場合）
    if [ "$DEPLOY_MODE" = "docker" ] || [ "$DEPLOY_MODE" = "kubernetes" ]; then
        build_images
    fi
    
    # デプロイ実行
    case $DEPLOY_MODE in
        docker)
            deploy_docker_compose
            ;;
        kubernetes)
            deploy_kubernetes
            ;;
        terraform)
            deploy_terraform
            ;;
        *)
            error_exit "Unknown deployment mode: $DEPLOY_MODE"
            ;;
    esac
    
    # ヘルスチェック
    if [ "$DRY_RUN" = "false" ]; then
        sleep 10
        run_health_checks
        run_smoke_tests
    fi
    
    # クリーンアップ
    cleanup
    
    log INFO "Deployment completed successfully! 🎉"
    log INFO "Log file: $LOG_FILE"
}

# トラップ設定（エラー時のクリーンアップ）
trap 'log ERROR "Deployment failed. Check log file: $LOG_FILE"' ERR

# メイン処理実行
main "$@"