#!/usr/bin/env python3
"""
シュンスケ式パフォーマンススイート - Ultimate ShunsukeModel Ecosystem

システム全体のパフォーマンスを最適化する包括的なツールキット
"""

from .performance_profiler import (
    PerformanceProfiler,
    ProfileResult,
    MemoryProfile,
    CPUProfile,
    IOProfile,
    NetworkProfile,
    create_performance_profiler,
    get_global_profiler,
    profile
)

from .resource_monitor import (
    ResourceMonitor,
    ResourceType,
    AlertLevel,
    ResourceMetrics,
    CPUMetrics,
    MemoryMetrics,
    DiskMetrics,
    NetworkMetrics,
    ProcessMetrics,
    Alert,
    create_resource_monitor
)

from .optimization_engine import (
    OptimizationEngine,
    OptimizationType,
    OptimizationLevel,
    OptimizationRule,
    OptimizationResult,
    PerformanceBottleneck,
    create_optimization_engine
)

from .benchmark_suite import (
    BenchmarkRunner,
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkSuite,
    BenchmarkType,
    create_benchmark_runner,
    benchmark_cpu_intensive,
    benchmark_memory_intensive,
    benchmark_io_intensive,
    benchmark_async_operations
)

__version__ = "1.0.0"
__author__ = "ShunsukeModel Team"

__all__ = [
    # Performance Profiler
    "PerformanceProfiler",
    "ProfileResult",
    "MemoryProfile",
    "CPUProfile",
    "IOProfile",
    "NetworkProfile",
    "create_performance_profiler",
    "get_global_profiler",
    "profile",
    
    # Resource Monitor
    "ResourceMonitor",
    "ResourceType",
    "AlertLevel",
    "ResourceMetrics",
    "CPUMetrics",
    "MemoryMetrics",
    "DiskMetrics",
    "NetworkMetrics",
    "ProcessMetrics",
    "Alert",
    "create_resource_monitor",
    
    # Optimization Engine
    "OptimizationEngine",
    "OptimizationType",
    "OptimizationLevel",
    "OptimizationRule",
    "OptimizationResult",
    "PerformanceBottleneck",
    "create_optimization_engine",
    
    # Benchmark Suite
    "BenchmarkRunner",
    "BenchmarkConfig",
    "BenchmarkResult",
    "BenchmarkSuite",
    "BenchmarkType",
    "create_benchmark_runner",
    "benchmark_cpu_intensive",
    "benchmark_memory_intensive",
    "benchmark_io_intensive",
    "benchmark_async_operations"
]

# モジュール情報
__doc__ = """
Ultimate ShunsukeModel Ecosystem - Performance Suite

統合パフォーマンス最適化ツールキット

主要コンポーネント:

1. Performance Profiler (パフォーマンスプロファイラー)
   - コード実行時間の詳細分析
   - メモリ使用量プロファイリング
   - CPU使用率監視
   - I/Oパフォーマンス測定
   - ボトルネック自動検出
   - 最適化提案生成

2. Resource Monitor (リソースモニター)
   - リアルタイムシステムリソース監視
   - CPU、メモリ、ディスク、ネットワークの使用状況
   - 異常検知とアラート機能
   - トレンド分析
   - プロセス別リソース追跡

3. Optimization Engine (最適化エンジン)
   - コードの自動最適化
   - アルゴリズム改善提案
   - メモ化・キャッシング実装
   - 並列化・非同期化変換
   - データ構造最適化
   - SQL クエリ最適化

4. Benchmark Suite (ベンチマークスイート)
   - 包括的パフォーマンステスト
   - ベースライン比較
   - 統計分析とレポート生成
   - 長期トレンド追跡
   - マルチプラットフォーム対応

使用例:

# パフォーマンスプロファイリング
from tools.performance_suite import profile

@profile
async def my_function():
    # 処理
    pass

# リソース監視
from tools.performance_suite import create_resource_monitor

monitor = create_resource_monitor()
await monitor.start_monitoring()

# コード最適化
from tools.performance_suite import create_optimization_engine

engine = create_optimization_engine()
bottlenecks = await engine.analyze_code(file_path)
results = await engine.optimize_code(file_path, bottlenecks)

# ベンチマーク実行
from tools.performance_suite import create_benchmark_runner, BenchmarkConfig

runner = create_benchmark_runner()
config = BenchmarkConfig(name="my_test", iterations=100)
result = await runner.run_benchmark(config, test_function)

統合機能:
- Claude Code グローバル設定対応
- GitHub Actions 自動化
- MCP サーバー統合
- リアルタイム品質監視との連携
- 自動ドキュメント生成

最適化レベル:
- Conservative: 安全な最適化のみ実行
- Moderate: 標準的な最適化（デフォルト）
- Aggressive: 積極的な最適化（リスクあり）

監視しきい値:
- CPU: 警告 70%、クリティカル 90%
- メモリ: 警告 80%、クリティカル 95%
- ディスク: 警告 85%、クリティカル 95%
- カスタマイズ可能

レポート形式:
- テキストレポート
- JSON データエクスポート
- HTML レポート生成
- パフォーマンスグラフ
- CSV エクスポート
"""