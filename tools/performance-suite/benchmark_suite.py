#!/usr/bin/env python3
"""
シュンスケ式ベンチマークスイート - Ultimate ShunsukeModel Ecosystem

システム全体のパフォーマンスを包括的に測定し、
ベースラインとの比較分析を行う高精度ベンチマークシステム
"""

import asyncio
import time
import psutil
import statistics
import logging
import json
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
import platform
import sys
import os
import gc
import tracemalloc
import subprocess


class BenchmarkType(Enum):
    """ベンチマークタイプ"""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    DATABASE = "database"
    ALGORITHM = "algorithm"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class BenchmarkConfig:
    """ベンチマーク設定"""
    name: str
    description: str
    benchmark_type: BenchmarkType
    iterations: int = 100
    warmup_iterations: int = 10
    timeout: float = 300.0  # 秒
    parallel_execution: bool = False
    collect_system_metrics: bool = True
    save_raw_data: bool = True
    generate_report: bool = True
    compare_baseline: bool = True


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""
    benchmark_id: str
    name: str
    timestamp: datetime
    config: BenchmarkConfig
    
    # 実行時間統計
    execution_times: List[float]
    min_time: float
    max_time: float
    mean_time: float
    median_time: float
    std_dev: float
    percentile_95: float
    percentile_99: float
    
    # システムメトリクス
    cpu_usage: Dict[str, float] = field(default_factory=dict)
    memory_usage: Dict[str, float] = field(default_factory=dict)
    io_stats: Dict[str, Any] = field(default_factory=dict)
    
    # 比較結果
    baseline_comparison: Optional[Dict[str, float]] = None
    performance_score: float = 0.0
    
    # エラー情報
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class BenchmarkSuite:
    """ベンチマークスイート"""
    suite_id: str
    name: str
    description: str
    benchmarks: List[BenchmarkConfig]
    created_at: datetime
    tags: List[str] = field(default_factory=list)


