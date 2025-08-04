#!/usr/bin/env python3
"""
シュンスケ式リソースモニター - Ultimate ShunsukeModel Ecosystem

システムリソースの使用状況をリアルタイムで監視し、
異常検知とアラート発生を行う高精度監視システム
"""

import asyncio
import psutil
import logging
import time
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque, defaultdict
import numpy as np
import platform
import os
import threading
from enum import Enum
import socket
import aiohttp
from concurrent.futures import ThreadPoolExecutor


class ResourceType(Enum):
    """リソースタイプ"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"
    SYSTEM = "system"


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ResourceMetrics:
    """リソースメトリクス"""
    timestamp: datetime
    resource_type: ResourceType
    metrics: Dict[str, Any]
    usage_percent: float
    status: str = "normal"
    alerts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CPUMetrics:
    """CPUメトリクス"""
    usage_percent: float
    usage_per_core: List[float]
    frequency_current: float
    frequency_max: float
    temperature: Optional[float]
    load_average: Tuple[float, float, float]
    context_switches: int
    interrupts: int
    processes: int
    threads: int


@dataclass
class MemoryMetrics:
    """メモリメトリクス"""
    total: int
    available: int
    used: int
    free: int
    percent: float
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float
    cached: int
    buffers: int


@dataclass
class DiskMetrics:
    """ディスクメトリクス"""
    partitions: List[Dict[str, Any]]
    io_counters: Dict[str, Any]
    usage_per_partition: Dict[str, float]
    read_speed: float  # MB/s
    write_speed: float  # MB/s
    io_wait: float


@dataclass
class NetworkMetrics:
    """ネットワークメトリクス"""
    interfaces: Dict[str, Dict[str, Any]]
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    upload_speed: float  # MB/s
    download_speed: float  # MB/s
    connections: int
    connection_states: Dict[str, int]


@dataclass
class ProcessMetrics:
    """プロセスメトリクス"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_info: Dict[str, Any]
    num_threads: int
    status: str
    create_time: float
    io_counters: Optional[Dict[str, Any]]
    open_files: int
    connections: int


