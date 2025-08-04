#!/usr/bin/env python3
"""
シュンスケ式E2Eテストフレームワーク - Ultimate ShunsukeModel Ecosystem

ユーザーの実際の使用シナリオを完全に再現し、
システム全体の動作を検証する包括的なエンドツーエンドテスト
"""

import asyncio
import pytest
import logging
import json
import time
import yaml
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Set, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import tempfile
import shutil
import sys
import os
import subprocess
import aiohttp
from enum import Enum
import re
from contextlib import asynccontextmanager
import psutil
import signal


# テスト対象モジュールのインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.command_tower.command_tower import CommandTower, CommandContext
from orchestration.coordinator.agent_coordinator import AgentCoordinator
from tools.quality_analyzer.quality_guardian import QualityGuardian
from tools.doc_synthesizer.documentation_synthesizer import DocumentationSynthesizer
from tools.performance_suite import create_performance_profiler, create_resource_monitor
from tests.integration.integration_test_framework import TestStatus, TestLevel


class UserAction(Enum):
    """ユーザーアクション"""
    COMMAND = "command"
    CLICK = "click"
    INPUT = "input"
    WAIT = "wait"
    VERIFY = "verify"
    NAVIGATE = "navigate"
    UPLOAD = "upload"
    DOWNLOAD = "download"


