#!/usr/bin/env python3
"""
シュンスケ式E2Eテストスイート - Ultimate ShunsukeModel Ecosystem

エンドツーエンドテストのための包括的なテストフレームワーク
"""

from .e2e_test_framework import (
    E2ETestFramework,
    UserAction,
    ScenarioStatus,
    UserStep,
    TestScenario,
    ScenarioResult,
    create_e2e_test_framework,
    create_developer_workflow_scenario,
    create_optimization_workflow_scenario,
    create_multi_agent_scenario
)

from .scenario_builder import (
    ScenarioBuilder,
    SAMPLE_SCENARIO_YAML
)

__version__ = "1.0.0"
__author__ = "ShunsukeModel Team"

__all__ = [
    # E2E Test Framework
    "E2ETestFramework",
    "UserAction",
    "ScenarioStatus",
    "UserStep",
    "TestScenario",
    "ScenarioResult",
    "create_e2e_test_framework",
    
    # Standard Scenarios
    "create_developer_workflow_scenario",
    "create_optimization_workflow_scenario",
    "create_multi_agent_scenario",
    
    # Scenario Builder
    "ScenarioBuilder",
    "SAMPLE_SCENARIO_YAML"
]

# モジュール情報
__doc__ = """
Ultimate ShunsukeModel Ecosystem - E2E Test Suite

エンドツーエンドテストの包括的なフレームワーク

主要コンポーネント:

1. E2E Test Framework (E2Eテストフレームワーク)
   - ユーザーワークフロー完全再現
   - 実環境シミュレーション
   - マルチステップシナリオ実行
   - パフォーマンス計測
   - 自動レポート生成

2. Scenario Builder (シナリオビルダー)
   - YAMLベースのシナリオ定義
   - テンプレート機能
   - 条件分岐・ループサポート
   - データ駆動テスト
   - ランダムシナリオ生成

使用例:

# 基本的なE2Eテスト実行
from tests.e2e import create_e2e_test_framework, create_developer_workflow_scenario

async def run_e2e():
    framework = create_e2e_test_framework()
    await framework.setup_test_environment()
    
    scenario = create_developer_workflow_scenario()
    result = await framework.run_scenario(scenario)
    
    print(f"Result: {result.status}")
    await framework.cleanup()

# YAMLベースのシナリオ実行
from tests.e2e import ScenarioBuilder, E2ETestFramework

builder = ScenarioBuilder()
scenarios = builder.load_scenario_yaml(Path("scenarios.yaml"))

framework = E2ETestFramework()
for scenario in scenarios:
    result = await framework.run_scenario(scenario)

# データ駆動テスト
data_sets = [
    {'env': 'dev', 'user': 'developer'},
    {'env': 'staging', 'user': 'tester'},
    {'env': 'prod', 'user': 'admin'}
]

scenarios = builder.create_data_driven_scenario('base_scenario', data_sets)

ユーザーアクション:
- COMMAND: コマンド実行
- INPUT: データ入力
- VERIFY: 検証
- WAIT: 待機
- CLICK: クリック（UI）
- NAVIGATE: ナビゲーション
- UPLOAD: アップロード
- DOWNLOAD: ダウンロード

シナリオステータス:
- PENDING: 実行待ち
- RUNNING: 実行中
- PASSED: 成功
- FAILED: 失敗
- SKIPPED: スキップ
- TIMEOUT: タイムアウト

レポート形式:
- HTMLレポート（視覚的）
- JSONレポート（プログラマティック）
- パフォーマンスメトリクス
- ステップ詳細ログ

統合機能:
- Command Tower連携
- Agent Coordinator連携
- Quality Guardian連携
- Performance Suite統合
- リアルタイムモニタリング
"""