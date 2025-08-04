#!/usr/bin/env python3
"""
シュンスケ式パフォーマンスプロファイラー - Ultimate ShunsukeModel Ecosystem

コード実行のプロファイリング、ボトルネック検出、最適化提案を行う
高精度パフォーマンス分析システム
"""

import asyncio
import cProfile
import pstats
import io
import time
import tracemalloc
import psutil
import sys
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
import json
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
from collections import defaultdict, deque
import gc
import inspect
import ast


@dataclass
class ProfileResult:
    """プロファイル結果"""
    function_name: str
    total_time: float
    calls: int
    time_per_call: float
    cumulative_time: float
    memory_usage: float
    cpu_percent: float
    subcalls: List[Dict[str, Any]] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class MemoryProfile:
    """メモリプロファイル"""
    current_usage: float
    peak_usage: float
    allocated_blocks: int
    gc_stats: Dict[str, Any]
    top_allocations: List[Dict[str, Any]]
    memory_leaks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CPUProfile:
    """CPUプロファイル"""
    usage_percent: float
    core_usage: List[float]
    context_switches: int
    interrupts: int
    load_average: Tuple[float, float, float]
    thread_count: int


@dataclass
class IOProfile:
    """I/Oプロファイル"""
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int
    io_wait_time: float
    disk_usage: Dict[str, float]


@dataclass
class NetworkProfile:
    """ネットワークプロファイル"""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    connections: int
    latency_ms: float