class BenchmarkRunner:
    """
    シュンスケ式ベンチマークランナー
    
    機能:
    - 包括的なパフォーマンス測定
    - ベースライン比較
    - 統計分析
    - レポート生成
    - 長期トレンド分析
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # ベンチマーク設定
        self.output_dir = Path(self.config.get('output_dir', './benchmark_results'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ベースライン管理
        self.baseline_file = self.output_dir / 'baseline.json'
        self.baseline_data = self._load_baseline()
        
        # 実行履歴
        self.execution_history: List[BenchmarkResult] = []
        
        # プロセスプール
        self.process_pool = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        
        # システム情報
        self.system_info = self._collect_system_info()
        
        # 統計情報
        self.stats = {
            'total_benchmarks': 0,
            'successful_benchmarks': 0,
            'failed_benchmarks': 0,
            'total_execution_time': 0.0
        }
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """システム情報収集"""
        return {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory_total': psutil.virtual_memory().total,
            'python_version': sys.version,
            'timestamp': datetime.now().isoformat()
        }
    
    def _load_baseline(self) -> Dict[str, Any]:
        """ベースラインデータ読み込み"""
        try:
            if self.baseline_file.exists():
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load baseline: {e}")
            return {}
    
    def _save_baseline(self):
        """ベースラインデータ保存"""
        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(self.baseline_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save baseline: {e}")
    
    async def run_benchmark(self, config: BenchmarkConfig, 
                          test_function: Callable,
                          *args, **kwargs) -> BenchmarkResult:
        """単一ベンチマーク実行"""
        benchmark_id = f"{config.name}_{int(time.time())}"
        self.logger.info(f"Starting benchmark: {config.name}")
        
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            name=config.name,
            timestamp=datetime.now(),
            config=config,
            execution_times=[],
            min_time=float('inf'),
            max_time=0.0,
            mean_time=0.0,
            median_time=0.0,
            std_dev=0.0,
            percentile_95=0.0,
            percentile_99=0.0
        )
        
        try:
            # ウォームアップ実行
            if config.warmup_iterations > 0:
                self.logger.debug(f"Running {config.warmup_iterations} warmup iterations")
                for _ in range(config.warmup_iterations):
                    if asyncio.iscoroutinefunction(test_function):
                        await test_function(*args, **kwargs)
                    else:
                        test_function(*args, **kwargs)
            
            # GCを無効化（より正確な測定のため）
            gc_enabled = gc.isenabled()
            gc.disable()
            
            # メモリ測定開始
            if config.collect_system_metrics:
                tracemalloc.start()
            
            # ベンチマーク実行
            execution_times = []
            system_metrics = defaultdict(list)
            
            for i in range(config.iterations):
                # システムメトリクス収集（前）
                if config.collect_system_metrics:
                    metrics_before = self._collect_metrics()
                
                # 実行時間測定
                start_time = time.perf_counter()
                
                try:
                    if asyncio.iscoroutinefunction(test_function):
                        await asyncio.wait_for(
                            test_function(*args, **kwargs),
                            timeout=config.timeout
                        )
                    else:
                        # 同期関数の場合
                        if config.parallel_execution:
                            future = self.thread_pool.submit(test_function, *args, **kwargs)
                            future.result(timeout=config.timeout)
                        else:
                            test_function(*args, **kwargs)
                    
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time
                    execution_times.append(execution_time)
                    
                except asyncio.TimeoutError:
                    result.errors.append(f"Iteration {i} timed out after {config.timeout}s")
                except Exception as e:
                    result.errors.append(f"Iteration {i} error: {str(e)}")
                
                # システムメトリクス収集（後）
                if config.collect_system_metrics:
                    metrics_after = self._collect_metrics()
                    for key in metrics_after:
                        if key in metrics_before:
                            system_metrics[key].append(
                                metrics_after[key] - metrics_before[key]
                            )
                
                # 進捗表示
                if (i + 1) % max(1, config.iterations // 10) == 0:
                    progress = (i + 1) / config.iterations * 100
                    self.logger.debug(f"Progress: {progress:.0f}%")
            
            # GCを元に戻す
            if gc_enabled:
                gc.enable()
            
            # メモリ測定終了
            if config.collect_system_metrics:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                result.memory_usage['current'] = current
                result.memory_usage['peak'] = peak
            
            # 統計計算
            if execution_times:
                result.execution_times = execution_times
                result.min_time = min(execution_times)
                result.max_time = max(execution_times)
                result.mean_time = statistics.mean(execution_times)
                result.median_time = statistics.median(execution_times)
                result.std_dev = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
                result.percentile_95 = np.percentile(execution_times, 95)
                result.percentile_99 = np.percentile(execution_times, 99)
                
                # システムメトリクス集計
                if system_metrics:
                    for key, values in system_metrics.items():
                        if values:
                            if 'cpu' in key:
                                result.cpu_usage[key] = statistics.mean(values)
                            elif 'memory' in key:
                                result.memory_usage[key] = statistics.mean(values)
                            else:
                                result.io_stats[key] = statistics.mean(values)
                
                # パフォーマンススコア計算
                result.performance_score = self._calculate_performance_score(result)
                
                # ベースライン比較
                if config.compare_baseline:
                    result.baseline_comparison = self._compare_with_baseline(result)
                
                self.stats['successful_benchmarks'] += 1
            else:
                result.errors.append("No successful executions")
                self.stats['failed_benchmarks'] += 1
            
            # 結果保存
            self.execution_history.append(result)
            self.stats['total_benchmarks'] += 1
            self.stats['total_execution_time'] += sum(execution_times) if execution_times else 0
            
            # レポート生成
            if config.generate_report:
                await self._generate_benchmark_report(result)
            
            self.logger.info(f"Benchmark completed: {config.name} (mean: {result.mean_time:.3f}s)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Benchmark execution error: {e}")
            result.errors.append(str(e))
            self.stats['failed_benchmarks'] += 1
            return result
    
    def _collect_metrics(self) -> Dict[str, float]:
        """システムメトリクス収集"""
        metrics = {}
        
        try:
            # CPU使用率
            metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            
            # メモリ使用量
            mem = psutil.virtual_memory()
            metrics['memory_used'] = mem.used
            metrics['memory_percent'] = mem.percent
            
            # I/O統計
            io = psutil.disk_io_counters()
            if io:
                metrics['io_read_bytes'] = io.read_bytes
                metrics['io_write_bytes'] = io.write_bytes
            
            # プロセス固有の情報
            process = psutil.Process()
            metrics['process_cpu_percent'] = process.cpu_percent()
            metrics['process_memory_rss'] = process.memory_info().rss
            
        except Exception as e:
            self.logger.error(f"Metrics collection error: {e}")
        
        return metrics
    
    def _calculate_performance_score(self, result: BenchmarkResult) -> float:
        """パフォーマンススコア計算"""
        try:
            # 基準値（仮想的な理想値）
            ideal_time = 0.001  # 1ms
            
            # スコア計算（0-100）
            score = (ideal_time / result.median_time) * 100
            score = min(100, max(0, score))
            
            # 安定性ペナルティ（標準偏差が大きい場合）
            if result.std_dev > result.mean_time * 0.2:  # 20%以上の変動
                score *= 0.9
            
            return round(score, 2)
            
        except Exception as e:
            self.logger.error(f"Score calculation error: {e}")
            return 0.0
    
    def _compare_with_baseline(self, result: BenchmarkResult) -> Dict[str, float]:
        """ベースライン比較"""
        comparison = {}
        
        try:
            baseline_key = f"{result.name}_{self.system_info['platform']}"
            
            if baseline_key in self.baseline_data:
                baseline = self.baseline_data[baseline_key]
                
                # 実行時間比較
                comparison['time_change_percent'] = (
                    (result.median_time - baseline['median_time']) / 
                    baseline['median_time'] * 100
                )
                
                # メモリ使用量比較
                if 'memory_peak' in baseline and result.memory_usage.get('peak'):
                    comparison['memory_change_percent'] = (
                        (result.memory_usage['peak'] - baseline['memory_peak']) / 
                        baseline['memory_peak'] * 100
                    )
                
                # スコア比較
                if 'performance_score' in baseline:
                    comparison['score_change'] = (
                        result.performance_score - baseline['performance_score']
                    )
            
        except Exception as e:
            self.logger.error(f"Baseline comparison error: {e}")
        
        return comparison
    
    async def run_benchmark_suite(self, suite: BenchmarkSuite,
                                test_functions: Dict[str, Callable]) -> List[BenchmarkResult]:
        """ベンチマークスイート実行"""
        results = []
        suite_start_time = time.time()
        
        self.logger.info(f"Starting benchmark suite: {suite.name}")
        
        for benchmark_config in suite.benchmarks:
            if benchmark_config.name not in test_functions:
                self.logger.warning(f"Test function not found for: {benchmark_config.name}")
                continue
            
            test_function = test_functions[benchmark_config.name]
            result = await self.run_benchmark(benchmark_config, test_function)
            results.append(result)
        
        suite_execution_time = time.time() - suite_start_time
        
        # スイートレポート生成
        await self._generate_suite_report(suite, results, suite_execution_time)
        
        self.logger.info(f"Benchmark suite completed: {suite.name} ({suite_execution_time:.1f}s)")
        
        return results
    
    async def _generate_benchmark_report(self, result: BenchmarkResult):
        """個別ベンチマークレポート生成"""
        try:
            report_dir = self.output_dir / result.name
            report_dir.mkdir(exist_ok=True)
            
            # テキストレポート
            report_path = report_dir / f"{result.benchmark_id}_report.txt"
            with open(report_path, 'w') as f:
                f.write(f"Benchmark Report: {result.name}\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Timestamp: {result.timestamp}\n")
                f.write(f"Iterations: {result.config.iterations}\n")
                f.write(f"System: {self.system_info['platform']}\n\n")
                
                f.write("Execution Time Statistics:\n")
                f.write(f"  Min: {result.min_time:.6f}s\n")
                f.write(f"  Max: {result.max_time:.6f}s\n")
                f.write(f"  Mean: {result.mean_time:.6f}s\n")
                f.write(f"  Median: {result.median_time:.6f}s\n")
                f.write(f"  Std Dev: {result.std_dev:.6f}s\n")
                f.write(f"  95th Percentile: {result.percentile_95:.6f}s\n")
                f.write(f"  99th Percentile: {result.percentile_99:.6f}s\n\n")
                
                f.write(f"Performance Score: {result.performance_score}\n\n")
                
                if result.baseline_comparison:
                    f.write("Baseline Comparison:\n")
                    for key, value in result.baseline_comparison.items():
                        f.write(f"  {key}: {value:+.2f}%\n")
                    f.write("\n")
                
                if result.errors:
                    f.write("Errors:\n")
                    for error in result.errors:
                        f.write(f"  - {error}\n")
            
            # JSONレポート
            json_path = report_dir / f"{result.benchmark_id}_data.json"
            with open(json_path, 'w') as f:
                json.dump({
                    'benchmark_id': result.benchmark_id,
                    'name': result.name,
                    'timestamp': result.timestamp.isoformat(),
                    'config': {
                        'iterations': result.config.iterations,
                        'warmup_iterations': result.config.warmup_iterations,
                        'timeout': result.config.timeout
                    },
                    'statistics': {
                        'min': result.min_time,
                        'max': result.max_time,
                        'mean': result.mean_time,
                        'median': result.median_time,
                        'std_dev': result.std_dev,
                        'percentile_95': result.percentile_95,
                        'percentile_99': result.percentile_99
                    },
                    'performance_score': result.performance_score,
                    'baseline_comparison': result.baseline_comparison,
                    'system_info': self.system_info,
                    'execution_times': result.execution_times if result.config.save_raw_data else []
                }, f, indent=2)
            
            # グラフ生成
            if result.execution_times:
                await self._generate_performance_graphs(result, report_dir)
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
    
    async def _generate_performance_graphs(self, result: BenchmarkResult, output_dir: Path):
        """パフォーマンスグラフ生成"""
        try:
            # 実行時間分布
            plt.figure(figsize=(10, 6))
            plt.hist(result.execution_times, bins=50, alpha=0.7, color='blue', edgecolor='black')
            plt.axvline(result.mean_time, color='red', linestyle='--', label=f'Mean: {result.mean_time:.3f}s')
            plt.axvline(result.median_time, color='green', linestyle='--', label=f'Median: {result.median_time:.3f}s')
            plt.xlabel('Execution Time (seconds)')
            plt.ylabel('Frequency')
            plt.title(f'Execution Time Distribution - {result.name}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig(output_dir / f"{result.benchmark_id}_distribution.png", dpi=150, bbox_inches='tight')
            plt.close()
            
            # 時系列グラフ
            plt.figure(figsize=(10, 6))
            plt.plot(result.execution_times, alpha=0.7)
            plt.xlabel('Iteration')
            plt.ylabel('Execution Time (seconds)')
            plt.title(f'Execution Time Over Iterations - {result.name}')
            plt.grid(True, alpha=0.3)
            
            # 移動平均を追加
            if len(result.execution_times) > 10:
                window_size = min(50, len(result.execution_times) // 10)
                moving_avg = np.convolve(result.execution_times, 
                                        np.ones(window_size) / window_size, 
                                        mode='valid')
                plt.plot(range(window_size - 1, len(result.execution_times)), 
                        moving_avg, 
                        color='red', 
                        linewidth=2, 
                        label=f'Moving Average ({window_size})')
                plt.legend()
            
            plt.savefig(output_dir / f"{result.benchmark_id}_timeseries.png", dpi=150, bbox_inches='tight')
            plt.close()
            
            # ボックスプロット（複数回のベンチマーク比較用）
            if len(self.execution_history) > 1:
                # 同じ名前のベンチマークを集める
                same_benchmarks = [r for r in self.execution_history if r.name == result.name]
                if len(same_benchmarks) > 1:
                    plt.figure(figsize=(10, 6))
                    data = [r.execution_times for r in same_benchmarks[-5:]]  # 最新5回
                    labels = [r.timestamp.strftime('%Y-%m-%d %H:%M') for r in same_benchmarks[-5:]]
                    
                    plt.boxplot(data, labels=labels)
                    plt.xlabel('Execution Time')
                    plt.ylabel('Time (seconds)')
                    plt.title(f'Performance Trend - {result.name}')
                    plt.xticks(rotation=45)
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                    plt.savefig(output_dir / f"{result.benchmark_id}_trend.png", dpi=150, bbox_inches='tight')
                    plt.close()
            
        except Exception as e:
            self.logger.error(f"Graph generation error: {e}")
    
    async def _generate_suite_report(self, suite: BenchmarkSuite, 
                                   results: List[BenchmarkResult],
                                   execution_time: float):
        """スイートレポート生成"""
        try:
            report_path = self.output_dir / f"{suite.suite_id}_suite_report.html"
            
            # HTML レポート生成
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Suite Report - {suite.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .good {{ color: green; }}
        .bad {{ color: red; }}
        .neutral {{ color: black; }}
        h1, h2 {{ color: #333; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .error {{ background-color: #ffeeee; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>Benchmark Suite Report: {suite.name}</h1>
    <p>{suite.description}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Benchmarks:</strong> {len(results)}</p>
        <p><strong>Successful:</strong> {sum(1 for r in results if not r.errors)}</p>
        <p><strong>Failed:</strong> {sum(1 for r in results if r.errors)}</p>
        <p><strong>Total Execution Time:</strong> {execution_time:.1f}s</p>
        <p><strong>System:</strong> {self.system_info['platform']}</p>
        <p><strong>CPU:</strong> {self.system_info['processor']}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>Benchmark Results</h2>
    <table>
        <tr>
            <th>Benchmark</th>
            <th>Mean Time (s)</th>
            <th>Median Time (s)</th>
            <th>Std Dev (s)</th>
            <th>Performance Score</th>
            <th>vs Baseline</th>
            <th>Status</th>
        </tr>
"""
            
            for result in results:
                status = "✓" if not result.errors else "✗"
                status_class = "good" if not result.errors else "bad"
                
                baseline_change = ""
                baseline_class = "neutral"
                if result.baseline_comparison and 'time_change_percent' in result.baseline_comparison:
                    change = result.baseline_comparison['time_change_percent']
                    baseline_change = f"{change:+.1f}%"
                    baseline_class = "good" if change < 0 else "bad" if change > 10 else "neutral"
                
                html_content += f"""
        <tr>
            <td>{result.name}</td>
            <td>{result.mean_time:.6f}</td>
            <td>{result.median_time:.6f}</td>
            <td>{result.std_dev:.6f}</td>
            <td>{result.performance_score:.1f}</td>
            <td class="{baseline_class}">{baseline_change}</td>
            <td class="{status_class}">{status}</td>
        </tr>
"""
            
            html_content += """
    </table>
"""
            
            # エラー詳細
            errors_found = False
            for result in results:
                if result.errors:
                    if not errors_found:
                        html_content += "<h2>Errors</h2>"
                        errors_found = True
                    
                    html_content += f"""
    <div class="error">
        <h3>{result.name}</h3>
        <ul>
"""
                    for error in result.errors:
                        html_content += f"            <li>{error}</li>\n"
                    
                    html_content += """        </ul>
    </div>
"""
            
            html_content += """
</body>
</html>
"""
            
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            self.logger.info(f"Suite report generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Suite report generation error: {e}")
    
    def update_baseline(self, result: BenchmarkResult):
        """ベースライン更新"""
        try:
            baseline_key = f"{result.name}_{self.system_info['platform']}"
            
            self.baseline_data[baseline_key] = {
                'name': result.name,
                'median_time': result.median_time,
                'mean_time': result.mean_time,
                'performance_score': result.performance_score,
                'memory_peak': result.memory_usage.get('peak', 0),
                'timestamp': result.timestamp.isoformat(),
                'system_info': self.system_info
            }
            
            self._save_baseline()
            self.logger.info(f"Baseline updated for: {result.name}")
            
        except Exception as e:
            self.logger.error(f"Baseline update error: {e}")
    
    async def compare_benchmarks(self, benchmark_ids: List[str]) -> Dict[str, Any]:
        """複数ベンチマーク比較"""
        try:
            # 指定されたベンチマークを収集
            benchmarks = []
            for result in self.execution_history:
                if result.benchmark_id in benchmark_ids:
                    benchmarks.append(result)
            
            if len(benchmarks) < 2:
                return {'error': 'Need at least 2 benchmarks to compare'}
            
            # 比較データ作成
            comparison = {
                'benchmarks': [],
                'winner': None,
                'summary': {}
            }
            
            best_score = 0
            winner = None
            
            for benchmark in benchmarks:
                data = {
                    'id': benchmark.benchmark_id,
                    'name': benchmark.name,
                    'median_time': benchmark.median_time,
                    'performance_score': benchmark.performance_score,
                    'cpu_usage': benchmark.cpu_usage.get('cpu_percent', 0),
                    'memory_peak': benchmark.memory_usage.get('peak', 0)
                }
                comparison['benchmarks'].append(data)
                
                if benchmark.performance_score > best_score:
                    best_score = benchmark.performance_score
                    winner = benchmark.name
            
            comparison['winner'] = winner
            comparison['summary'] = {
                'best_performance_score': best_score,
                'performance_spread': max(b.performance_score for b in benchmarks) - 
                                    min(b.performance_score for b in benchmarks)
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Benchmark comparison error: {e}")
            return {'error': str(e)}
    
    async def export_results(self, output_format: str = 'json') -> Path:
        """結果エクスポート"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if output_format == 'json':
                export_path = self.output_dir / f"benchmark_export_{timestamp}.json"
                
                export_data = {
                    'system_info': self.system_info,
                    'statistics': self.stats,
                    'results': [
                        {
                            'benchmark_id': r.benchmark_id,
                            'name': r.name,
                            'timestamp': r.timestamp.isoformat(),
                            'median_time': r.median_time,
                            'performance_score': r.performance_score,
                            'errors': r.errors
                        }
                        for r in self.execution_history
                    ]
                }
                
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
            elif output_format == 'csv':
                export_path = self.output_dir / f"benchmark_export_{timestamp}.csv"
                
                with open(export_path, 'w') as f:
                    f.write("benchmark_id,name,timestamp,median_time,performance_score,errors\n")
                    for r in self.execution_history:
                        errors = ';'.join(r.errors) if r.errors else ''
                        f.write(f"{r.benchmark_id},{r.name},{r.timestamp.isoformat()},"
                               f"{r.median_time},{r.performance_score},{errors}\n")
            
            else:
                raise ValueError(f"Unsupported format: {output_format}")
            
            self.logger.info(f"Results exported to: {export_path}")
            return export_path
            
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            raise
    
    def get_summary_report(self) -> Dict[str, Any]:
        """サマリーレポート取得"""
        try:
            if not self.execution_history:
                return {'message': 'No benchmark results available'}
            
            # パフォーマンス統計
            all_scores = [r.performance_score for r in self.execution_history if r.performance_score > 0]
            all_times = [r.median_time for r in self.execution_history if r.median_time > 0]
            
            # ベンチマーク別の統計
            by_benchmark = defaultdict(list)
            for result in self.execution_history:
                by_benchmark[result.name].append(result)
            
            benchmark_stats = {}
            for name, results in by_benchmark.items():
                times = [r.median_time for r in results]
                scores = [r.performance_score for r in results]
                
                benchmark_stats[name] = {
                    'executions': len(results),
                    'avg_time': statistics.mean(times) if times else 0,
                    'avg_score': statistics.mean(scores) if scores else 0,
                    'best_time': min(times) if times else 0,
                    'worst_time': max(times) if times else 0,
                    'improvement': ((times[0] - times[-1]) / times[0] * 100) if len(times) > 1 else 0
                }
            
            return {
                'total_benchmarks': self.stats['total_benchmarks'],
                'successful': self.stats['successful_benchmarks'],
                'failed': self.stats['failed_benchmarks'],
                'success_rate': self.stats['successful_benchmarks'] / max(self.stats['total_benchmarks'], 1) * 100,
                'total_execution_time': self.stats['total_execution_time'],
                'average_performance_score': statistics.mean(all_scores) if all_scores else 0,
                'average_execution_time': statistics.mean(all_times) if all_times else 0,
                'benchmark_statistics': benchmark_stats,
                'system_info': self.system_info
            }
            
        except Exception as e:
            self.logger.error(f"Summary report error: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """クリーンアップ"""
        self.process_pool.shutdown(wait=False)
        self.thread_pool.shutdown(wait=False)


# ベンチマークランナーのファクトリー関数
def create_benchmark_runner(config: Optional[Dict[str, Any]] = None) -> BenchmarkRunner:
    """ベンチマークランナー作成"""
    return BenchmarkRunner(config)


# 標準ベンチマーク関数
async def benchmark_cpu_intensive(n: int = 1000000):
    """CPU集約的ベンチマーク"""
    result = 0
    for i in range(n):
        result += i ** 2
    return result


async def benchmark_memory_intensive(size: int = 1000000):
    """メモリ集約的ベンチマーク"""
    data = [i for i in range(size)]
    sorted_data = sorted(data, reverse=True)
    return len(sorted_data)


async def benchmark_io_intensive(iterations: int = 100):
    """I/O集約的ベンチマーク"""
    temp_file = Path(f"temp_benchmark_{time.time()}.txt")
    try:
        for i in range(iterations):
            with open(temp_file, 'w') as f:
                f.write(f"Test data {i}\n" * 100)
            
            with open(temp_file, 'r') as f:
                content = f.read()
        
        return len(content)
    finally:
        if temp_file.exists():
            temp_file.unlink()


async def benchmark_async_operations(tasks: int = 100):
    """非同期操作ベンチマーク"""
    async def async_task(delay: float):
        await asyncio.sleep(delay)
        return delay
    
    tasks_list = [async_task(0.001) for _ in range(tasks)]
    results = await asyncio.gather(*tasks_list)
    return sum(results)


if __name__ == "__main__":
    # テスト実行
    async def test_benchmark_suite():
        # ベンチマークランナー作成
        runner = create_benchmark_runner({
            'output_dir': './benchmark_results'
        })
        
        # ベンチマーク設定
        cpu_benchmark = BenchmarkConfig(
            name="cpu_intensive",
            description="CPU intensive operations benchmark",
            benchmark_type=BenchmarkType.CPU,
            iterations=50,
            warmup_iterations=5
        )
        
        memory_benchmark = BenchmarkConfig(
            name="memory_intensive",
            description="Memory intensive operations benchmark",
            benchmark_type=BenchmarkType.MEMORY,
            iterations=30,
            warmup_iterations=3
        )
        
        io_benchmark = BenchmarkConfig(
            name="io_intensive",
            description="I/O intensive operations benchmark",
            benchmark_type=BenchmarkType.IO,
            iterations=20,
            warmup_iterations=2
        )
        
        async_benchmark = BenchmarkConfig(
            name="async_operations",
            description="Async operations benchmark",
            benchmark_type=BenchmarkType.SYSTEM,
            iterations=30,
            warmup_iterations=3
        )
        
        # ベンチマークスイート作成
        suite = BenchmarkSuite(
            suite_id=f"test_suite_{int(time.time())}",
            name="Performance Test Suite",
            description="Comprehensive performance benchmark suite",
            benchmarks=[cpu_benchmark, memory_benchmark, io_benchmark, async_benchmark],
            created_at=datetime.now(),
            tags=["performance", "test"]
        )
        
        # テスト関数マッピング
        test_functions = {
            "cpu_intensive": benchmark_cpu_intensive,
            "memory_intensive": benchmark_memory_intensive,
            "io_intensive": benchmark_io_intensive,
            "async_operations": benchmark_async_operations
        }
        
        # スイート実行
        print("Running benchmark suite...")
        results = await runner.run_benchmark_suite(suite, test_functions)
        
        # サマリー表示
        summary = runner.get_summary_report()
        print("\nBenchmark Summary:")
        print(json.dumps(summary, indent=2))
        
        # 結果エクスポート
        export_path = await runner.export_results('json')
        print(f"\nResults exported to: {export_path}")
        
        # クリーンアップ
        runner.cleanup()
    
    asyncio.run(test_benchmark_suite())