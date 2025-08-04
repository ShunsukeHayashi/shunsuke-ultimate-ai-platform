#!/bin/bash
# モニタリングセットアップスクリプト - Ultimate ShunsukeModel Ecosystem

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"

# Prometheus設定作成
create_prometheus_config() {
    cat > "$DEPLOYMENT_DIR/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'shunsuke-platform'
    environment: 'production'

# Alertmanager設定
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# ルールファイル
rule_files:
  - "alerts/*.yml"

# スクレイプ設定
scrape_configs:
  # Prometheus自身
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Command Tower
  - job_name: 'command-tower'
    static_configs:
      - targets: ['command-tower:8080']
    metrics_path: '/metrics'

  # Agent Coordinator
  - job_name: 'agent-coordinator'
    static_configs:
      - targets: ['agent-coordinator:8081']
    metrics_path: '/metrics'

  # Quality Guardian
  - job_name: 'quality-guardian'
    static_configs:
      - targets: ['quality-guardian:8082']
    metrics_path: '/metrics'

  # Performance Monitor
  - job_name: 'performance-monitor'
    static_configs:
      - targets: ['performance-monitor:8084']
    metrics_path: '/metrics'

  # Node Exporter
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Postgres Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Kubernetes metrics (if running on k8s)
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  # Kubernetes nodes
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  # Kubernetes pods
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name
EOF
}

# アラートルール作成
create_alert_rules() {
    mkdir -p "$DEPLOYMENT_DIR/prometheus/alerts"
    
    cat > "$DEPLOYMENT_DIR/prometheus/alerts/platform-alerts.yml" << 'EOF'
groups:
  - name: platform_alerts
    interval: 30s
    rules:
      # CPU使用率アラート
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected on {{ $labels.instance }}"
          description: "CPU usage is above 80% (current value: {{ $value }}%)"

      - alert: CriticalCPUUsage
        expr: rate(process_cpu_seconds_total[5m]) * 100 > 95
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Critical CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 95% (current value: {{ $value }}%)"

      # メモリ使用率アラート
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected on {{ $labels.instance }}"
          description: "Memory usage is above 85% (current value: {{ $value }}%)"

      # サービスダウンアラート
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute."

      # レスポンスタイムアラート
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time on {{ $labels.instance }}"
          description: "95th percentile response time is above 2 seconds (current value: {{ $value }}s)"

      # エラー率アラート
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is above 5% (current value: {{ $value }}%)"

      # ディスク使用率アラート
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk space is below 15% (current value: {{ $value }}%)"

      # Redis接続アラート
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis has been down for more than 1 minute"

      # PostgreSQL接続アラート
      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL has been down for more than 1 minute"

      # エージェント数アラート
      - alert: TooManyAgents
        expr: agent_coordinator_active_agents > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Too many active agents"
          description: "Active agent count is above 100 (current value: {{ $value }})"

      # 品質スコアアラート
      - alert: LowQualityScore
        expr: quality_guardian_overall_score < 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low quality score detected"
          description: "Overall quality score is below 0.7 (current value: {{ $value }})"
EOF
}