@dataclass
class Alert:
    """アラート"""
    timestamp: datetime
    resource_type: ResourceType
    alert_level: AlertLevel
    metric_name: str
    current_value: float
    threshold: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ResourceMonitor:
    """
    シュンスケ式リソースモニター
    
    機能:
    - リアルタイムリソース監視
    - 異常検知とアラート
    - トレンド分析
    - パフォーマンス予測
    - 自動最適化提案
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 監視設定
        self.monitoring_interval = self.config.get('interval', 1.0)  # 秒
        self.history_size = self.config.get('history_size', 3600)  # 1時間分
        
        # しきい値設定
        self.thresholds = self.config.get('thresholds', {
            'cpu': {'warning': 70, 'critical': 90},
            'memory': {'warning': 80, 'critical': 95},
            'disk': {'warning': 85, 'critical': 95},
            'network': {'warning': 80, 'critical': 95}
        })
        
        # メトリクス履歴
        self.metrics_history = {
            ResourceType.CPU: deque(maxlen=self.history_size),
            ResourceType.MEMORY: deque(maxlen=self.history_size),
            ResourceType.DISK: deque(maxlen=self.history_size),
            ResourceType.NETWORK: deque(maxlen=self.history_size),
            ResourceType.PROCESS: deque(maxlen=self.history_size)
        }
        
        # アラート管理
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_callbacks: List[Callable] = []
        
        # 監視タスク
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        self.monitor_lock = threading.Lock()
        
        # 統計情報
        self.stats = {
            'start_time': None,
            'total_alerts': 0,
            'alerts_by_level': defaultdict(int),
            'alerts_by_type': defaultdict(int)
        }
        
        # プロセスキャッシュ
        self.process_cache = {}
        self.process_cache_ttl = 5  # 秒
        
        # スレッドプール
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def start_monitoring(self):
        """監視開始"""
        with self.monitor_lock:
            if self.is_monitoring:
                self.logger.warning("Monitoring already started")
                return
            
            self.is_monitoring = True
            self.stats['start_time'] = datetime.now()
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """監視停止"""
        with self.monitor_lock:
            if not self.is_monitoring:
                return
            
            self.is_monitoring = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        while self.is_monitoring:
            try:
                # 各リソースの監視
                await asyncio.gather(
                    self._monitor_cpu(),
                    self._monitor_memory(),
                    self._monitor_disk(),
                    self._monitor_network(),
                    self._monitor_processes()
                )
                
                # アラートチェック
                await self._check_alerts()
                
                # トレンド分析
                await self._analyze_trends()
                
                # 待機
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _monitor_cpu(self):
        """CPU監視"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # CPU周波数
            cpu_freq = psutil.cpu_freq()
            freq_current = cpu_freq.current if cpu_freq else 0
            freq_max = cpu_freq.max if cpu_freq else 0
            
            # CPU温度（利用可能な場合）
            temperature = None
            try:
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # 最初のセンサーの温度を取得
                        for name, entries in temps.items():
                            if entries:
                                temperature = entries[0].current
                                break
            except:
                pass
            
            # ロードアベレージ
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            # コンテキストスイッチと割り込み
            cpu_stats = psutil.cpu_stats()
            
            # プロセス数とスレッド数
            process_count = len(psutil.pids())
            thread_count = threading.active_count()
            
            # メトリクス作成
            metrics = CPUMetrics(
                usage_percent=cpu_percent,
                usage_per_core=cpu_percent_per_core,
                frequency_current=freq_current,
                frequency_max=freq_max,
                temperature=temperature,
                load_average=load_avg,
                context_switches=cpu_stats.ctx_switches,
                interrupts=cpu_stats.interrupts,
                processes=process_count,
                threads=thread_count
            )
            
            # 履歴に追加
            resource_metrics = ResourceMetrics(
                timestamp=datetime.now(),
                resource_type=ResourceType.CPU,
                metrics=metrics.__dict__,
                usage_percent=cpu_percent
            )
            
            self.metrics_history[ResourceType.CPU].append(resource_metrics)
            
            # しきい値チェック
            await self._check_threshold(ResourceType.CPU, 'usage', cpu_percent)
            
        except Exception as e:
            self.logger.error(f"CPU monitoring error: {e}")
    
    async def _monitor_memory(self):
        """メモリ監視"""
        try:
            # 物理メモリ
            mem = psutil.virtual_memory()
            
            # スワップメモリ
            swap = psutil.swap_memory()
            
            # メトリクス作成
            metrics = MemoryMetrics(
                total=mem.total,
                available=mem.available,
                used=mem.used,
                free=mem.free,
                percent=mem.percent,
                swap_total=swap.total,
                swap_used=swap.used,
                swap_free=swap.free,
                swap_percent=swap.percent,
                cached=getattr(mem, 'cached', 0),
                buffers=getattr(mem, 'buffers', 0)
            )
            
            # 履歴に追加
            resource_metrics = ResourceMetrics(
                timestamp=datetime.now(),
                resource_type=ResourceType.MEMORY,
                metrics=metrics.__dict__,
                usage_percent=mem.percent
            )
            
            self.metrics_history[ResourceType.MEMORY].append(resource_metrics)
            
            # しきい値チェック
            await self._check_threshold(ResourceType.MEMORY, 'usage', mem.percent)
            await self._check_threshold(ResourceType.MEMORY, 'swap', swap.percent)
            
        except Exception as e:
            self.logger.error(f"Memory monitoring error: {e}")
    
    async def _monitor_disk(self):
        """ディスク監視"""
        try:
            # ディスクパーティション
            partitions = []
            usage_per_partition = {}
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partition_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                    partitions.append(partition_info)
                    usage_per_partition[partition.device] = usage.percent
                except:
                    continue
            
            # I/Oカウンター
            io_counters = psutil.disk_io_counters()
            io_dict = {
                'read_count': io_counters.read_count,
                'write_count': io_counters.write_count,
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes,
                'read_time': io_counters.read_time,
                'write_time': io_counters.write_time
            } if io_counters else {}
            
            # I/O速度計算（前回との差分）
            read_speed = 0
            write_speed = 0
            
            if ResourceType.DISK in self.metrics_history and self.metrics_history[ResourceType.DISK]:
                last_metrics = self.metrics_history[ResourceType.DISK][-1]
                if 'io_counters' in last_metrics.metrics:
                    last_io = last_metrics.metrics['io_counters']
                    time_diff = (datetime.now() - last_metrics.timestamp).total_seconds()
                    
                    if time_diff > 0 and io_counters:
                        read_speed = (io_counters.read_bytes - last_io.get('read_bytes', 0)) / time_diff / 1024 / 1024
                        write_speed = (io_counters.write_bytes - last_io.get('write_bytes', 0)) / time_diff / 1024 / 1024
            
            # メトリクス作成
            metrics = DiskMetrics(
                partitions=partitions,
                io_counters=io_dict,
                usage_per_partition=usage_per_partition,
                read_speed=max(0, read_speed),
                write_speed=max(0, write_speed),
                io_wait=0  # TODO: プラットフォーム固有の実装
            )
            
            # 最大使用率を計算
            max_usage = max(usage_per_partition.values()) if usage_per_partition else 0
            
            # 履歴に追加
            resource_metrics = ResourceMetrics(
                timestamp=datetime.now(),
                resource_type=ResourceType.DISK,
                metrics=metrics.__dict__,
                usage_percent=max_usage
            )
            
            self.metrics_history[ResourceType.DISK].append(resource_metrics)
            
            # しきい値チェック（各パーティション）
            for device, usage in usage_per_partition.items():
                await self._check_threshold(ResourceType.DISK, f'usage_{device}', usage)
            
        except Exception as e:
            self.logger.error(f"Disk monitoring error: {e}")
    
    async def _monitor_network(self):
        """ネットワーク監視"""
        try:
            # ネットワークインターフェース
            interfaces = {}
            for iface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    'addresses': []
                }
                for addr in addrs:
                    interface_info['addresses'].append({
                        'family': addr.family.name,
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                interfaces[iface] = interface_info
            
            # I/Oカウンター
            net_io = psutil.net_io_counters()
            
            # 接続情報
            connections = psutil.net_connections()
            connection_states = defaultdict(int)
            for conn in connections:
                if conn.status:
                    connection_states[conn.status] += 1
            
            # 速度計算
            upload_speed = 0
            download_speed = 0
            
            if ResourceType.NETWORK in self.metrics_history and self.metrics_history[ResourceType.NETWORK]:
                last_metrics = self.metrics_history[ResourceType.NETWORK][-1]
                time_diff = (datetime.now() - last_metrics.timestamp).total_seconds()
                
                if time_diff > 0:
                    last_sent = last_metrics.metrics.get('bytes_sent', 0)
                    last_recv = last_metrics.metrics.get('bytes_recv', 0)
                    
                    upload_speed = (net_io.bytes_sent - last_sent) / time_diff / 1024 / 1024
                    download_speed = (net_io.bytes_recv - last_recv) / time_diff / 1024 / 1024
            
            # メトリクス作成
            metrics = NetworkMetrics(
                interfaces=interfaces,
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
                upload_speed=max(0, upload_speed),
                download_speed=max(0, download_speed),
                connections=len(connections),
                connection_states=dict(connection_states)
            )
            
            # ネットワーク使用率の推定（簡易版）
            # 仮定: 1Gbps = 125MB/s を基準
            max_bandwidth = 125  # MB/s
            network_usage = ((upload_speed + download_speed) / max_bandwidth) * 100
            
            # 履歴に追加
            resource_metrics = ResourceMetrics(
                timestamp=datetime.now(),
                resource_type=ResourceType.NETWORK,
                metrics=metrics.__dict__,
                usage_percent=min(100, network_usage)
            )
            
            self.metrics_history[ResourceType.NETWORK].append(resource_metrics)
            
        except Exception as e:
            self.logger.error(f"Network monitoring error: {e}")
    
    async def _monitor_processes(self):
        """プロセス監視"""
        try:
            # 上位のプロセスを取得
            top_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    
                    # CPU使用率が高いプロセスを記録
                    if pinfo['cpu_percent'] > 5 or pinfo['memory_percent'] > 5:
                        # 詳細情報取得
                        process_metrics = ProcessMetrics(
                            pid=pinfo['pid'],
                            name=pinfo['name'],
                            cpu_percent=pinfo['cpu_percent'],
                            memory_percent=pinfo['memory_percent'],
                            memory_info=proc.memory_info()._asdict(),
                            num_threads=proc.num_threads(),
                            status=proc.status(),
                            create_time=proc.create_time(),
                            io_counters=proc.io_counters()._asdict() if hasattr(proc, 'io_counters') else None,
                            open_files=len(proc.open_files()) if hasattr(proc, 'open_files') else 0,
                            connections=len(proc.connections()) if hasattr(proc, 'connections') else 0
                        )
                        
                        top_processes.append(process_metrics.__dict__)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # CPU使用率でソート
            top_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_processes = top_processes[:10]  # 上位10プロセス
            
            # 履歴に追加
            resource_metrics = ResourceMetrics(
                timestamp=datetime.now(),
                resource_type=ResourceType.PROCESS,
                metrics={'top_processes': top_processes},
                usage_percent=0  # プロセスの場合は個別に管理
            )
            
            self.metrics_history[ResourceType.PROCESS].append(resource_metrics)
            
        except Exception as e:
            self.logger.error(f"Process monitoring error: {e}")
    
    async def _check_threshold(self, resource_type: ResourceType, metric_name: str, current_value: float):
        """しきい値チェック"""
        try:
            thresholds = self.thresholds.get(resource_type.value, {})
            
            # アラートキー
            alert_key = f"{resource_type.value}_{metric_name}"
            
            # 現在のアラートレベル判定
            alert_level = None
            threshold_value = None
            
            if current_value >= thresholds.get('critical', 100):
                alert_level = AlertLevel.CRITICAL
                threshold_value = thresholds['critical']
            elif current_value >= thresholds.get('warning', 100):
                alert_level = AlertLevel.WARNING
                threshold_value = thresholds['warning']
            
            # アラート処理
            if alert_level:
                if alert_key not in self.active_alerts:
                    # 新規アラート
                    alert = Alert(
                        timestamp=datetime.now(),
                        resource_type=resource_type,
                        alert_level=alert_level,
                        metric_name=metric_name,
                        current_value=current_value,
                        threshold=threshold_value,
                        message=f"{resource_type.value} {metric_name} exceeded {alert_level.value} threshold: {current_value:.1f}% (threshold: {threshold_value}%)",
                        details={
                            'resource': resource_type.value,
                            'metric': metric_name,
                            'value': current_value,
                            'threshold': threshold_value
                        }
                    )
                    
                    self.active_alerts[alert_key] = alert
                    self.alert_history.append(alert)
                    self.stats['total_alerts'] += 1
                    self.stats['alerts_by_level'][alert_level.value] += 1
                    self.stats['alerts_by_type'][resource_type.value] += 1
                    
                    # コールバック実行
                    await self._trigger_alert_callbacks(alert)
                    
                    self.logger.warning(alert.message)
                else:
                    # 既存アラートの更新
                    existing_alert = self.active_alerts[alert_key]
                    existing_alert.current_value = current_value
                    
                    # レベルが上がった場合
                    if alert_level.value > existing_alert.alert_level.value:
                        existing_alert.alert_level = alert_level
                        existing_alert.message = f"{resource_type.value} {metric_name} escalated to {alert_level.value}: {current_value:.1f}%"
                        await self._trigger_alert_callbacks(existing_alert)
                        self.logger.warning(existing_alert.message)
            else:
                # しきい値以下の場合、アラート解除
                if alert_key in self.active_alerts:
                    alert = self.active_alerts[alert_key]
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    del self.active_alerts[alert_key]
                    
                    self.logger.info(f"Alert resolved: {alert_key}")
            
        except Exception as e:
            self.logger.error(f"Threshold check error: {e}")
    
    async def _check_alerts(self):
        """アラート状態チェック"""
        try:
            # 長時間継続しているアラートの確認
            for alert_key, alert in list(self.active_alerts.items()):
                duration = datetime.now() - alert.timestamp
                
                # 30分以上継続している場合はエスカレート
                if duration > timedelta(minutes=30) and alert.alert_level != AlertLevel.EMERGENCY:
                    alert.alert_level = AlertLevel.EMERGENCY
                    alert.message = f"EMERGENCY: {alert.message} (continuing for {duration})"
                    await self._trigger_alert_callbacks(alert)
                    self.logger.error(alert.message)
            
        except Exception as e:
            self.logger.error(f"Alert check error: {e}")
    
    async def _analyze_trends(self):
        """トレンド分析"""
        try:
            # 各リソースタイプのトレンド分析
            for resource_type, history in self.metrics_history.items():
                if len(history) < 10:
                    continue
                
                # 最近のデータ
                recent_data = list(history)[-60:]  # 直近1分
                
                if resource_type in [ResourceType.CPU, ResourceType.MEMORY, ResourceType.DISK]:
                    # 使用率のトレンド
                    usage_values = [m.usage_percent for m in recent_data]
                    
                    if len(usage_values) >= 10:
                        # 移動平均
                        avg_usage = np.mean(usage_values)
                        
                        # トレンド（増加/減少）
                        trend = np.polyfit(range(len(usage_values)), usage_values, 1)[0]
                        
                        # 急激な増加を検出
                        if trend > 1.0:  # 1%/秒以上の増加
                            self.logger.warning(f"{resource_type.value} usage increasing rapidly: {trend:.2f}%/s")
                            
                            # 予測：このまま続くと何分後に100%に達するか
                            if avg_usage < 100:
                                minutes_to_full = (100 - avg_usage) / (trend * 60)
                                if minutes_to_full < 10:
                                    self.logger.warning(f"{resource_type.value} will reach 100% in {minutes_to_full:.1f} minutes")
            
        except Exception as e:
            self.logger.error(f"Trend analysis error: {e}")
    
    async def _trigger_alert_callbacks(self, alert: Alert):
        """アラートコールバック実行"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    await asyncio.get_event_loop().run_in_executor(self.executor, callback, alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """アラートコールバック追加"""
        self.alert_callbacks.append(callback)
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """現在のメトリクス取得"""
        current = {}
        
        for resource_type, history in self.metrics_history.items():
            if history:
                latest = history[-1]
                current[resource_type.value] = {
                    'timestamp': latest.timestamp.isoformat(),
                    'usage_percent': latest.usage_percent,
                    'status': latest.status,
                    'metrics': latest.metrics
                }
        
        return current
    
    async def get_metrics_history(self, resource_type: ResourceType, duration: timedelta = None) -> List[Dict[str, Any]]:
        """メトリクス履歴取得"""
        history = self.metrics_history.get(resource_type, [])
        
        if duration:
            cutoff_time = datetime.now() - duration
            filtered_history = [m for m in history if m.timestamp > cutoff_time]
        else:
            filtered_history = list(history)
        
        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'usage_percent': m.usage_percent,
                'metrics': m.metrics
            }
            for m in filtered_history
        ]
    
    async def get_resource_report(self) -> Dict[str, Any]:
        """リソースレポート生成"""
        try:
            # 現在のメトリクス
            current_metrics = await self.get_current_metrics()
            
            # 統計情報
            uptime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
            
            # 各リソースの平均使用率
            average_usage = {}
            peak_usage = {}
            
            for resource_type, history in self.metrics_history.items():
                if history and resource_type != ResourceType.PROCESS:
                    usage_values = [m.usage_percent for m in history]
                    average_usage[resource_type.value] = np.mean(usage_values)
                    peak_usage[resource_type.value] = max(usage_values)
            
            return {
                'status': 'monitoring' if self.is_monitoring else 'stopped',
                'uptime': str(uptime),
                'current_metrics': current_metrics,
                'average_usage': average_usage,
                'peak_usage': peak_usage,
                'active_alerts': len(self.active_alerts),
                'total_alerts': self.stats['total_alerts'],
                'alerts_by_level': dict(self.stats['alerts_by_level']),
                'alerts_by_type': dict(self.stats['alerts_by_type']),
                'system_info': {
                    'platform': platform.platform(),
                    'cpu_count': psutil.cpu_count(),
                    'total_memory': psutil.virtual_memory().total,
                    'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Resource report generation error: {e}")
            return {'error': str(e)}
    
    async def export_metrics(self, output_path: Path, duration: timedelta = None) -> bool:
        """メトリクスエクスポート"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'report': await self.get_resource_report(),
                'metrics_history': {}
            }
            
            # 各リソースの履歴
            for resource_type in ResourceType:
                history = await self.get_metrics_history(resource_type, duration)
                export_data['metrics_history'][resource_type.value] = history
            
            # アラート履歴
            export_data['alert_history'] = [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'resource_type': alert.resource_type.value,
                    'alert_level': alert.alert_level.value,
                    'metric_name': alert.metric_name,
                    'current_value': alert.current_value,
                    'threshold': alert.threshold,
                    'message': alert.message,
                    'resolved': alert.resolved,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                for alert in self.alert_history
            ]
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Metrics exported to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Metrics export error: {e}")
            return False
    
    def __del__(self):
        """クリーンアップ"""
        self.executor.shutdown(wait=False)


# リソースモニターのファクトリー関数
def create_resource_monitor(config: Optional[Dict[str, Any]] = None) -> ResourceMonitor:
    """リソースモニター作成"""
    return ResourceMonitor(config)


if __name__ == "__main__":
    # テスト実行
    async def test_resource_monitor():
        # 設定
        config = {
            'interval': 1.0,
            'thresholds': {
                'cpu': {'warning': 50, 'critical': 80},
                'memory': {'warning': 60, 'critical': 90},
                'disk': {'warning': 70, 'critical': 90}
            }
        }
        
        monitor = create_resource_monitor(config)
        
        # アラートコールバック
        def alert_handler(alert: Alert):
            print(f"🚨 ALERT: {alert.message}")
        
        monitor.add_alert_callback(alert_handler)
        
        # 監視開始
        print("Starting resource monitoring...")
        await monitor.start_monitoring()
        
        # 10秒間監視
        await asyncio.sleep(10)
        
        # レポート生成
        report = await monitor.get_resource_report()
        print("\nResource Report:")
        print(json.dumps(report, indent=2))
        
        # メトリクスエクスポート
        export_path = Path.home() / '.claude' / 'monitoring' / 'resource_metrics.json'
        await monitor.export_metrics(export_path)
        print(f"\nMetrics exported to: {export_path}")
        
        # 監視停止
        await monitor.stop_monitoring()
        print("Resource monitoring stopped")
    
    asyncio.run(test_resource_monitor())