#!/usr/bin/env python3
"""
シュンスケ式負荷テストフレームワーク - Ultimate ShunsukeModel Ecosystem

システムの負荷耐性、スケーラビリティ、パフォーマンス限界を
包括的に検証する高精度負荷テストシステム
"""

import asyncio
import aiohttp
import time
import logging
import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
import statistics
from enum import Enum
import psutil
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import signal
import yaml


# テスト対象モジュールのインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.performance_suite import create_resource_monitor
from tools.performance_suite.resource_monitor import ResourceMonitor, Alert, AlertLevel


class LoadPattern(Enum):
    """負荷パターン"""
    CONSTANT = "constant"           # 一定負荷
    RAMP_UP = "ramp_up"            # 徐々に増加
    SPIKE = "spike"                # スパイク負荷
    WAVE = "wave"                  # 波状負荷
    STRESS = "stress"              # ストレステスト
    BREAKPOINT = "breakpoint"      # 限界点探索
    CUSTOM = "custom"              # カスタムパターン


class RequestType(Enum):
    """リクエストタイプ"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    COMMAND = "COMMAND"
    QUERY = "QUERY"
    STREAM = "STREAM"


@dataclass
class LoadTestConfig:
    """負荷テスト設定"""
    name: str
    description: str
    target_url: Optional[str] = None
    target_function: Optional[Callable] = None
    load_pattern: LoadPattern = LoadPattern.CONSTANT
    duration: float = 60.0  # 秒
    users: int = 10
    ramp_up_time: float = 10.0
    requests_per_user: int = 100
    think_time: float = 1.0  # ユーザー間の待機時間
    timeout: float = 30.0
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_payload: Optional[Any] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class RequestResult:
    """リクエスト結果"""
    request_id: str
    user_id: int
    request_type: RequestType
    start_time: float
    end_time: float
    duration: float
    status_code: Optional[int] = None
    success: bool = False
    error: Optional[str] = None
    response_size: int = 0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadTestResult:
    """負荷テスト結果"""
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    requests_per_second: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    percentiles: Dict[str, float]  # 50th, 90th, 95th, 99th
    response_time_distribution: List[float]
    error_distribution: Dict[str, int]
    throughput: float  # bytes/sec
    concurrent_users: List[int]
    resource_usage: Dict[str, Any]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]


class VirtualUser:
    """仮想ユーザー"""
    
    def __init__(self, user_id: int, config: LoadTestConfig, session: aiohttp.ClientSession):
        self.user_id = user_id
        self.config = config
        self.session = session
        self.request_count = 0
        self.results: List[RequestResult] = []
        self.active = True
        
    async def run(self) -> List[RequestResult]:
        """ユーザーシミュレーション実行"""
        for i in range(self.config.requests_per_user):
            if not self.active:
                break
            
            # リクエスト実行
            result = await self._execute_request()
            self.results.append(result)
            self.request_count += 1
            
            # Think time
            if self.config.think_time > 0:
                await asyncio.sleep(self.config.think_time + random.uniform(-0.5, 0.5))
        
        return self.results
    
    async def _execute_request(self) -> RequestResult:
        """リクエスト実行"""
        request_id = f"user_{self.user_id}_req_{self.request_count}"
        start_time = time.time()
        
        result = RequestResult(
            request_id=request_id,
            user_id=self.user_id,
            request_type=RequestType.GET,
            start_time=start_time,
            end_time=start_time,
            duration=0.0
        )
        
        try:
            if self.config.target_url:
                # HTTPリクエスト
                async with self.session.get(
                    self.config.target_url,
                    headers=self.config.custom_headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    result.status_code = response.status
                    result.success = 200 <= response.status < 300
                    content = await response.read()
                    result.response_size = len(content)
                    
            elif self.config.target_function:
                # 関数呼び出し
                if asyncio.iscoroutinefunction(self.config.target_function):
                    response = await self.config.target_function(self.config.custom_payload)
                else:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self.config.target_function, self.config.custom_payload
                    )
                result.success = True
                result.custom_metrics['response'] = response
                
        except asyncio.TimeoutError:
            result.success = False
            result.error = "Timeout"
        except Exception as e:
            result.success = False
            result.error = str(e)
        finally:
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
        
        return result
    
    def stop(self):
        """ユーザー停止"""
        self.active = False


class LoadTestFramework:
    """
    シュンスケ式負荷テストフレームワーク
    
    機能:
    - 多様な負荷パターン生成
    - リアルタイムメトリクス収集
    - ボトルネック自動検出
    - スケーラビリティ分析
    - パフォーマンス推奨事項生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 結果保存先
        self.output_dir = Path(self.config.get('output_dir', './load_test_results'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 仮想ユーザー管理
        self.virtual_users: List[VirtualUser] = []
        self.active_users = 0
        
        # メトリクス収集
        self.results: List[RequestResult] = []
        self.metrics_history = deque(maxlen=1000)
        
        # リソースモニター
        self.resource_monitor: Optional[ResourceMonitor] = None
        
        # 統計情報
        self.stats = {
            'start_time': None,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_bytes': 0,
            'error_types': defaultdict(int)
        }
        
        # 実行制御
        self.is_running = False
        self.stop_signal = False
    
    async def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """負荷テスト実行"""
        self.logger.info(f"Starting load test: {config.name}")
        
        # 初期化
        self.is_running = True
        self.stop_signal = False
        self.stats['start_time'] = datetime.now()
        start_time = time.time()
        
        # リソースモニター開始
        self.resource_monitor = create_resource_monitor({
            'interval': 1.0,
            'thresholds': {
                'cpu': {'warning': 80, 'critical': 95},
                'memory': {'warning': 85, 'critical': 95}
            }
        })
        await self.resource_monitor.start_monitoring()
        
        try:
            # HTTPセッション作成
            connector = aiohttp.TCPConnector(limit=config.users * 2)
            async with aiohttp.ClientSession(connector=connector) as session:
                # 負荷パターンに応じた実行
                if config.load_pattern == LoadPattern.CONSTANT:
                    result = await self._run_constant_load(config, session)
                elif config.load_pattern == LoadPattern.RAMP_UP:
                    result = await self._run_ramp_up_load(config, session)
                elif config.load_pattern == LoadPattern.SPIKE:
                    result = await self._run_spike_load(config, session)
                elif config.load_pattern == LoadPattern.WAVE:
                    result = await self._run_wave_load(config, session)
                elif config.load_pattern == LoadPattern.STRESS:
                    result = await self._run_stress_test(config, session)
                elif config.load_pattern == LoadPattern.BREAKPOINT:
                    result = await self._run_breakpoint_test(config, session)
                else:
                    result = await self._run_custom_load(config, session)
            
            # 結果分析
            end_time = time.time()
            duration = end_time - start_time
            
            # リソース使用状況取得
            resource_report = await self.resource_monitor.get_resource_report()
            
            # 最終結果生成
            final_result = self._analyze_results(config, duration, resource_report)
            
            # レポート生成
            await self._generate_report(final_result)
            
            return final_result
            
        finally:
            # クリーンアップ
            if self.resource_monitor:
                await self.resource_monitor.stop_monitoring()
            self.is_running = False
    
    async def _run_constant_load(self, config: LoadTestConfig, session: aiohttp.ClientSession) -> LoadTestResult:
        """一定負荷テスト"""
        self.logger.info(f"Running constant load test with {config.users} users")
        
        # 全ユーザー同時起動
        tasks = []
        for i in range(config.users):
            user = VirtualUser(i, config, session)
            self.virtual_users.append(user)
            tasks.append(asyncio.create_task(user.run()))
        
        # タイムアウト付き実行
        try:
            all_results = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=config.duration
            )
            
            # 結果収集
            for user_results in all_results:
                self.results.extend(user_results)
                
        except asyncio.TimeoutError:
            self.logger.info("Test duration reached, stopping users...")
            for user in self.virtual_users:
                user.stop()
    
    async def _run_ramp_up_load(self, config: LoadTestConfig, session: aiohttp.ClientSession) -> LoadTestResult:
        """段階的負荷増加テスト"""
        self.logger.info(f"Running ramp-up load test: 0 to {config.users} users over {config.ramp_up_time}s")
        
        users_per_second = config.users / config.ramp_up_time
        tasks = []
        start_time = time.time()
        
        for i in range(config.users):
            # ユーザー起動タイミング計算
            delay = i / users_per_second
            
            async def start_user_delayed(user_id: int, delay: float):
                await asyncio.sleep(delay)
                user = VirtualUser(user_id, config, session)
                self.virtual_users.append(user)
                return await user.run()
            
            tasks.append(asyncio.create_task(start_user_delayed(i, delay)))
        
        # 全ユーザー完了待機
        try:
            all_results = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=config.duration
            )
            
            for user_results in all_results:
                if user_results:  # Noneチェック
                    self.results.extend(user_results)
                    
        except asyncio.TimeoutError:
            self.logger.info("Test duration reached")
            for user in self.virtual_users:
                user.stop()
    
    async def _run_spike_load(self, config: LoadTestConfig, session: aiohttp.ClientSession) -> LoadTestResult:
        """スパイク負荷テスト"""
        self.logger.info(f"Running spike load test")
        
        # 基本負荷
        base_users = max(1, config.users // 4)
        spike_users = config.users
        
        tasks = []
        
        # フェーズ1: 低負荷
        self.logger.info(f"Phase 1: Low load ({base_users} users)")
        for i in range(base_users):
            user = VirtualUser(i, config, session)
            self.virtual_users.append(user)
            tasks.append(asyncio.create_task(user.run()))
        
        await asyncio.sleep(config.duration * 0.3)
        
        # フェーズ2: スパイク
        self.logger.info(f"Phase 2: Spike ({spike_users} users)")
        for i in range(base_users, spike_users):
            user = VirtualUser(i, config, session)
            self.virtual_users.append(user)
            tasks.append(asyncio.create_task(user.run()))
        
        await asyncio.sleep(config.duration * 0.4)
        
        # フェーズ3: 低負荷に戻る
        self.logger.info(f"Phase 3: Return to low load")
        for i in range(base_users, spike_users):
            if i < len(self.virtual_users):
                self.virtual_users[i].stop()
        
        await asyncio.sleep(config.duration * 0.3)
        
        # 結果収集
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        for user_results in all_results:
            if isinstance(user_results, list):
                self.results.extend(user_results)
    
    async def _run_wave_load(self, config: LoadTestConfig, session: aiohttp.ClientSession) -> LoadTestResult:
        """波状負荷テスト"""
        self.logger.info(f"Running wave load test")
        
        wave_period = config.duration / 3  # 3波
        max_users = config.users
        min_users = max(1, config.users // 4)
        
        all_tasks = []
        elapsed_time = 0
        
        while elapsed_time < config.duration:
            # 波の現在位置計算
            wave_position = (elapsed_time % wave_period) / wave_period
            current_users = int(min_users + (max_users - min_users) * abs(np.sin(wave_position * np.pi)))
            
            # ユーザー数調整
            active_count = len([u for u in self.virtual_users if u.active])
            
            if current_users > active_count:
                # ユーザー追加
                for i in range(active_count, current_users):
                    user = VirtualUser(len(self.virtual_users), config, session)
                    self.virtual_users.append(user)
                    all_tasks.append(asyncio.create_task(user.run()))
            elif current_users < active_count:
                # ユーザー削減
                for i in range(current_users, active_count):
                    if i < len(self.virtual_users):
                        self.virtual_users[i].stop()
            
            await asyncio.sleep(1)
            elapsed_time += 1
        
        # 全タスク完了待機
        if all_tasks:
            all_results = await asyncio.gather(*all_tasks, return_exceptions=True)
            for user_results in all_results:
                if isinstance(user_results, list):
                    self.results.extend(user_results)
    
    async def _run_stress_test(self, config: LoadTestConfig, session: aiohttp.ClientSession) -> LoadTestResult:
        """ストレステスト（限界まで負荷増加）"""
        self.logger.info(f"Running stress test - finding breaking point")
        
        initial_users = 10
        user_increment = 10
        current_users = 0
        error_threshold = 0.1  # 10%エラー率で停止
        
        all_tasks = []
        phase = 0
        
        while not self.stop_signal:
            phase += 1
            current_users += user_increment
            
            self.logger.info(f"Stress test phase {phase}: {current_users} users")
            
            # 新規ユーザー追加
            new_tasks = []
            for i in range(len(self.virtual_users), current_users):
                user = VirtualUser(i, config, session)
                self.virtual_users.append(user)
                task = asyncio.create_task(user.run())
                all_tasks.append(task)
                new_tasks.append(task)
            
            # フェーズ実行
            await asyncio.sleep(30)  # 各フェーズ30秒
            
            # エラー率チェック
            recent_results = [r for r in self.results if time.time() - r.start_time < 30]
            if recent_results:
                error_rate = sum(1 for r in recent_results if not r.success) / len(recent_results)
                
                if error_rate > error_threshold:
                    self.logger.warning(f"Error threshold reached: {error_rate:.2%}")
                    self.stop_signal = True
                    break
            
            # リソース制限チェック
            if self.resource_monitor:
                current_metrics = await self.resource_monitor.get_current_metrics()
                cpu_usage = current_metrics.get('cpu', {}).get('usage_percent', 0)
                memory_usage = current_metrics.get('memory', {}).get('usage_percent', 0)
                
                if cpu_usage > 95 or memory_usage > 95:
                    self.logger.warning(f"Resource limit reached - CPU: {cpu_usage}%, Memory: {memory_usage}%")
                    self.stop_signal = True
                    break
            
            # 最大ユーザー数チェック
            if current_users >= config.users:
                self.logger.info(f"Maximum users reached: {current_users}")
                break
        
        # 全ユーザー停止
        for user in self.virtual_users:
            user.stop()
        
        # 結果収集
        if all_tasks:
            all_results = await asyncio.gather(*all_tasks, return_exceptions=True)
            for user_results in all_results:
                if isinstance(user_results, list):
                    self.results.extend(user_results)
    
    async def _run_breakpoint_test(self, config: LoadTestConfig, session: aiohttp.ClientSession) -> LoadTestResult:
        """ブレークポイントテスト（システム限界点探索）"""
        self.logger.info(f"Running breakpoint test - finding system limits")
        
        # 二分探索で限界点を見つける
        min_users = 1
        max_users = config.users
        breakpoint_users = 0
        tolerance = 5  # ユーザー数の許容誤差
        
        while max_users - min_users > tolerance:
            current_users = (min_users + max_users) // 2
            self.logger.info(f"Testing with {current_users} users")
            
            # テスト実行
            self.virtual_users = []
            self.results = []
            
            tasks = []
            for i in range(current_users):
                user = VirtualUser(i, config, session)
                self.virtual_users.append(user)
                tasks.append(asyncio.create_task(user.run()))
            
            # 1分間実行
            await asyncio.sleep(60)
            
            # ユーザー停止
            for user in self.virtual_users:
                user.stop()
            
            # 結果収集
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            test_results = []
            for user_results in all_results:
                if isinstance(user_results, list):
                    test_results.extend(user_results)
            
            # 成功率計算
            if test_results:
                success_rate = sum(1 for r in test_results if r.success) / len(test_results)
                avg_response_time = statistics.mean(r.duration for r in test_results if r.success)
                
                # 成功基準チェック
                if success_rate >= 0.95 and avg_response_time < 2.0:  # 95%成功率、2秒以内
                    min_users = current_users
                    breakpoint_users = current_users
                else:
                    max_users = current_users
            else:
                max_users = current_users
        
        self.logger.info(f"Breakpoint found at approximately {breakpoint_users} users")
        
        # 最終的な結果として breakpoint での結果を返す
        self.results = test_results
    
    async def _run_custom_load(self, config: LoadTestConfig, session: aiohttp.ClientSession) -> LoadTestResult:
        """カスタム負荷パターン"""
        self.logger.info(f"Running custom load pattern")
        
        # カスタムロジックの実装
        # ここでは簡単な例として、設定に基づいた実行を行う
        tasks = []
        for i in range(config.users):
            user = VirtualUser(i, config, session)
            self.virtual_users.append(user)
            tasks.append(asyncio.create_task(user.run()))
        
        all_results = await asyncio.gather(*tasks)
        for user_results in all_results:
            self.results.extend(user_results)
    
    def _analyze_results(self, config: LoadTestConfig, duration: float, resource_report: Dict[str, Any]) -> LoadTestResult:
        """結果分析"""
        if not self.results:
            # 結果がない場合のデフォルト値
            return LoadTestResult(
                config=config,
                start_time=self.stats['start_time'],
                end_time=datetime.now(),
                duration=duration,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                error_rate=0.0,
                requests_per_second=0.0,
                average_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                percentiles={},
                response_time_distribution=[],
                error_distribution={},
                throughput=0.0,
                concurrent_users=[],
                resource_usage=resource_report,
                bottlenecks=[],
                recommendations=["No test data available"]
            )
        
        # 基本統計
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        # レスポンスタイム統計
        response_times = [r.duration for r in self.results if r.success]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # パーセンタイル計算
            sorted_times = sorted(response_times)
            percentiles = {
                '50th': np.percentile(sorted_times, 50),
                '90th': np.percentile(sorted_times, 90),
                '95th': np.percentile(sorted_times, 95),
                '99th': np.percentile(sorted_times, 99)
            }
        else:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
            percentiles = {'50th': 0, '90th': 0, '95th': 0, '99th': 0}
        
        # スループット計算
        total_bytes = sum(r.response_size for r in self.results)
        throughput = total_bytes / duration if duration > 0 else 0
        
        # RPS計算
        requests_per_second = total_requests / duration if duration > 0 else 0
        
        # エラー分布
        error_distribution = defaultdict(int)
        for r in self.results:
            if not r.success and r.error:
                error_distribution[r.error] += 1
        
        # 並行ユーザー数の時系列
        time_buckets = defaultdict(set)
        for r in self.results:
            bucket = int(r.start_time - self.results[0].start_time)
            time_buckets[bucket].add(r.user_id)
        
        concurrent_users = [len(users) for _, users in sorted(time_buckets.items())]
        
        # ボトルネック検出
        bottlenecks = self._detect_bottlenecks(
            response_times, 
            error_rate, 
            resource_report
        )
        
        # 推奨事項生成
        recommendations = self._generate_recommendations(
            avg_response_time,
            error_rate,
            percentiles,
            bottlenecks,
            resource_report
        )
        
        return LoadTestResult(
            config=config,
            start_time=self.stats['start_time'],
            end_time=datetime.now(),
            duration=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            error_rate=error_rate,
            requests_per_second=requests_per_second,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            percentiles=percentiles,
            response_time_distribution=response_times,
            error_distribution=dict(error_distribution),
            throughput=throughput,
            concurrent_users=concurrent_users,
            resource_usage=resource_report,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )
    
    def _detect_bottlenecks(self, 
                           response_times: List[float], 
                           error_rate: float,
                           resource_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ボトルネック検出"""
        bottlenecks = []
        
        # レスポンスタイムの急激な増加検出
        if len(response_times) > 10:
            # 移動平均で傾向分析
            window_size = min(10, len(response_times) // 10)
            moving_avg = []
            
            for i in range(window_size, len(response_times)):
                window = response_times[i-window_size:i]
                moving_avg.append(statistics.mean(window))
            
            if moving_avg:
                # 急激な増加を検出
                for i in range(1, len(moving_avg)):
                    if moving_avg[i] > moving_avg[i-1] * 1.5:  # 50%以上の増加
                        bottlenecks.append({
                            'type': 'response_time_degradation',
                            'severity': 'high',
                            'description': f'Response time increased by {(moving_avg[i]/moving_avg[i-1] - 1)*100:.1f}% at {i*window_size} requests',
                            'metric': 'response_time',
                            'value': moving_avg[i]
                        })
        
        # エラー率ベースのボトルネック
        if error_rate > 0.05:  # 5%以上のエラー
            severity = 'critical' if error_rate > 0.2 else 'high' if error_rate > 0.1 else 'medium'
            bottlenecks.append({
                'type': 'high_error_rate',
                'severity': severity,
                'description': f'Error rate of {error_rate*100:.1f}% exceeds acceptable threshold',
                'metric': 'error_rate',
                'value': error_rate
            })
        
        # リソースベースのボトルネック
        if resource_report:
            # CPU ボトルネック
            cpu_usage = resource_report.get('peak_usage', {}).get('cpu', 0)
            if cpu_usage > 80:
                bottlenecks.append({
                    'type': 'cpu_bottleneck',
                    'severity': 'critical' if cpu_usage > 95 else 'high',
                    'description': f'CPU usage peaked at {cpu_usage:.1f}%',
                    'metric': 'cpu_usage',
                    'value': cpu_usage
                })
            
            # メモリボトルネック
            memory_usage = resource_report.get('peak_usage', {}).get('memory', 0)
            if memory_usage > 85:
                bottlenecks.append({
                    'type': 'memory_bottleneck',
                    'severity': 'critical' if memory_usage > 95 else 'high',
                    'description': f'Memory usage peaked at {memory_usage:.1f}%',
                    'metric': 'memory_usage',
                    'value': memory_usage
                })
        
        return bottlenecks
    
    def _generate_recommendations(self,
                                 avg_response_time: float,
                                 error_rate: float,
                                 percentiles: Dict[str, float],
                                 bottlenecks: List[Dict[str, Any]],
                                 resource_report: Dict[str, Any]) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        # レスポンスタイムベースの推奨事項
        if avg_response_time > 3.0:
            recommendations.append("⚠️ Average response time exceeds 3 seconds. Consider:")
            recommendations.append("  • Implementing caching mechanisms")
            recommendations.append("  • Optimizing database queries")
            recommendations.append("  • Adding more application servers")
        
        if percentiles.get('95th', 0) > avg_response_time * 2:
            recommendations.append("📊 High response time variance detected. Consider:")
            recommendations.append("  • Investigating slow queries or operations")
            recommendations.append("  • Implementing request queuing")
            recommendations.append("  • Adding circuit breakers")
        
        # エラー率ベースの推奨事項
        if error_rate > 0.01:
            recommendations.append(f"❌ Error rate of {error_rate*100:.1f}% detected. Consider:")
            recommendations.append("  • Implementing retry mechanisms")
            recommendations.append("  • Increasing timeout values")
            recommendations.append("  • Scaling backend services")
        
        # ボトルネックベースの推奨事項
        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'cpu_bottleneck':
                recommendations.append("🔥 CPU bottleneck detected. Consider:")
                recommendations.append("  • Optimizing CPU-intensive operations")
                recommendations.append("  • Implementing horizontal scaling")
                recommendations.append("  • Using more efficient algorithms")
                
            elif bottleneck['type'] == 'memory_bottleneck':
                recommendations.append("💾 Memory bottleneck detected. Consider:")
                recommendations.append("  • Optimizing memory usage")
                recommendations.append("  • Implementing memory pooling")
                recommendations.append("  • Increasing available memory")
        
        # 一般的な推奨事項
        if not recommendations:
            recommendations.append("✅ System performed well under load")
            recommendations.append("Consider running tests with higher load to find limits")
        
        return recommendations
    
    async def _generate_report(self, result: LoadTestResult):
        """レポート生成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # HTMLレポート
        html_path = self.output_dir / f"load_test_report_{timestamp}.html"
        html_content = self._generate_html_report(result)
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        # JSONレポート
        json_path = self.output_dir / f"load_test_results_{timestamp}.json"
        json_data = {
            'config': {
                'name': result.config.name,
                'description': result.config.description,
                'load_pattern': result.config.load_pattern.value,
                'duration': result.config.duration,
                'users': result.config.users,
                'requests_per_user': result.config.requests_per_user
            },
            'summary': {
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'duration': result.duration,
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'error_rate': result.error_rate,
                'requests_per_second': result.requests_per_second,
                'average_response_time': result.average_response_time,
                'throughput_bytes_per_sec': result.throughput
            },
            'response_times': {
                'min': result.min_response_time,
                'max': result.max_response_time,
                'average': result.average_response_time,
                'percentiles': result.percentiles
            },
            'errors': result.error_distribution,
            'bottlenecks': result.bottlenecks,
            'recommendations': result.recommendations,
            'resource_usage': result.resource_usage
        }
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        self.logger.info(f"Reports generated: {html_path}, {json_path}")
    
    def _generate_html_report(self, result: LoadTestResult) -> str:
        """HTMLレポート生成"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Load Test Report - {result.config.name}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #d32f2f; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .metric-card {{ display: inline-block; margin: 10px; padding: 15px; background-color: #fff; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); min-width: 150px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #1976d2; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .section {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .bottleneck {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .bottleneck.critical {{ background-color: #ffebee; border-left: 5px solid #d32f2f; }}
        .bottleneck.high {{ background-color: #fff3e0; border-left: 5px solid #f57c00; }}
        .bottleneck.medium {{ background-color: #fff8e1; border-left: 5px solid #fbc02d; }}
        .recommendation {{ padding: 10px; margin: 5px 0; background-color: #e3f2fd; border-left: 5px solid #1976d2; border-radius: 5px; }}
        .chart {{ margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Load Test Report: {result.config.name}</h1>
        <p>{result.config.description}</p>
        <p>Test Pattern: {result.config.load_pattern.value} | Duration: {result.duration:.1f}s | Users: {result.config.users}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        <div style="text-align: center;">
            <div class="metric-card">
                <div class="metric-value">{result.total_requests:,}</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{result.requests_per_second:.1f}</div>
                <div class="metric-label">Requests/sec</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{result.average_response_time*1000:.0f}ms</div>
                <div class="metric-label">Avg Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: {'#d32f2f' if result.error_rate > 0.05 else '#388e3c'}">
                    {result.error_rate*100:.1f}%
                </div>
                <div class="metric-label">Error Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{result.throughput/1024/1024:.1f} MB/s</div>
                <div class="metric-label">Throughput</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>⏱️ Response Time Analysis</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value (ms)</th>
            </tr>
            <tr>
                <td>Minimum</td>
                <td>{result.min_response_time*1000:.1f}</td>
            </tr>
            <tr>
                <td>Average</td>
                <td>{result.average_response_time*1000:.1f}</td>
            </tr>
            <tr>
                <td>50th percentile (Median)</td>
                <td>{result.percentiles.get('50th', 0)*1000:.1f}</td>
            </tr>
            <tr>
                <td>90th percentile</td>
                <td>{result.percentiles.get('90th', 0)*1000:.1f}</td>
            </tr>
            <tr>
                <td>95th percentile</td>
                <td>{result.percentiles.get('95th', 0)*1000:.1f}</td>
            </tr>
            <tr>
                <td>99th percentile</td>
                <td>{result.percentiles.get('99th', 0)*1000:.1f}</td>
            </tr>
            <tr>
                <td>Maximum</td>
                <td>{result.max_response_time*1000:.1f}</td>
            </tr>
        </table>
    </div>
"""
        
        # レスポンスタイム分布グラフ
        if result.response_time_distribution:
            html += """
    <div class="section">
        <h2>📈 Response Time Distribution</h2>
        <div id="responseTimeChart" class="chart"></div>
    </div>
    
    <script>
        var responseData = {
            x: """ + json.dumps([r*1000 for r in result.response_time_distribution]) + """,
            type: 'histogram',
            name: 'Response Time (ms)',
            nbinsx: 50
        };
        
        var layout = {
            title: 'Response Time Distribution',
            xaxis: {title: 'Response Time (ms)'},
            yaxis: {title: 'Frequency'}
        };
        
        Plotly.newPlot('responseTimeChart', [responseData], layout);
    </script>
"""
        
        # エラー分布
        if result.error_distribution:
            html += f"""
    <div class="section">
        <h2>❌ Error Distribution</h2>
        <table>
            <tr>
                <th>Error Type</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""
            for error_type, count in result.error_distribution.items():
                percentage = (count / result.failed_requests * 100) if result.failed_requests > 0 else 0
                html += f"""
            <tr>
                <td>{error_type}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""
            html += """
        </table>
    </div>
"""
        
        # ボトルネック
        if result.bottlenecks:
            html += """
    <div class="section">
        <h2>🔍 Detected Bottlenecks</h2>
"""
            for bottleneck in result.bottlenecks:
                html += f"""
        <div class="bottleneck {bottleneck['severity']}">
            <strong>{bottleneck['type'].replace('_', ' ').title()}</strong><br>
            {bottleneck['description']}<br>
            <small>Metric: {bottleneck['metric']} = {bottleneck['value']}</small>
        </div>
"""
            html += """
    </div>
"""
        
        # 推奨事項
        if result.recommendations:
            html += """
    <div class="section">
        <h2>💡 Recommendations</h2>
"""
            for recommendation in result.recommendations:
                html += f"""
        <div class="recommendation">
            {recommendation}
        </div>
"""
            html += """
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def stop(self):
        """テスト停止"""
        self.stop_signal = True
        for user in self.virtual_users:
            user.stop()


# サンプル負荷テスト関数
async def sample_api_endpoint(payload: Any) -> Dict[str, Any]:
    """サンプルAPIエンドポイント（テスト用）"""
    # ランダムな遅延をシミュレート
    delay = random.uniform(0.1, 0.5)
    await asyncio.sleep(delay)
    
    # たまにエラーを返す
    if random.random() < 0.05:  # 5%の確率でエラー
        raise Exception("Random error occurred")
    
    return {
        'status': 'success',
        'data': payload,
        'timestamp': datetime.now().isoformat()
    }


# ファクトリー関数
def create_load_test_framework(config: Optional[Dict[str, Any]] = None) -> LoadTestFramework:
    """負荷テストフレームワーク作成"""
    return LoadTestFramework(config)


if __name__ == "__main__":
    # 負荷テスト実行例
    async def run_load_tests():
        framework = create_load_test_framework()
        
        # テスト設定
        configs = [
            LoadTestConfig(
                name="Constant Load Test",
                description="Test with constant 50 users",
                target_function=sample_api_endpoint,
                load_pattern=LoadPattern.CONSTANT,
                duration=60,
                users=50,
                requests_per_user=20,
                custom_payload={'test': 'data'}
            ),
            LoadTestConfig(
                name="Ramp-up Load Test",
                description="Gradually increase to 100 users",
                target_function=sample_api_endpoint,
                load_pattern=LoadPattern.RAMP_UP,
                duration=120,
                users=100,
                ramp_up_time=60,
                requests_per_user=10
            ),
            LoadTestConfig(
                name="Stress Test",
                description="Find system breaking point",
                target_function=sample_api_endpoint,
                load_pattern=LoadPattern.STRESS,
                duration=300,
                users=500,
                requests_per_user=50
            )
        ]
        
        # 各テスト実行
        for config in configs:
            print(f"\n🚀 Starting: {config.name}")
            print(f"   Pattern: {config.load_pattern.value}")
            print(f"   Users: {config.users}")
            print(f"   Duration: {config.duration}s")
            
            result = await framework.run_load_test(config)
            
            print(f"\n📊 Results:")
            print(f"   Total Requests: {result.total_requests:,}")
            print(f"   Success Rate: {(1-result.error_rate)*100:.1f}%")
            print(f"   Avg Response Time: {result.average_response_time*1000:.0f}ms")
            print(f"   95th Percentile: {result.percentiles.get('95th', 0)*1000:.0f}ms")
            print(f"   Throughput: {result.throughput/1024/1024:.2f} MB/s")
            
            if result.bottlenecks:
                print(f"\n⚠️  Bottlenecks Detected:")
                for bottleneck in result.bottlenecks:
                    print(f"   - {bottleneck['description']}")
            
            print("\n" + "="*50)
    
    # 実行
    asyncio.run(run_load_tests())