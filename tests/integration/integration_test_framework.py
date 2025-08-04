#!/usr/bin/env python3
"""
シュンスケ式統合テストフレームワーク - Ultimate ShunsukeModel Ecosystem

システム全体の統合テストを包括的に実行し、
コンポーネント間の連携を検証する高度なテストフレームワーク
"""

import asyncio
import pytest
import logging
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Set, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import tempfile
import shutil
import sys
import os
from enum import Enum
import yaml
import subprocess
from contextlib import asynccontextmanager
import aiohttp
import psutil


# テスト対象モジュールのインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.command_tower.command_tower import CommandTower, CommandContext
from orchestration.coordinator.agent_coordinator import AgentCoordinator
from orchestration.communication.communication_protocol import CommunicationProtocol, MessageType
from tools.quality_analyzer.quality_guardian import QualityGuardian
from tools.doc_synthesizer.documentation_synthesizer import DocumentationSynthesizer, DocumentationConfig
from tools.performance_suite import (
    create_performance_profiler,
    create_resource_monitor,
    create_optimization_engine,
    create_benchmark_runner
)


class TestLevel(Enum):
    """テストレベル"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestStatus(Enum):
    """テストステータス"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """テストケース"""
    test_id: str
    name: str
    description: str
    test_level: TestLevel
    module_under_test: str
    dependencies: List[str] = field(default_factory=list)
    setup_function: Optional[Callable] = None
    test_function: Callable = None
    teardown_function: Optional[Callable] = None
    expected_results: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 300.0  # 5分
    retry_count: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """テスト結果"""
    test_case: TestCase
    status: TestStatus
    start_time: datetime
    end_time: datetime
    duration: float
    actual_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    artifacts: List[Path] = field(default_factory=list)


@dataclass
class TestSuite:
    """テストスイート"""
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase]
    test_level: TestLevel
    parallel_execution: bool = False
    stop_on_failure: bool = False
    tags: List[str] = field(default_factory=list)


class IntegrationTestFramework:
    """
    シュンスケ式統合テストフレームワーク
    
    機能:
    - モジュール間統合テスト
    - エンドツーエンドテスト
    - パフォーマンステスト
    - セキュリティテスト
    - 自動テストレポート生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # テスト設定
        self.test_output_dir = Path(self.config.get('output_dir', './test_results'))
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # テスト環境
        self.test_env_dir = Path(tempfile.mkdtemp(prefix="shunsuke_test_"))
        self.components = {}
        
        # テスト結果管理
        self.test_results: List[TestResult] = []
        self.test_suites: Dict[str, TestSuite] = {}
        
        # メトリクス収集
        self.performance_profiler = None
        self.resource_monitor = None
        
        # 統計情報
        self.stats = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'total_duration': 0.0
        }
    
    async def setup_test_environment(self):
        """テスト環境セットアップ"""
        try:
            self.logger.info("Setting up test environment...")
            
            # パフォーマンス監視ツール初期化
            self.performance_profiler = create_performance_profiler()
            self.resource_monitor = create_resource_monitor()
            
            # リソース監視開始
            await self.resource_monitor.start_monitoring()
            
            # テスト用ディレクトリ構造作成
            (self.test_env_dir / "logs").mkdir(exist_ok=True)
            (self.test_env_dir / "artifacts").mkdir(exist_ok=True)
            (self.test_env_dir / "temp").mkdir(exist_ok=True)
            
            self.logger.info(f"Test environment created at: {self.test_env_dir}")
            
        except Exception as e:
            self.logger.error(f"Test environment setup failed: {e}")
            raise
    
    async def teardown_test_environment(self):
        """テスト環境クリーンアップ"""
        try:
            self.logger.info("Tearing down test environment...")
            
            # リソース監視停止
            if self.resource_monitor:
                await self.resource_monitor.stop_monitoring()
            
            # コンポーネントのシャットダウン
            for component_name, component in self.components.items():
                if hasattr(component, 'shutdown'):
                    await component.shutdown()
            
            # テスト環境削除
            if self.test_env_dir.exists():
                shutil.rmtree(self.test_env_dir)
            
        except Exception as e:
            self.logger.error(f"Test environment teardown error: {e}")
    
    async def initialize_components(self) -> Dict[str, Any]:
        """コンポーネント初期化"""
        try:
            # Command Tower
            command_tower = CommandTower()
            await command_tower.initialize()
            self.components['command_tower'] = command_tower
            
            # Agent Coordinator
            agent_coordinator = AgentCoordinator()
            await agent_coordinator.initialize()
            self.components['agent_coordinator'] = agent_coordinator
            
            # Communication Protocol
            comm_protocol = CommunicationProtocol("test_system", {})
            await comm_protocol.initialize()
            self.components['comm_protocol'] = comm_protocol
            
            # Quality Guardian
            quality_guardian = QualityGuardian({
                'project_path': self.test_env_dir
            })
            self.components['quality_guardian'] = quality_guardian
            
            # Documentation Synthesizer
            doc_config = DocumentationConfig(
                project_path=self.test_env_dir,
                output_path=self.test_env_dir / "docs"
            )
            doc_synthesizer = DocumentationSynthesizer(doc_config)
            await doc_synthesizer.initialize()
            self.components['doc_synthesizer'] = doc_synthesizer
            
            self.logger.info("All components initialized successfully")
            return self.components
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise
    
    def create_test_case(self,
                        test_id: str,
                        name: str,
                        test_function: Callable,
                        **kwargs) -> TestCase:
        """テストケース作成"""
        return TestCase(
            test_id=test_id,
            name=name,
            description=kwargs.get('description', ''),
            test_level=kwargs.get('test_level', TestLevel.INTEGRATION),
            module_under_test=kwargs.get('module', 'unknown'),
            dependencies=kwargs.get('dependencies', []),
            setup_function=kwargs.get('setup'),
            test_function=test_function,
            teardown_function=kwargs.get('teardown'),
            expected_results=kwargs.get('expected', {}),
            timeout=kwargs.get('timeout', 300.0),
            retry_count=kwargs.get('retry', 0),
            tags=kwargs.get('tags', [])
        )
    
    def create_test_suite(self,
                         suite_id: str,
                         name: str,
                         test_cases: List[TestCase],
                         **kwargs) -> TestSuite:
        """テストスイート作成"""
        suite = TestSuite(
            suite_id=suite_id,
            name=name,
            description=kwargs.get('description', ''),
            test_cases=test_cases,
            test_level=kwargs.get('test_level', TestLevel.INTEGRATION),
            parallel_execution=kwargs.get('parallel', False),
            stop_on_failure=kwargs.get('stop_on_failure', False),
            tags=kwargs.get('tags', [])
        )
        
        self.test_suites[suite_id] = suite
        return suite
    
    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """単一テストケース実行"""
        start_time = datetime.now()
        result = TestResult(
            test_case=test_case,
            status=TestStatus.RUNNING,
            start_time=start_time,
            end_time=start_time,
            duration=0.0
        )
        
        # ログキャプチャ設定
        log_capture = []
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        
        class LogCapture(logging.Handler):
            def emit(self, record):
                log_capture.append(self.format(record))
        
        capture_handler = LogCapture()
        self.logger.addHandler(capture_handler)
        
        try:
            self.logger.info(f"Running test: {test_case.name}")
            
            # セットアップ実行
            if test_case.setup_function:
                await self._run_with_timeout(
                    test_case.setup_function(self.components),
                    test_case.timeout / 3
                )
            
            # パフォーマンスプロファイリング開始
            profile_id = f"test_{test_case.test_id}"
            if self.performance_profiler:
                await self.performance_profiler.start_profile(profile_id, test_case.name)
            
            # テスト実行
            test_result = await self._run_with_timeout(
                test_case.test_function(self.components),
                test_case.timeout
            )
            
            # パフォーマンスプロファイリング終了
            if self.performance_profiler:
                profile_result = await self.performance_profiler.stop_profile(profile_id)
                result.performance_metrics = {
                    'execution_time': profile_result.total_time,
                    'memory_usage': profile_result.memory_usage,
                    'cpu_percent': profile_result.cpu_percent
                }
            
            # リソース使用状況取得
            if self.resource_monitor:
                current_metrics = await self.resource_monitor.get_current_metrics()
                result.resource_usage = current_metrics
            
            # 結果検証
            result.actual_results = test_result if isinstance(test_result, dict) else {'result': test_result}
            
            if test_case.expected_results:
                if self._validate_results(result.actual_results, test_case.expected_results):
                    result.status = TestStatus.PASSED
                else:
                    result.status = TestStatus.FAILED
                    result.error_message = "Actual results do not match expected results"
            else:
                result.status = TestStatus.PASSED
            
            # ティアダウン実行
            if test_case.teardown_function:
                await self._run_with_timeout(
                    test_case.teardown_function(self.components),
                    test_case.timeout / 3
                )
            
        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.error_message = f"Test timed out after {test_case.timeout}s"
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.stack_trace = self._get_stack_trace()
            
        finally:
            # 終了時刻と実行時間
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            # ログ保存
            result.logs = log_capture
            self.logger.removeHandler(capture_handler)
            
            # 統計更新
            self._update_statistics(result)
            
            # 結果保存
            self.test_results.append(result)
            
            self.logger.info(f"Test completed: {test_case.name} - {result.status.value}")
        
        return result
    
    async def run_test_suite(self, suite: TestSuite) -> List[TestResult]:
        """テストスイート実行"""
        self.logger.info(f"Running test suite: {suite.name}")
        results = []
        
        try:
            if suite.parallel_execution:
                # 並列実行
                tasks = []
                for test_case in suite.test_cases:
                    task = asyncio.create_task(self.run_test_case(test_case))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 例外処理
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_result = TestResult(
                            test_case=suite.test_cases[i],
                            status=TestStatus.ERROR,
                            start_time=datetime.now(),
                            end_time=datetime.now(),
                            duration=0.0,
                            error_message=str(result)
                        )
                        results[i] = error_result
            else:
                # 順次実行
                for test_case in suite.test_cases:
                    result = await self.run_test_case(test_case)
                    results.append(result)
                    
                    # 失敗時の停止判定
                    if suite.stop_on_failure and result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                        self.logger.warning(f"Stopping test suite due to failure: {result.test_case.name}")
                        break
            
            return results
            
        except Exception as e:
            self.logger.error(f"Test suite execution error: {e}")
            raise
    
    async def _run_with_timeout(self, coro, timeout: float):
        """タイムアウト付きコルーチン実行"""
        return await asyncio.wait_for(coro, timeout=timeout)
    
    def _validate_results(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """結果検証"""
        try:
            for key, expected_value in expected.items():
                if key not in actual:
                    self.logger.warning(f"Missing expected key: {key}")
                    return False
                
                actual_value = actual[key]
                
                # 型チェック
                if type(actual_value) != type(expected_value):
                    self.logger.warning(f"Type mismatch for {key}: {type(actual_value)} != {type(expected_value)}")
                    return False
                
                # 値チェック
                if isinstance(expected_value, dict):
                    if not self._validate_results(actual_value, expected_value):
                        return False
                elif isinstance(expected_value, (list, tuple)):
                    if len(actual_value) != len(expected_value):
                        return False
                    for a, e in zip(actual_value, expected_value):
                        if a != e:
                            return False
                else:
                    if actual_value != expected_value:
                        self.logger.warning(f"Value mismatch for {key}: {actual_value} != {expected_value}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Result validation error: {e}")
            return False
    
    def _get_stack_trace(self) -> str:
        """スタックトレース取得"""
        import traceback
        return traceback.format_exc()
    
    def _update_statistics(self, result: TestResult):
        """統計情報更新"""
        self.stats['total_tests'] += 1
        self.stats['total_duration'] += result.duration
        
        if result.status == TestStatus.PASSED:
            self.stats['passed'] += 1
        elif result.status == TestStatus.FAILED:
            self.stats['failed'] += 1
        elif result.status == TestStatus.SKIPPED:
            self.stats['skipped'] += 1
        elif result.status == TestStatus.ERROR:
            self.stats['errors'] += 1
    
    async def generate_test_report(self) -> Path:
        """テストレポート生成"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.test_output_dir / f"test_report_{timestamp}.html"
            
            # HTML レポート生成
            html_content = self._generate_html_report()
            
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            # JSON レポート生成
            json_path = self.test_output_dir / f"test_results_{timestamp}.json"
            json_data = self._generate_json_report()
            
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            self.logger.info(f"Test reports generated: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            raise
    
    def _generate_html_report(self) -> str:
        """HTMLレポート生成"""
        passed_rate = (self.stats['passed'] / max(self.stats['total_tests'], 1)) * 100
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Integration Test Report - Ultimate ShunsukeModel Ecosystem</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .test-case {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .passed {{ border-left: 5px solid #27ae60; }}
        .failed {{ border-left: 5px solid #e74c3c; }}
        .error {{ border-left: 5px solid #f39c12; }}
        .skipped {{ border-left: 5px solid #95a5a6; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #34495e; color: white; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #ecf0f1; border-radius: 5px; }}
        .chart {{ margin: 20px 0; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Integration Test Report</h1>
        <p>Ultimate ShunsukeModel Ecosystem - Comprehensive Testing</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        <div class="metric">Total Tests: <strong>{self.stats['total_tests']}</strong></div>
        <div class="metric" style="background-color: #d4edda;">Passed: <strong>{self.stats['passed']}</strong></div>
        <div class="metric" style="background-color: #f8d7da;">Failed: <strong>{self.stats['failed']}</strong></div>
        <div class="metric" style="background-color: #fff3cd;">Errors: <strong>{self.stats['errors']}</strong></div>
        <div class="metric">Pass Rate: <strong>{passed_rate:.1f}%</strong></div>
        <div class="metric">Total Duration: <strong>{self.stats['total_duration']:.2f}s</strong></div>
    </div>
    
    <div class="summary">
        <h2>📈 Performance Metrics</h2>
        <table>
            <tr>
                <th>Test Name</th>
                <th>Duration (s)</th>
                <th>Memory Usage (MB)</th>
                <th>CPU Usage (%)</th>
            </tr>
"""
        
        # テスト結果の追加
        for result in self.test_results:
            memory_mb = result.performance_metrics.get('memory_usage', 0) / 1024 / 1024
            cpu_percent = result.performance_metrics.get('cpu_percent', 0)
            
            html += f"""
            <tr>
                <td>{result.test_case.name}</td>
                <td>{result.duration:.3f}</td>
                <td>{memory_mb:.1f}</td>
                <td>{cpu_percent:.1f}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
    
    <h2>🔍 Detailed Test Results</h2>
"""
        
        # 詳細結果
        for result in self.test_results:
            status_class = result.status.value.lower()
            status_icon = {
                TestStatus.PASSED: "✅",
                TestStatus.FAILED: "❌",
                TestStatus.ERROR: "⚠️",
                TestStatus.SKIPPED: "⏭️"
            }.get(result.status, "❓")
            
            html += f"""
    <div class="test-case {status_class}">
        <h3>{status_icon} {result.test_case.name}</h3>
        <p><strong>Status:</strong> {result.status.value}</p>
        <p><strong>Duration:</strong> {result.duration:.3f}s</p>
        <p><strong>Module:</strong> {result.test_case.module_under_test}</p>
"""
            
            if result.error_message:
                html += f"""
        <p><strong>Error:</strong></p>
        <pre>{result.error_message}</pre>
"""
            
            if result.stack_trace:
                html += f"""
        <details>
            <summary>Stack Trace</summary>
            <pre>{result.stack_trace}</pre>
        </details>
"""
            
            if result.logs:
                html += f"""
        <details>
            <summary>Logs ({len(result.logs)} lines)</summary>
            <pre>{chr(10).join(result.logs[-20:])}</pre>
        </details>
"""
            
            html += """
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _generate_json_report(self) -> Dict[str, Any]:
        """JSONレポート生成"""
        return {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'framework_version': '1.0.0',
                'test_environment': str(self.test_env_dir)
            },
            'summary': self.stats,
            'test_results': [
                {
                    'test_id': result.test_case.test_id,
                    'name': result.test_case.name,
                    'status': result.status.value,
                    'duration': result.duration,
                    'start_time': result.start_time.isoformat(),
                    'end_time': result.end_time.isoformat(),
                    'error_message': result.error_message,
                    'performance_metrics': result.performance_metrics,
                    'resource_usage': result.resource_usage
                }
                for result in self.test_results
            ],
            'test_suites': {
                suite_id: {
                    'name': suite.name,
                    'test_count': len(suite.test_cases),
                    'test_level': suite.test_level.value,
                    'tags': suite.tags
                }
                for suite_id, suite in self.test_suites.items()
            }
        }
    
    async def cleanup(self):
        """クリーンアップ"""
        await self.teardown_test_environment()


# 標準統合テストケース
async def test_command_tower_integration(components: Dict[str, Any]) -> Dict[str, Any]:
    """Command Tower統合テスト"""
    command_tower = components['command_tower']
    
    # コマンド実行テスト
    context = CommandContext(user_id="test_user")
    result = await command_tower.execute_command_sequence(
        "analyze_project",
        context=context
    )
    
    return {
        'command_executed': result.get('status') == 'completed',
        'execution_time': result.get('execution_time', 0),
        'steps_completed': len(result.get('completed_steps', []))
    }


async def test_agent_coordination(components: Dict[str, Any]) -> Dict[str, Any]:
    """エージェント協調テスト"""
    coordinator = components['agent_coordinator']
    
    # マルチエージェントタスク実行
    task_spec = {
        'task_type': 'code_analysis',
        'target': 'test_file.py',
        'agents_required': ['scout', 'quality_guardian']
    }
    
    result = await coordinator.execute_task_with_agents(
        task_id="test_task_001",
        agents=task_spec['agents_required'],
        task_spec=task_spec
    )
    
    return {
        'task_completed': result.get('status') == 'completed',
        'agents_participated': len(result.get('agent_results', {})),
        'coordination_time': result.get('coordination_time', 0)
    }


async def test_quality_analysis_integration(components: Dict[str, Any]) -> Dict[str, Any]:
    """品質分析統合テスト"""
    quality_guardian = components['quality_guardian']
    
    # テストプロジェクト分析
    quality_report = await quality_guardian.analyze_project_quality(
        Path(components['test_env_dir'])
    )
    
    return {
        'analysis_completed': quality_report is not None,
        'issues_found': len(quality_report.issues) if quality_report else 0,
        'quality_score': quality_report.overall_score if quality_report else 0
    }


async def test_documentation_generation(components: Dict[str, Any]) -> Dict[str, Any]:
    """ドキュメント生成統合テスト"""
    doc_synthesizer = components['doc_synthesizer']
    
    # ドキュメント生成
    result = await doc_synthesizer.synthesize_complete_documentation()
    
    return {
        'generation_completed': result.get('status') == 'completed',
        'documents_generated': result.get('documents_generated', 0),
        'languages_processed': result.get('languages_processed', 0)
    }


async def test_communication_protocol(components: Dict[str, Any]) -> Dict[str, Any]:
    """通信プロトコル統合テスト"""
    comm_protocol = components['comm_protocol']
    
    # メッセージ送受信テスト
    test_message = {
        'content': 'Integration test message',
        'timestamp': datetime.now().isoformat()
    }
    
    # 自己宛てメッセージ送信
    message_id = await comm_protocol.send_message(
        receiver="test_system",
        message_type=MessageType.REQUEST,
        payload=test_message
    )
    
    # メッセージ受信
    received = await comm_protocol.receive_message(timeout=5.0)
    
    return {
        'message_sent': message_id is not None,
        'message_received': received is not None,
        'round_trip_success': received and received.payload == test_message
    }


# ファクトリー関数
def create_integration_test_framework(config: Optional[Dict[str, Any]] = None) -> IntegrationTestFramework:
    """統合テストフレームワーク作成"""
    return IntegrationTestFramework(config)


if __name__ == "__main__":
    # テスト実行例
    async def run_integration_tests():
        # フレームワーク作成
        framework = create_integration_test_framework()
        
        try:
            # 環境セットアップ
            await framework.setup_test_environment()
            await framework.initialize_components()
            
            # テストケース作成
            test_cases = [
                framework.create_test_case(
                    "test_001",
                    "Command Tower Integration",
                    test_command_tower_integration,
                    module="command_tower",
                    expected={'command_executed': True}
                ),
                framework.create_test_case(
                    "test_002",
                    "Agent Coordination",
                    test_agent_coordination,
                    module="agent_coordinator",
                    expected={'task_completed': True}
                ),
                framework.create_test_case(
                    "test_003",
                    "Quality Analysis",
                    test_quality_analysis_integration,
                    module="quality_guardian",
                    expected={'analysis_completed': True}
                ),
                framework.create_test_case(
                    "test_004",
                    "Documentation Generation",
                    test_documentation_generation,
                    module="doc_synthesizer",
                    expected={'generation_completed': True}
                ),
                framework.create_test_case(
                    "test_005",
                    "Communication Protocol",
                    test_communication_protocol,
                    module="comm_protocol",
                    expected={'round_trip_success': True}
                )
            ]
            
            # テストスイート作成
            suite = framework.create_test_suite(
                "integration_suite_001",
                "Core Integration Test Suite",
                test_cases,
                description="Tests core component integration"
            )
            
            # テスト実行
            print("🚀 Running integration tests...")
            results = await framework.run_test_suite(suite)
            
            # レポート生成
            report_path = await framework.generate_test_report()
            print(f"\n📊 Test report generated: {report_path}")
            
            # サマリー表示
            print("\n🎯 Test Summary:")
            print(f"  Total: {framework.stats['total_tests']}")
            print(f"  Passed: {framework.stats['passed']} ✅")
            print(f"  Failed: {framework.stats['failed']} ❌")
            print(f"  Errors: {framework.stats['errors']} ⚠️")
            print(f"  Duration: {framework.stats['total_duration']:.2f}s")
            
        finally:
            # クリーンアップ
            await framework.cleanup()
    
    # 実行
    asyncio.run(run_integration_tests())