# Grafanaダッシュボード作成
create_grafana_dashboards() {
    mkdir -p "$DEPLOYMENT_DIR/grafana/dashboards"
    
    cat > "$DEPLOYMENT_DIR/grafana/dashboards/platform-overview.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "uid": "shunsuke-platform-overview",
    "title": "Shunsuke Platform Overview",
    "tags": ["shunsuke", "platform", "overview"],
    "timezone": "browser",
    "schemaVersion": 30,
    "version": 0,
    "refresh": "10s",
    "panels": [
      {
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "axisLabel": "",
              "axisPlacement": "auto",
              "barAlignment": 0,
              "drawStyle": "line",
              "fillOpacity": 10,
              "gradientMode": "none",
              "hideFrom": {
                "tooltip": false,
                "viz": false,
                "legend": false
              },
              "lineInterpolation": "linear",
              "lineWidth": 1,
              "pointSize": 5,
              "scaleDistribution": {
                "type": "linear"
              },
              "showPoints": "never",
              "spanNulls": true,
              "stacking": {
                "group": "A",
                "mode": "none"
              },
              "thresholdsStyle": {
                "mode": "off"
              }
            },
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": null
                },
                {
                  "color": "red",
                  "value": 80
                }
              ]
            },
            "unit": "percent"
          },
          "overrides": []
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        },
        "id": 2,
        "options": {
          "legend": {
            "calcs": [],
            "displayMode": "list",
            "placement": "bottom"
          },
          "tooltip": {
            "mode": "single",
            "sort": "none"
          }
        },
        "pluginVersion": "8.0.0",
        "targets": [
          {
            "expr": "rate(process_cpu_seconds_total[5m]) * 100",
            "refId": "A",
            "legendFormat": "{{job}}"
          }
        ],
        "title": "CPU Usage",
        "type": "timeseries"
      },
      {
        "datasource": {
          "type": "prometheus",
          "uid": "prometheus"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": null
                },
                {
                  "color": "yellow",
                  "value": 70
                },
                {
                  "color": "red",
                  "value": 85
                }
              ]
            },
            "unit": "percent"
          },
          "overrides": []
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        },
        "id": 3,
        "options": {
          "orientation": "auto",
          "reduceOptions": {
            "values": false,
            "calcs": [
              "lastNotNull"
            ],
            "fields": ""
          },
          "showThresholdLabels": false,
          "showThresholdMarkers": true
        },
        "pluginVersion": "8.0.0",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "refId": "A"
          }
        ],
        "title": "Memory Usage",
        "type": "gauge"
      }
    ]
  }
}
EOF

    # Grafanaプロビジョニング設定
    mkdir -p "$DEPLOYMENT_DIR/grafana/provisioning/dashboards"
    mkdir -p "$DEPLOYMENT_DIR/grafana/provisioning/datasources"
    
    cat > "$DEPLOYMENT_DIR/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    cat > "$DEPLOYMENT_DIR/grafana/provisioning/dashboards/default.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
}

# Logstash設定作成
create_logstash_config() {
    mkdir -p "$DEPLOYMENT_DIR/logstash/pipeline"
    mkdir -p "$DEPLOYMENT_DIR/logstash/config"
    
    cat > "$DEPLOYMENT_DIR/logstash/config/logstash.yml" << 'EOF'
http.host: "0.0.0.0"
xpack.monitoring.elasticsearch.hosts: [ "http://elasticsearch:9200" ]
EOF

    cat > "$DEPLOYMENT_DIR/logstash/pipeline/platform.conf" << 'EOF'
input {
  file {
    path => "/logs/**/*.log"
    start_position => "beginning"
    codec => "json"
    tags => ["shunsuke-platform"]
  }
}

filter {
  if [tags] == "shunsuke-platform" {
    date {
      match => [ "timestamp", "ISO8601" ]
      target => "@timestamp"
    }
    
    mutate {
      add_field => {
        "service" => "%{[fields][service]}"
        "environment" => "%{[fields][environment]}"
      }
    }
    
    if [level] == "ERROR" or [level] == "CRITICAL" {
      mutate {
        add_tag => [ "alert" ]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "shunsuke-platform-%{+YYYY.MM.dd}"
  }
  
  if "alert" in [tags] {
    stdout {
      codec => rubydebug
    }
  }
}
EOF
}

# メイン処理
main() {
    echo "Setting up monitoring for Shunsuke Platform..."
    
    # ディレクトリ作成
    mkdir -p "$DEPLOYMENT_DIR/prometheus/alerts"
    mkdir -p "$DEPLOYMENT_DIR/grafana/dashboards"
    mkdir -p "$DEPLOYMENT_DIR/logstash/pipeline"
    
    # 設定ファイル作成
    create_prometheus_config
    create_alert_rules
    create_grafana_dashboards
    create_logstash_config
    
    echo "Monitoring setup completed!"
    echo ""
    echo "Access points:"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000 (admin/shunsuke2024)"
    echo "  - Kibana: http://localhost:5601"
    echo ""
    echo "To start monitoring stack, run:"
    echo "  cd $DEPLOYMENT_DIR && docker-compose up -d prometheus grafana elasticsearch kibana logstash"
}

main "$@"