class PerformanceProfiler:
    """
    シュンスケ式パフォーマンスプロファイラー
    
    機能:
    - 実行時間プロファイリング
    - メモリ使用状況分析
    - CPU使用率監視
    - I/Oパフォーマンス測定
    - ネットワーク性能分析
    - ボトルネック自動検出
    - 最適化提案生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # プロファイル設定
        self.enable_memory_profiling = self.config.get('enable_memory', True)
        self.enable_cpu_profiling = self.config.get('enable_cpu', True)
        self.enable_io_profiling = self.config.get('enable_io', True)
        self.enable_network_profiling = self.config.get('enable_network', False)
        
        # しきい値設定
        self.time_threshold = self.config.get('time_threshold', 0.1)  # 100ms
        self.memory_threshold = self.config.get('memory_threshold', 100 * 1024 * 1024)  # 100MB
        self.cpu_threshold = self.config.get('cpu_threshold', 80.0)  # 80%
        
        # プロファイルデータ保存
        self.profile_history = deque(maxlen=1000)
        self.performance_metrics = defaultdict(list)
        
        # 実行中のプロファイル
        self.active_profiles = {}
        self.profile_lock = threading.Lock()
        
        # 統計情報
        self.total_profiles = 0
        self.total_optimizations = 0
    
    def profile_function(self, func: Callable) -> Callable:
        """関数プロファイリングデコレーター"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            profile_id = f"{func.__name__}_{time.time()}"
            
            # プロファイル開始
            profile_data = await self.start_profile(profile_id, func.__name__)
            
            try:
                # 関数実行
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # プロファイル終了
                profile_result = await self.stop_profile(profile_id)
                
                # 結果分析
                await self._analyze_profile_result(profile_result)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Function profiling error: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    async def start_profile(self, profile_id: str, target_name: str) -> Dict[str, Any]:
        """プロファイル開始"""
        try:
            with self.profile_lock:
                if profile_id in self.active_profiles:
                    raise ValueError(f"Profile {profile_id} already active")
                
                profile_data = {
                    'id': profile_id,
                    'target': target_name,
                    'start_time': time.time(),
                    'start_memory': None,
                    'start_cpu': None,
                    'start_io': None,
                    'profiler': cProfile.Profile()
                }
                
                # メモリプロファイリング開始
                if self.enable_memory_profiling:
                    tracemalloc.start()
                    profile_data['start_memory'] = self._get_memory_usage()
                
                # CPU使用率記録
                if self.enable_cpu_profiling:
                    profile_data['start_cpu'] = self._get_cpu_usage()
                
                # I/O統計記録
                if self.enable_io_profiling:
                    profile_data['start_io'] = self._get_io_stats()
                
                # ネットワーク統計記録
                if self.enable_network_profiling:
                    profile_data['start_network'] = self._get_network_stats()
                
                # cProfiler開始
                profile_data['profiler'].enable()
                
                self.active_profiles[profile_id] = profile_data
                self.logger.debug(f"Started profile: {profile_id}")
                
                return profile_data
                
        except Exception as e:
            self.logger.error(f"Failed to start profile: {e}")
            raise
    
    async def stop_profile(self, profile_id: str) -> ProfileResult:
        """プロファイル終了"""
        try:
            with self.profile_lock:
                if profile_id not in self.active_profiles:
                    raise ValueError(f"Profile {profile_id} not found")
                
                profile_data = self.active_profiles.pop(profile_id)
                
                # cProfiler停止
                profile_data['profiler'].disable()
                
                # 実行時間計算
                end_time = time.time()
                total_time = end_time - profile_data['start_time']
                
                # プロファイル統計取得
                stats_stream = io.StringIO()
                stats = pstats.Stats(profile_data['profiler'], stream=stats_stream)
                stats.sort_stats('cumulative')
                
                # メモリ使用量計算
                memory_delta = 0
                memory_peak = 0
                if self.enable_memory_profiling:
                    end_memory = self._get_memory_usage()
                    memory_delta = end_memory - profile_data['start_memory']
                    memory_peak = tracemalloc.get_traced_memory()[1]
                    tracemalloc.stop()
                
                # CPU使用率計算
                cpu_percent = 0
                if self.enable_cpu_profiling:
                    end_cpu = self._get_cpu_usage()
                    cpu_percent = (end_cpu - profile_data['start_cpu']) / total_time
                
                # 結果構築
                result = ProfileResult(
                    function_name=profile_data['target'],
                    total_time=total_time,
                    calls=1,
                    time_per_call=total_time,
                    cumulative_time=total_time,
                    memory_usage=memory_delta,
                    cpu_percent=cpu_percent,
                    subcalls=self._extract_subcalls(stats),
                    bottlenecks=[],
                    optimization_suggestions=[]
                )
                
                # ボトルネック検出
                result.bottlenecks = await self._detect_bottlenecks(result, stats)
                
                # 最適化提案生成
                result.optimization_suggestions = await self._generate_optimization_suggestions(result)
                
                # 履歴に追加
                self.profile_history.append(result)
                self.total_profiles += 1
                
                self.logger.info(f"Profile completed: {profile_id} - {total_time:.3f}s")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to stop profile: {e}")
            raise
    
    def _get_memory_usage(self) -> float:
        """現在のメモリ使用量取得"""
        process = psutil.Process()
        return process.memory_info().rss
    
    def _get_cpu_usage(self) -> float:
        """CPU使用率取得"""
        return psutil.cpu_percent(interval=0.1)
    
    def _get_io_stats(self) -> Dict[str, Any]:
        """I/O統計取得"""
        io_counters = psutil.disk_io_counters()
        return {
            'read_bytes': io_counters.read_bytes,
            'write_bytes': io_counters.write_bytes,
            'read_count': io_counters.read_count,
            'write_count': io_counters.write_count
        }
    
    def _get_network_stats(self) -> Dict[str, Any]:
        """ネットワーク統計取得"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    
    def _extract_subcalls(self, stats: pstats.Stats) -> List[Dict[str, Any]]:
        """サブコール情報抽出"""
        subcalls = []
        
        try:
            # 上位10個の関数を抽出
            for func, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:10]:
                subcalls.append({
                    'function': f"{func[0]}:{func[1]}:{func[2]}",
                    'calls': nc,
                    'total_time': tt,
                    'cumulative_time': ct,
                    'time_per_call': tt / nc if nc > 0 else 0
                })
            
            return sorted(subcalls, key=lambda x: x['cumulative_time'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to extract subcalls: {e}")
            return []
    
    async def _detect_bottlenecks(self, result: ProfileResult, stats: pstats.Stats) -> List[str]:
        """ボトルネック検出"""
        bottlenecks = []
        
        try:
            # 実行時間のボトルネック
            if result.total_time > self.time_threshold:
                bottlenecks.append(f"Slow execution: {result.total_time:.3f}s (threshold: {self.time_threshold}s)")
            
            # メモリ使用量のボトルネック
            if result.memory_usage > self.memory_threshold:
                bottlenecks.append(f"High memory usage: {result.memory_usage / 1024 / 1024:.1f}MB (threshold: {self.memory_threshold / 1024 / 1024}MB)")
            
            # CPU使用率のボトルネック
            if result.cpu_percent > self.cpu_threshold:
                bottlenecks.append(f"High CPU usage: {result.cpu_percent:.1f}% (threshold: {self.cpu_threshold}%)")
            
            # ホットスポット検出
            hot_functions = []
            for func_info in result.subcalls[:3]:
                if func_info['cumulative_time'] > result.total_time * 0.2:  # 20%以上
                    hot_functions.append(func_info['function'])
            
            if hot_functions:
                bottlenecks.append(f"Hot spots detected: {', '.join(hot_functions)}")
            
            # 再帰呼び出し検出
            for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                if cc != nc:  # primitive calls != total calls
                    bottlenecks.append(f"Recursive calls detected in {func[2]}")
            
            return bottlenecks
            
        except Exception as e:
            self.logger.error(f"Bottleneck detection failed: {e}")
            return []
    
    async def _generate_optimization_suggestions(self, result: ProfileResult) -> List[str]:
        """最適化提案生成"""
        suggestions = []
        
        try:
            # 実行時間の最適化
            if result.total_time > self.time_threshold:
                suggestions.append("Consider using caching for frequently called functions")
                suggestions.append("Profile and optimize hot spots in the code")
                
                # 並列化の提案
                if result.cpu_percent < 50:
                    suggestions.append("Consider parallelizing CPU-bound operations")
            
            # メモリ最適化
            if result.memory_usage > self.memory_threshold:
                suggestions.append("Use generators instead of lists for large data sets")
                suggestions.append("Implement object pooling for frequently created objects")
                suggestions.append("Consider using __slots__ for classes with many instances")
            
            # I/O最適化
            if any("read" in b or "write" in b for b in result.bottlenecks):
                suggestions.append("Use async I/O for file operations")
                suggestions.append("Implement buffering for frequent I/O operations")
                suggestions.append("Consider using memory-mapped files for large data")
            
            # アルゴリズム最適化
            if result.subcalls:
                top_function = result.subcalls[0]
                if top_function['time_per_call'] > 0.01:  # 10ms
                    suggestions.append(f"Optimize algorithm in {top_function['function']}")
                    suggestions.append("Consider using more efficient data structures")
            
            # データベース最適化
            if any("sql" in b.lower() or "query" in b.lower() for b in result.bottlenecks):
                suggestions.append("Add database indexes for frequently queried columns")
                suggestions.append("Use connection pooling for database operations")
                suggestions.append("Consider query result caching")
            
            self.total_optimizations += len(suggestions)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Optimization suggestion generation failed: {e}")
            return []
    
    async def _analyze_profile_result(self, result: ProfileResult):
        """プロファイル結果分析"""
        try:
            # メトリクス更新
            self.performance_metrics[result.function_name].append({
                'timestamp': datetime.now().isoformat(),
                'total_time': result.total_time,
                'memory_usage': result.memory_usage,
                'cpu_percent': result.cpu_percent,
                'bottlenecks': len(result.bottlenecks),
                'suggestions': len(result.optimization_suggestions)
            })
            
            # トレンド分析
            if len(self.performance_metrics[result.function_name]) >= 10:
                await self._analyze_performance_trends(result.function_name)
            
        except Exception as e:
            self.logger.error(f"Profile analysis failed: {e}")
    
    async def _analyze_performance_trends(self, function_name: str):
        """パフォーマンストレンド分析"""
        try:
            metrics = self.performance_metrics[function_name]
            recent_metrics = metrics[-10:]
            
            # 実行時間トレンド
            times = [m['total_time'] for m in recent_metrics]
            time_trend = np.polyfit(range(len(times)), times, 1)[0]
            
            if time_trend > 0.01:  # 増加傾向
                self.logger.warning(f"Performance degradation detected in {function_name}: {time_trend:.3f}s/call increase")
            
            # メモリ使用量トレンド
            memory_usage = [m['memory_usage'] for m in recent_metrics]
            memory_trend = np.polyfit(range(len(memory_usage)), memory_usage, 1)[0]
            
            if memory_trend > 1024 * 1024:  # 1MB/call増加
                self.logger.warning(f"Memory leak suspected in {function_name}: {memory_trend / 1024 / 1024:.1f}MB/call increase")
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
    
    async def profile_code_block(self, code: str, globals_dict: Dict[str, Any] = None) -> ProfileResult:
        """コードブロックのプロファイリング"""
        profile_id = f"code_block_{time.time()}"
        
        try:
            # プロファイル開始
            await self.start_profile(profile_id, "code_block")
            
            # コード実行
            exec(code, globals_dict or {})
            
            # プロファイル終了
            result = await self.stop_profile(profile_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Code block profiling failed: {e}")
            if profile_id in self.active_profiles:
                self.active_profiles.pop(profile_id)
            raise
    
    async def profile_async_function(self, coro: Any) -> Tuple[Any, ProfileResult]:
        """非同期関数のプロファイリング"""
        profile_id = f"async_{time.time()}"
        
        try:
            # プロファイル開始
            await self.start_profile(profile_id, str(coro))
            
            # コルーチン実行
            result = await coro
            
            # プロファイル終了
            profile_result = await self.stop_profile(profile_id)
            
            return result, profile_result
            
        except Exception as e:
            self.logger.error(f"Async function profiling failed: {e}")
            if profile_id in self.active_profiles:
                self.active_profiles.pop(profile_id)
            raise
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート生成"""
        try:
            # 最近のプロファイル結果
            recent_profiles = list(self.profile_history)[-10:]
            
            # 統計情報計算
            if recent_profiles:
                avg_time = np.mean([p.total_time for p in recent_profiles])
                avg_memory = np.mean([p.memory_usage for p in recent_profiles])
                avg_cpu = np.mean([p.cpu_percent for p in recent_profiles])
                
                # ボトルネックサマリー
                all_bottlenecks = []
                for profile in recent_profiles:
                    all_bottlenecks.extend(profile.bottlenecks)
                
                bottleneck_counts = defaultdict(int)
                for bottleneck in all_bottlenecks:
                    bottleneck_type = bottleneck.split(':')[0]
                    bottleneck_counts[bottleneck_type] += 1
                
                # 最適化提案サマリー
                all_suggestions = []
                for profile in recent_profiles:
                    all_suggestions.extend(profile.optimization_suggestions)
                
                suggestion_counts = defaultdict(int)
                for suggestion in all_suggestions:
                    suggestion_counts[suggestion] += 1
                
                # 上位の提案
                top_suggestions = sorted(
                    suggestion_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                return {
                    'summary': {
                        'total_profiles': self.total_profiles,
                        'total_optimizations': self.total_optimizations,
                        'average_execution_time': f"{avg_time:.3f}s",
                        'average_memory_usage': f"{avg_memory / 1024 / 1024:.1f}MB",
                        'average_cpu_usage': f"{avg_cpu:.1f}%"
                    },
                    'bottleneck_summary': dict(bottleneck_counts),
                    'top_optimization_suggestions': [
                        {'suggestion': s, 'frequency': f}
                        for s, f in top_suggestions
                    ],
                    'recent_profiles': [
                        {
                            'function': p.function_name,
                            'time': f"{p.total_time:.3f}s",
                            'memory': f"{p.memory_usage / 1024 / 1024:.1f}MB",
                            'cpu': f"{p.cpu_percent:.1f}%",
                            'bottlenecks': len(p.bottlenecks),
                            'suggestions': len(p.optimization_suggestions)
                        }
                        for p in recent_profiles
                    ],
                    'performance_trends': self._get_performance_trends()
                }
            else:
                return {
                    'summary': {
                        'total_profiles': 0,
                        'message': 'No profiles available'
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Performance report generation failed: {e}")
            return {'error': str(e)}
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """パフォーマンストレンド取得"""
        trends = {}
        
        for function_name, metrics in self.performance_metrics.items():
            if len(metrics) >= 5:
                recent = metrics[-5:]
                times = [m['total_time'] for m in recent]
                
                # 簡易トレンド計算
                if times[-1] > times[0] * 1.2:
                    trend = "degrading"
                elif times[-1] < times[0] * 0.8:
                    trend = "improving"
                else:
                    trend = "stable"
                
                trends[function_name] = {
                    'trend': trend,
                    'recent_times': times,
                    'change': f"{((times[-1] / times[0]) - 1) * 100:.1f}%"
                }
        
        return trends
    
    async def export_profile_data(self, output_path: Path) -> bool:
        """プロファイルデータエクスポート"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': await self.get_performance_report(),
                'detailed_profiles': [
                    {
                        'function_name': p.function_name,
                        'total_time': p.total_time,
                        'memory_usage': p.memory_usage,
                        'cpu_percent': p.cpu_percent,
                        'bottlenecks': p.bottlenecks,
                        'optimization_suggestions': p.optimization_suggestions,
                        'subcalls': p.subcalls
                    }
                    for p in self.profile_history
                ],
                'performance_metrics': dict(self.performance_metrics)
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Profile data exported to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Profile export failed: {e}")
            return False


# パフォーマンスプロファイラーのファクトリー関数
def create_performance_profiler(config: Optional[Dict[str, Any]] = None) -> PerformanceProfiler:
    """パフォーマンスプロファイラー作成"""
    return PerformanceProfiler(config)


# グローバルプロファイラーインスタンス
_global_profiler = None


def get_global_profiler() -> PerformanceProfiler:
    """グローバルプロファイラー取得"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = create_performance_profiler()
    return _global_profiler


# デコレーター簡易版
def profile(func: Callable) -> Callable:
    """プロファイリングデコレーター"""
    return get_global_profiler().profile_function(func)


if __name__ == "__main__":
    # テスト実行
    async def test_performance_profiler():
        profiler = create_performance_profiler({
            'time_threshold': 0.001,  # 1ms
            'memory_threshold': 1024 * 1024,  # 1MB
            'cpu_threshold': 50.0  # 50%
        })
        
        # テスト関数
        @profiler.profile_function
        async def test_slow_function():
            # CPUバウンドな処理
            result = 0
            for i in range(1000000):
                result += i ** 2
            
            # メモリ使用
            data = [i for i in range(100000)]
            
            # I/O操作
            await asyncio.sleep(0.1)
            
            return result
        
        # プロファイル実行
        print("Running performance profiling test...")
        result = await test_slow_function()
        print(f"Function result: {result}")
        
        # レポート生成
        report = await profiler.get_performance_report()
        print("\nPerformance Report:")
        print(json.dumps(report, indent=2))
        
        # データエクスポート
        export_path = Path.home() / '.claude' / 'performance' / 'test_profile.json'
        await profiler.export_profile_data(export_path)
        print(f"\nProfile data exported to: {export_path}")
    
    asyncio.run(test_performance_profiler())