class ScenarioStatus(Enum):
    """シナリオステータス"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class UserStep:
    """ユーザーステップ"""
    step_id: str
    action: UserAction
    target: str
    value: Optional[Any] = None
    expected: Optional[Any] = None
    timeout: float = 30.0
    description: Optional[str] = None
    critical: bool = True  # 失敗時にシナリオを停止するか


@dataclass
class TestScenario:
    """E2Eテストシナリオ"""
    scenario_id: str
    name: str
    description: str
    user_profile: Dict[str, Any]
    steps: List[UserStep]
    setup_commands: List[str] = field(default_factory=list)
    teardown_commands: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: float = 600.0  # 10分
    tags: List[str] = field(default_factory=list)


@dataclass
class ScenarioResult:
    """シナリオ実行結果"""
    scenario: TestScenario
    status: ScenarioStatus
    start_time: datetime
    end_time: datetime
    duration: float
    steps_completed: int
    steps_total: int
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    screenshots: List[Path] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Path] = field(default_factory=list)


class E2ETestFramework:
    """
    シュンスケ式E2Eテストフレームワーク
    
    機能:
    - ユーザーワークフロー完全再現
    - 実環境シミュレーション
    - 視覚的検証
    - パフォーマンス計測
    - 自動レポート生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # テスト設定
        self.test_output_dir = Path(self.config.get('output_dir', './e2e_test_results'))
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 環境設定
        self.test_env_dir = Path(tempfile.mkdtemp(prefix="shunsuke_e2e_"))
        self.browser_process = None
        self.server_process = None
        
        # シナリオ管理
        self.scenarios: Dict[str, TestScenario] = {}
        self.scenario_results: List[ScenarioResult] = []
        
        # プロセス管理
        self.processes: Dict[str, subprocess.Popen] = {}
        
        # パフォーマンス監視
        self.performance_profiler = None
        self.resource_monitor = None
        
        # 統計情報
        self.stats = {
            'total_scenarios': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'timeout': 0,
            'total_duration': 0.0,
            'total_steps': 0,
            'steps_passed': 0,
            'steps_failed': 0
        }
    
    async def setup_test_environment(self):
        """テスト環境セットアップ"""
        try:
            self.logger.info("Setting up E2E test environment...")
            
            # パフォーマンス監視ツール初期化
            self.performance_profiler = create_performance_profiler()
            self.resource_monitor = create_resource_monitor()
            
            await self.resource_monitor.start_monitoring()
            
            # テスト用ディレクトリ構造作成
            (self.test_env_dir / "workspace").mkdir(exist_ok=True)
            (self.test_env_dir / "logs").mkdir(exist_ok=True)
            (self.test_env_dir / "screenshots").mkdir(exist_ok=True)
            (self.test_env_dir / "artifacts").mkdir(exist_ok=True)
            
            # テスト用プロジェクト作成
            await self._create_test_project()
            
            # サーバー起動
            await self._start_test_servers()
            
            self.logger.info(f"E2E test environment created at: {self.test_env_dir}")
            
        except Exception as e:
            self.logger.error(f"E2E test environment setup failed: {e}")
            raise
    
    async def teardown_test_environment(self):
        """テスト環境クリーンアップ"""
        try:
            self.logger.info("Tearing down E2E test environment...")
            
            # リソース監視停止
            if self.resource_monitor:
                await self.resource_monitor.stop_monitoring()
            
            # プロセス終了
            for name, process in self.processes.items():
                self._terminate_process(process)
            
            # テスト環境削除
            if self.test_env_dir.exists():
                shutil.rmtree(self.test_env_dir)
            
        except Exception as e:
            self.logger.error(f"E2E test environment teardown error: {e}")
    
    async def _create_test_project(self):
        """テスト用プロジェクト作成"""
        project_dir = self.test_env_dir / "workspace" / "test_project"
        project_dir.mkdir(parents=True)
        
        # サンプルファイル作成
        # Python ファイル
        (project_dir / "main.py").write_text("""
#!/usr/bin/env python3
\"\"\"Test project main module\"\"\"

def main():
    print("Hello from test project!")
    return 0

if __name__ == "__main__":
    main()
""")
        
        # JavaScript ファイル
        (project_dir / "app.js").write_text("""
// Test application
class TestApp {
    constructor() {
        this.name = "Test Application";
    }
    
    run() {
        console.log(`Running ${this.name}`);
    }
}

module.exports = TestApp;
""")
        
        # 設定ファイル
        config_data = {
            "name": "test_project",
            "version": "1.0.0",
            "description": "E2E test project"
        }
        
        (project_dir / "config.json").write_text(json.dumps(config_data, indent=2))
    
    async def _start_test_servers(self):
        """テストサーバー起動"""
        # MCP サーバーのモック
        mcp_server_script = self.test_env_dir / "mcp_mock_server.py"
        mcp_server_script.write_text("""
#!/usr/bin/env python3
import asyncio
import json
import sys

async def handle_request(reader, writer):
    data = await reader.read(1000)
    response = json.dumps({"status": "ok", "result": "mocked"})
    writer.write(response.encode())
    await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle_request, 'localhost', 8080)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
""")
        
        # サーバープロセス起動
        self.processes['mcp_server'] = subprocess.Popen(
            [sys.executable, str(mcp_server_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 起動待機
        await asyncio.sleep(2)
    
    def create_scenario(self,
                       scenario_id: str,
                       name: str,
                       steps: List[UserStep],
                       **kwargs) -> TestScenario:
        """シナリオ作成"""
        scenario = TestScenario(
            scenario_id=scenario_id,
            name=name,
            description=kwargs.get('description', ''),
            user_profile=kwargs.get('user_profile', {'role': 'developer'}),
            steps=steps,
            setup_commands=kwargs.get('setup_commands', []),
            teardown_commands=kwargs.get('teardown_commands', []),
            environment=kwargs.get('environment', {}),
            timeout=kwargs.get('timeout', 600.0),
            tags=kwargs.get('tags', [])
        )
        
        self.scenarios[scenario_id] = scenario
        return scenario
    
    async def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        """シナリオ実行"""
        start_time = datetime.now()
        result = ScenarioResult(
            scenario=scenario,
            status=ScenarioStatus.RUNNING,
            start_time=start_time,
            end_time=start_time,
            duration=0.0,
            steps_completed=0,
            steps_total=len(scenario.steps)
        )
        
        # ログキャプチャ設定
        log_capture = []
        log_handler = logging.StreamHandler()
        
        class LogCapture(logging.Handler):
            def emit(self, record):
                log_capture.append(self.format(record))
        
        capture_handler = LogCapture()
        self.logger.addHandler(capture_handler)
        
        try:
            self.logger.info(f"Running E2E scenario: {scenario.name}")
            
            # 環境変数設定
            env = os.environ.copy()
            env.update(scenario.environment)
            
            # セットアップコマンド実行
            for cmd in scenario.setup_commands:
                await self._execute_command(cmd, env)
            
            # パフォーマンスプロファイリング開始
            profile_id = f"scenario_{scenario.scenario_id}"
            if self.performance_profiler:
                await self.performance_profiler.start_profile(profile_id, scenario.name)
            
            # ステップ実行
            for i, step in enumerate(scenario.steps):
                try:
                    step_result = await self._execute_step(step, env)
                    result.step_results.append(step_result)
                    
                    if step_result['status'] == 'passed':
                        result.steps_completed += 1
                        self.stats['steps_passed'] += 1
                    else:
                        self.stats['steps_failed'] += 1
                        if step.critical:
                            result.status = ScenarioStatus.FAILED
                            result.error_message = f"Critical step failed: {step.step_id}"
                            break
                    
                except asyncio.TimeoutError:
                    result.status = ScenarioStatus.TIMEOUT
                    result.error_message = f"Step timeout: {step.step_id}"
                    break
                    
                except Exception as e:
                    result.status = ScenarioStatus.FAILED
                    result.error_message = f"Step error: {step.step_id} - {str(e)}"
                    if step.critical:
                        break
            
            # 全ステップ成功時
            if result.steps_completed == result.steps_total:
                result.status = ScenarioStatus.PASSED
            
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
                result.performance_metrics['resource_usage'] = current_metrics
            
            # ティアダウンコマンド実行
            for cmd in scenario.teardown_commands:
                await self._execute_command(cmd, env)
            
        except asyncio.TimeoutError:
            result.status = ScenarioStatus.TIMEOUT
            result.error_message = f"Scenario timeout after {scenario.timeout}s"
            
        except Exception as e:
            result.status = ScenarioStatus.FAILED
            result.error_message = str(e)
            
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
            self.scenario_results.append(result)
            
            self.logger.info(f"Scenario completed: {scenario.name} - {result.status.value}")
        
        return result
    
    async def _execute_step(self, step: UserStep, env: Dict[str, str]) -> Dict[str, Any]:
        """ステップ実行"""
        step_start = time.time()
        step_result = {
            'step_id': step.step_id,
            'action': step.action.value,
            'status': 'running',
            'duration': 0.0,
            'error': None
        }
        
        try:
            self.logger.info(f"Executing step: {step.step_id} - {step.action.value}")
            
            # タイムアウト付き実行
            async with asyncio.timeout(step.timeout):
                if step.action == UserAction.COMMAND:
                    result = await self._execute_command_step(step, env)
                    
                elif step.action == UserAction.INPUT:
                    result = await self._execute_input_step(step, env)
                    
                elif step.action == UserAction.VERIFY:
                    result = await self._execute_verify_step(step, env)
                    
                elif step.action == UserAction.WAIT:
                    await asyncio.sleep(float(step.value or 1))
                    result = {'status': 'success'}
                    
                elif step.action == UserAction.UPLOAD:
                    result = await self._execute_upload_step(step, env)
                    
                elif step.action == UserAction.DOWNLOAD:
                    result = await self._execute_download_step(step, env)
                    
                else:
                    result = {'status': 'skipped', 'message': f'Unsupported action: {step.action}'}
                
                # 結果判定
                if result.get('status') == 'success':
                    step_result['status'] = 'passed'
                else:
                    step_result['status'] = 'failed'
                    step_result['error'] = result.get('message', 'Unknown error')
                    
        except asyncio.TimeoutError:
            step_result['status'] = 'timeout'
            step_result['error'] = f'Step timed out after {step.timeout}s'
            
        except Exception as e:
            step_result['status'] = 'error'
            step_result['error'] = str(e)
            
        finally:
            step_result['duration'] = time.time() - step_start
            self.stats['total_steps'] += 1
        
        return step_result
    
    async def _execute_command_step(self, step: UserStep, env: Dict[str, str]) -> Dict[str, Any]:
        """コマンドステップ実行"""
        try:
            # CommandTower を使用してコマンド実行
            command_tower = CommandTower()
            await command_tower.initialize()
            
            context = CommandContext(
                user_id="e2e_test_user",
                environment=env
            )
            
            result = await command_tower.execute_command_sequence(
                step.value,
                context=context
            )
            
            # 期待値チェック
            if step.expected:
                if self._validate_expected(result, step.expected):
                    return {'status': 'success', 'result': result}
                else:
                    return {'status': 'failed', 'message': 'Expected value mismatch'}
            
            return {'status': 'success', 'result': result}
            
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}
    
    async def _execute_input_step(self, step: UserStep, env: Dict[str, str]) -> Dict[str, Any]:
        """入力ステップ実行"""
        try:
            # ファイルへの書き込みをシミュレート
            target_path = self.test_env_dir / "workspace" / step.target
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(step.value, dict):
                content = json.dumps(step.value, indent=2)
            else:
                content = str(step.value)
            
            target_path.write_text(content)
            
            return {'status': 'success'}
            
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}
    
    async def _execute_verify_step(self, step: UserStep, env: Dict[str, str]) -> Dict[str, Any]:
        """検証ステップ実行"""
        try:
            # ファイルの存在確認
            if step.target.startswith("file:"):
                file_path = self.test_env_dir / "workspace" / step.target[5:]
                if file_path.exists():
                    if step.expected:
                        content = file_path.read_text()
                        if step.expected in content:
                            return {'status': 'success'}
                        else:
                            return {'status': 'failed', 'message': 'Content mismatch'}
                    return {'status': 'success'}
                else:
                    return {'status': 'failed', 'message': 'File not found'}
            
            # プロセスの状態確認
            elif step.target.startswith("process:"):
                process_name = step.target[8:]
                if process_name in self.processes:
                    process = self.processes[process_name]
                    if process.poll() is None:
                        return {'status': 'success'}
                    else:
                        return {'status': 'failed', 'message': 'Process not running'}
                else:
                    return {'status': 'failed', 'message': 'Process not found'}
            
            # HTTPエンドポイントの確認
            elif step.target.startswith("http://") or step.target.startswith("https://"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(step.target) as response:
                        if response.status == 200:
                            if step.expected:
                                text = await response.text()
                                if step.expected in text:
                                    return {'status': 'success'}
                                else:
                                    return {'status': 'failed', 'message': 'Response mismatch'}
                            return {'status': 'success'}
                        else:
                            return {'status': 'failed', 'message': f'HTTP {response.status}'}
            
            else:
                return {'status': 'failed', 'message': 'Unknown verification target'}
                
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}
    
    async def _execute_upload_step(self, step: UserStep, env: Dict[str, str]) -> Dict[str, Any]:
        """アップロードステップ実行"""
        try:
            source_path = Path(step.value)
            target_path = self.test_env_dir / "workspace" / step.target
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_file():
                shutil.copy2(source_path, target_path)
            else:
                shutil.copytree(source_path, target_path)
            
            return {'status': 'success'}
            
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}
    
    async def _execute_download_step(self, step: UserStep, env: Dict[str, str]) -> Dict[str, Any]:
        """ダウンロードステップ実行"""
        try:
            source_path = self.test_env_dir / "workspace" / step.target
            target_path = Path(step.value)
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.exists():
                if source_path.is_file():
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.copytree(source_path, target_path)
                return {'status': 'success'}
            else:
                return {'status': 'failed', 'message': 'Source not found'}
                
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}
    
    async def _execute_command(self, command: str, env: Dict[str, str]):
        """コマンド実行"""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=self.test_env_dir / "workspace"
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Command failed: {command}\n{stderr.decode()}")
    
    def _validate_expected(self, actual: Any, expected: Any) -> bool:
        """期待値検証"""
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return False
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._validate_expected(actual[key], value):
                    return False
            return True
        elif isinstance(expected, list):
            if not isinstance(actual, list):
                return False
            if len(actual) != len(expected):
                return False
            for a, e in zip(actual, expected):
                if not self._validate_expected(a, e):
                    return False
            return True
        else:
            return actual == expected
    
    def _terminate_process(self, process: subprocess.Popen):
        """プロセス終了"""
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    
    def _update_statistics(self, result: ScenarioResult):
        """統計情報更新"""
        self.stats['total_scenarios'] += 1
        self.stats['total_duration'] += result.duration
        
        if result.status == ScenarioStatus.PASSED:
            self.stats['passed'] += 1
        elif result.status == ScenarioStatus.FAILED:
            self.stats['failed'] += 1
        elif result.status == ScenarioStatus.SKIPPED:
            self.stats['skipped'] += 1
        elif result.status == ScenarioStatus.TIMEOUT:
            self.stats['timeout'] += 1
    
    async def run_all_scenarios(self) -> List[ScenarioResult]:
        """全シナリオ実行"""
        results = []
        
        for scenario in self.scenarios.values():
            self.logger.info(f"Running scenario: {scenario.name}")
            result = await self.run_scenario(scenario)
            results.append(result)
            
            # スクリーンショット保存
            if result.status != ScenarioStatus.PASSED:
                await self._capture_state(scenario, result)
        
        return results
    
    async def _capture_state(self, scenario: TestScenario, result: ScenarioResult):
        """状態キャプチャ"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # ログファイル保存
            log_file = self.test_output_dir / f"scenario_{scenario.scenario_id}_{timestamp}.log"
            with open(log_file, 'w') as f:
                f.write('\n'.join(result.logs))
            result.artifacts.append(log_file)
            
            # ワークスペース状態保存
            workspace_snapshot = self.test_output_dir / f"workspace_{scenario.scenario_id}_{timestamp}"
            if (self.test_env_dir / "workspace").exists():
                shutil.copytree(
                    self.test_env_dir / "workspace",
                    workspace_snapshot,
                    ignore_errors=True
                )
                result.artifacts.append(workspace_snapshot)
            
        except Exception as e:
            self.logger.error(f"State capture error: {e}")
    
    async def generate_e2e_report(self) -> Path:
        """E2Eテストレポート生成"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = self.test_output_dir / f"e2e_report_{timestamp}.html"
            
            # HTML レポート生成
            html_content = self._generate_html_report()
            
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            # JSON レポート生成
            json_path = self.test_output_dir / f"e2e_results_{timestamp}.json"
            json_data = self._generate_json_report()
            
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            self.logger.info(f"E2E test reports generated: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            raise
    
    def _generate_html_report(self) -> str:
        """HTMLレポート生成"""
        passed_rate = (self.stats['passed'] / max(self.stats['total_scenarios'], 1)) * 100
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>E2E Test Report - Ultimate ShunsukeModel Ecosystem</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #1a237e; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .scenario {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .passed {{ border-left: 5px solid #4caf50; }}
        .failed {{ border-left: 5px solid #f44336; }}
        .timeout {{ border-left: 5px solid #ff9800; }}
        .skipped {{ border-left: 5px solid #9e9e9e; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e3f2fd; border-radius: 5px; }}
        .step {{ margin: 10px 20px; padding: 10px; background-color: #f5f5f5; border-radius: 3px; }}
        .step.passed {{ background-color: #e8f5e9; }}
        .step.failed {{ background-color: #ffebee; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3f51b5; color: white; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .timeline {{ margin: 20px 0; }}
        .timeline-bar {{ height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .timeline-progress {{ height: 100%; background-color: #4caf50; transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 E2E Test Report</h1>
        <p>Ultimate ShunsukeModel Ecosystem - End-to-End Testing</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Executive Summary</h2>
        <div class="metric">Total Scenarios: <strong>{self.stats['total_scenarios']}</strong></div>
        <div class="metric" style="background-color: #c8e6c9;">Passed: <strong>{self.stats['passed']}</strong></div>
        <div class="metric" style="background-color: #ffcdd2;">Failed: <strong>{self.stats['failed']}</strong></div>
        <div class="metric" style="background-color: #ffe0b2;">Timeout: <strong>{self.stats['timeout']}</strong></div>
        <div class="metric">Pass Rate: <strong>{passed_rate:.1f}%</strong></div>
        <div class="metric">Total Duration: <strong>{self.stats['total_duration']:.2f}s</strong></div>
    </div>
    
    <div class="summary">
        <h2>🎭 User Journey Coverage</h2>
        <table>
            <tr>
                <th>Scenario</th>
                <th>User Profile</th>
                <th>Steps</th>
                <th>Duration</th>
                <th>Status</th>
            </tr>
"""
        
        # シナリオ結果の追加
        for result in self.scenario_results:
            user_role = result.scenario.user_profile.get('role', 'unknown')
            status_class = result.status.value.lower()
            status_icon = {
                ScenarioStatus.PASSED: "✅",
                ScenarioStatus.FAILED: "❌",
                ScenarioStatus.TIMEOUT: "⏱️",
                ScenarioStatus.SKIPPED: "⏭️"
            }.get(result.status, "❓")
            
            html += f"""
            <tr>
                <td>{result.scenario.name}</td>
                <td>{user_role}</td>
                <td>{result.steps_completed}/{result.steps_total}</td>
                <td>{result.duration:.2f}s</td>
                <td>{status_icon} {result.status.value}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
    
    <h2>🔍 Detailed Scenario Results</h2>
"""
        
        # 詳細結果
        for result in self.scenario_results:
            status_class = result.status.value.lower()
            
            html += f"""
    <div class="scenario {status_class}">
        <h3>{result.scenario.name}</h3>
        <p><strong>Description:</strong> {result.scenario.description}</p>
        <p><strong>Status:</strong> {result.status.value}</p>
        <p><strong>Duration:</strong> {result.duration:.2f}s</p>
        <p><strong>Steps Completed:</strong> {result.steps_completed}/{result.steps_total}</p>
        
        <div class="timeline">
            <div class="timeline-bar">
                <div class="timeline-progress" style="width: {(result.steps_completed/result.steps_total)*100}%"></div>
            </div>
        </div>
"""
            
            if result.error_message:
                html += f"""
        <p><strong>Error:</strong></p>
        <pre>{result.error_message}</pre>
"""
            
            # ステップ詳細
            if result.step_results:
                html += """
        <details>
            <summary>Step Details</summary>
"""
                for step_result in result.step_results:
                    step_class = "passed" if step_result['status'] == 'passed' else "failed"
                    html += f"""
            <div class="step {step_class}">
                <strong>{step_result['step_id']}</strong> - {step_result['action']} 
                ({step_result['duration']:.2f}s) - {step_result['status']}
                {f"<br>Error: {step_result['error']}" if step_result.get('error') else ""}
            </div>
"""
                html += """
        </details>
"""
            
            # パフォーマンスメトリクス
            if result.performance_metrics:
                html += f"""
        <details>
            <summary>Performance Metrics</summary>
            <pre>{json.dumps(result.performance_metrics, indent=2)}</pre>
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
            'scenario_results': [
                {
                    'scenario_id': result.scenario.scenario_id,
                    'name': result.scenario.name,
                    'status': result.status.value,
                    'duration': result.duration,
                    'steps_completed': result.steps_completed,
                    'steps_total': result.steps_total,
                    'start_time': result.start_time.isoformat(),
                    'end_time': result.end_time.isoformat(),
                    'error_message': result.error_message,
                    'step_results': result.step_results,
                    'performance_metrics': result.performance_metrics,
                    'artifacts': [str(p) for p in result.artifacts]
                }
                for result in self.scenario_results
            ],
            'scenarios': {
                scenario_id: {
                    'name': scenario.name,
                    'description': scenario.description,
                    'user_profile': scenario.user_profile,
                    'step_count': len(scenario.steps),
                    'tags': scenario.tags
                }
                for scenario_id, scenario in self.scenarios.items()
            }
        }
    
    async def cleanup(self):
        """クリーンアップ"""
        await self.teardown_test_environment()


# 標準E2Eシナリオ定義
def create_developer_workflow_scenario() -> TestScenario:
    """開発者ワークフローシナリオ"""
    steps = [
        UserStep(
            step_id="dev_01",
            action=UserAction.COMMAND,
            target="command_tower",
            value="create_project python_app",
            expected={'status': 'completed'},
            description="新規プロジェクト作成"
        ),
        UserStep(
            step_id="dev_02",
            action=UserAction.INPUT,
            target="python_app/main.py",
            value="""
def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
""",
            description="メインコード作成"
        ),
        UserStep(
            step_id="dev_03",
            action=UserAction.COMMAND,
            target="command_tower",
            value="analyze_code python_app",
            expected={'issues': []},
            description="コード品質分析"
        ),
        UserStep(
            step_id="dev_04",
            action=UserAction.VERIFY,
            target="file:python_app/main.py",
            expected="hello_world",
            description="ファイル作成確認"
        ),
        UserStep(
            step_id="dev_05",
            action=UserAction.COMMAND,
            target="command_tower",
            value="generate_docs python_app",
            expected={'status': 'completed'},
            description="ドキュメント生成"
        ),
        UserStep(
            step_id="dev_06",
            action=UserAction.VERIFY,
            target="file:python_app/docs/README.md",
            expected="# python_app",
            description="ドキュメント確認"
        )
    ]
    
    return TestScenario(
        scenario_id="developer_workflow_01",
        name="Developer Project Creation Workflow",
        description="開発者が新規プロジェクトを作成し、コード品質チェックとドキュメント生成を行うワークフロー",
        user_profile={'role': 'developer', 'experience': 'intermediate'},
        steps=steps,
        tags=['developer', 'project_creation', 'documentation']
    )


def create_optimization_workflow_scenario() -> TestScenario:
    """最適化ワークフローシナリオ"""
    steps = [
        UserStep(
            step_id="opt_01",
            action=UserAction.INPUT,
            target="slow_app/process.py",
            value="""
import time

def slow_function(data):
    # Intentionally slow function
    result = []
    for i in range(len(data)):
        time.sleep(0.01)
        result.append(data[i] * 2)
    return result

def main():
    data = list(range(100))
    result = slow_function(data)
    print(f"Processed {len(result)} items")
""",
            description="遅いコードの作成"
        ),
        UserStep(
            step_id="opt_02",
            action=UserAction.COMMAND,
            target="command_tower",
            value="profile_performance slow_app/process.py",
            expected={'bottlenecks': ['slow_function']},
            description="パフォーマンスプロファイリング"
        ),
        UserStep(
            step_id="opt_03",
            action=UserAction.COMMAND,
            target="command_tower",
            value="optimize_code slow_app/process.py",
            expected={'status': 'optimized'},
            description="コード最適化実行"
        ),
        UserStep(
            step_id="opt_04",
            action=UserAction.VERIFY,
            target="file:slow_app/process_optimized.py",
            expected="# Optimized",
            description="最適化済みコード確認"
        ),
        UserStep(
            step_id="opt_05",
            action=UserAction.COMMAND,
            target="command_tower",
            value="benchmark slow_app/process.py slow_app/process_optimized.py",
            expected={'improvement': True},
            description="ベンチマーク比較"
        )
    ]
    
    return TestScenario(
        scenario_id="optimization_workflow_01",
        name="Performance Optimization Workflow",
        description="パフォーマンスボトルネックを検出し、自動最適化を実行するワークフロー",
        user_profile={'role': 'performance_engineer', 'focus': 'optimization'},
        steps=steps,
        tags=['optimization', 'performance', 'profiling']
    )


def create_multi_agent_scenario() -> TestScenario:
    """マルチエージェント協調シナリオ"""
    steps = [
        UserStep(
            step_id="ma_01",
            action=UserAction.INPUT,
            target="complex_project/requirements.txt",
            value="""
flask==2.0.1
sqlalchemy==1.4.22
pytest==6.2.4
black==21.7b0
""",
            description="プロジェクト要件定義"
        ),
        UserStep(
            step_id="ma_02",
            action=UserAction.COMMAND,
            target="command_tower",
            value="allocate_agents complex_project analyze",
            expected={'agents': ['scout', 'quality_guardian', 'doc_synthesizer']},
            description="エージェント割り当て"
        ),
        UserStep(
            step_id="ma_03",
            action=UserAction.COMMAND,
            target="command_tower",
            value="execute_multi_agent_task complex_project full_analysis",
            expected={'status': 'completed'},
            description="マルチエージェントタスク実行"
        ),
        UserStep(
            step_id="ma_04",
            action=UserAction.WAIT,
            target="task_completion",
            value=5,
            description="タスク完了待機"
        ),
        UserStep(
            step_id="ma_05",
            action=UserAction.VERIFY,
            target="file:complex_project/reports/analysis_report.json",
            expected="quality_score",
            description="分析レポート確認"
        ),
        UserStep(
            step_id="ma_06",
            action=UserAction.COMMAND,
            target="command_tower",
            value="aggregate_agent_results complex_project",
            expected={'reports': 3},
            description="エージェント結果集約"
        )
    ]
    
    return TestScenario(
        scenario_id="multi_agent_01",
        name="Multi-Agent Collaboration Scenario",
        description="複数のAIエージェントが協調してプロジェクト分析を行うシナリオ",
        user_profile={'role': 'architect', 'team_size': 'large'},
        steps=steps,
        tags=['multi_agent', 'collaboration', 'analysis']
    )


# ファクトリー関数
def create_e2e_test_framework(config: Optional[Dict[str, Any]] = None) -> E2ETestFramework:
    """E2Eテストフレームワーク作成"""
    return E2ETestFramework(config)


if __name__ == "__main__":
    # E2Eテスト実行例
    async def run_e2e_tests():
        # フレームワーク作成
        framework = create_e2e_test_framework()
        
        try:
            # 環境セットアップ
            await framework.setup_test_environment()
            
            # シナリオ登録
            scenarios = [
                create_developer_workflow_scenario(),
                create_optimization_workflow_scenario(),
                create_multi_agent_scenario()
            ]
            
            for scenario in scenarios:
                framework.scenarios[scenario.scenario_id] = scenario
            
            # 全シナリオ実行
            print("🚀 Running E2E test scenarios...")
            results = await framework.run_all_scenarios()
            
            # レポート生成
            report_path = await framework.generate_e2e_report()
            print(f"\n📊 E2E test report generated: {report_path}")
            
            # サマリー表示
            print("\n🎯 E2E Test Summary:")
            print(f"  Total Scenarios: {framework.stats['total_scenarios']}")
            print(f"  Passed: {framework.stats['passed']} ✅")
            print(f"  Failed: {framework.stats['failed']} ❌")
            print(f"  Timeout: {framework.stats['timeout']} ⏱️")
            print(f"  Total Duration: {framework.stats['total_duration']:.2f}s")
            print(f"  Steps Success Rate: {(framework.stats['steps_passed'] / max(framework.stats['total_steps'], 1)) * 100:.1f}%")
            
        finally:
            # クリーンアップ
            await framework.cleanup()
    
    # 実行
    asyncio.run(run_e2e_tests())