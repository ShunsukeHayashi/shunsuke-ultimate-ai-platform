#!/usr/bin/env python3
"""
シュンスケ式E2Eシナリオビルダー - Ultimate ShunsukeModel Ecosystem

YAMLベースのシナリオ定義と動的シナリオ生成をサポートする
高度なシナリオ構築ツール
"""

import yaml
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import re
from datetime import datetime
import random
import string

from e2e_test_framework import TestScenario, UserStep, UserAction


class ScenarioBuilder:
    """
    E2Eシナリオビルダー
    
    機能:
    - YAMLベースのシナリオ定義
    - テンプレート変数展開
    - 条件分岐サポート
    - ループ構造サポート
    - 動的シナリオ生成
    """
    
    def __init__(self):
        self.templates = {}
        self.variables = {}
        self.scenarios = {}
        
    def load_scenario_yaml(self, yaml_path: Path) -> List[TestScenario]:
        """YAMLファイルからシナリオロード"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        scenarios = []
        
        # グローバル変数設定
        if 'variables' in data:
            self.variables.update(data['variables'])
        
        # テンプレート登録
        if 'templates' in data:
            for name, template in data['templates'].items():
                self.templates[name] = template
        
        # シナリオ構築
        if 'scenarios' in data:
            for scenario_data in data['scenarios']:
                scenario = self._build_scenario(scenario_data)
                scenarios.append(scenario)
                self.scenarios[scenario.scenario_id] = scenario
        
        return scenarios
    
    def _build_scenario(self, scenario_data: Dict[str, Any]) -> TestScenario:
        """シナリオ構築"""
        # 変数展開
        scenario_data = self._expand_variables(scenario_data)
        
        # ステップ構築
        steps = []
        for step_data in scenario_data.get('steps', []):
            if 'template' in step_data:
                # テンプレート展開
                template_steps = self._expand_template(step_data['template'], step_data.get('params', {}))
                steps.extend(template_steps)
            elif 'loop' in step_data:
                # ループ展開
                loop_steps = self._expand_loop(step_data)
                steps.extend(loop_steps)
            elif 'condition' in step_data:
                # 条件分岐
                conditional_steps = self._expand_condition(step_data)
                steps.extend(conditional_steps)
            else:
                # 通常ステップ
                step = self._build_step(step_data)
                steps.append(step)
        
        # シナリオ作成
        return TestScenario(
            scenario_id=scenario_data['id'],
            name=scenario_data['name'],
            description=scenario_data.get('description', ''),
            user_profile=scenario_data.get('user_profile', {}),
            steps=steps,
            setup_commands=scenario_data.get('setup', []),
            teardown_commands=scenario_data.get('teardown', []),
            environment=scenario_data.get('environment', {}),
            timeout=scenario_data.get('timeout', 600.0),
            tags=scenario_data.get('tags', [])
        )
    
    def _build_step(self, step_data: Dict[str, Any]) -> UserStep:
        """ステップ構築"""
        action = UserAction[step_data['action'].upper()]
        
        return UserStep(
            step_id=step_data['id'],
            action=action,
            target=step_data['target'],
            value=step_data.get('value'),
            expected=step_data.get('expected'),
            timeout=step_data.get('timeout', 30.0),
            description=step_data.get('description'),
            critical=step_data.get('critical', True)
        )
    
    def _expand_variables(self, data: Any) -> Any:
        """変数展開"""
        if isinstance(data, str):
            # 変数置換
            pattern = r'\$\{(\w+)\}'
            matches = re.findall(pattern, data)
            for var_name in matches:
                if var_name in self.variables:
                    data = data.replace(f'${{{var_name}}}', str(self.variables[var_name]))
            return data
        elif isinstance(data, dict):
            return {k: self._expand_variables(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._expand_variables(item) for item in data]
        else:
            return data
    
    def _expand_template(self, template_name: str, params: Dict[str, Any]) -> List[UserStep]:
        """テンプレート展開"""
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")
        
        template = self.templates[template_name]
        steps = []
        
        # パラメータを一時変数として設定
        old_vars = self.variables.copy()
        self.variables.update(params)
        
        # テンプレートステップを展開
        for step_data in template['steps']:
            step_data = self._expand_variables(step_data)
            step = self._build_step(step_data)
            steps.append(step)
        
        # 変数を復元
        self.variables = old_vars
        
        return steps
    
    def _expand_loop(self, loop_data: Dict[str, Any]) -> List[UserStep]:
        """ループ展開"""
        steps = []
        
        loop_type = loop_data['loop']['type']
        loop_var = loop_data['loop'].get('var', 'i')
        
        if loop_type == 'range':
            start = loop_data['loop'].get('start', 0)
            end = loop_data['loop']['end']
            step = loop_data['loop'].get('step', 1)
            
            for i in range(start, end, step):
                # ループ変数設定
                old_var = self.variables.get(loop_var)
                self.variables[loop_var] = i
                
                # ステップ展開
                for step_data in loop_data['steps']:
                    step_data = self._expand_variables(step_data)
                    step_obj = self._build_step(step_data)
                    steps.append(step_obj)
                
                # 変数復元
                if old_var is not None:
                    self.variables[loop_var] = old_var
                else:
                    del self.variables[loop_var]
        
        elif loop_type == 'list':
            items = loop_data['loop']['items']
            
            for item in items:
                # ループ変数設定
                old_var = self.variables.get(loop_var)
                self.variables[loop_var] = item
                
                # ステップ展開
                for step_data in loop_data['steps']:
                    step_data = self._expand_variables(step_data)
                    step_obj = self._build_step(step_data)
                    steps.append(step_obj)
                
                # 変数復元
                if old_var is not None:
                    self.variables[loop_var] = old_var
                else:
                    del self.variables[loop_var]
        
        return steps
    
    def _expand_condition(self, condition_data: Dict[str, Any]) -> List[UserStep]:
        """条件分岐展開"""
        steps = []
        
        condition = condition_data['condition']
        
        # 条件評価（簡易版）
        if self._evaluate_condition(condition):
            for step_data in condition_data.get('then', []):
                step = self._build_step(step_data)
                steps.append(step)
        else:
            for step_data in condition_data.get('else', []):
                step = self._build_step(step_data)
                steps.append(step)
        
        return steps
    
    def _evaluate_condition(self, condition: str) -> bool:
        """条件評価（簡易実装）"""
        # 変数展開
        condition = self._expand_variables(condition)
        
        # 安全な評価（基本的な比較のみ）
        try:
            # 簡単な比較演算子のみサポート
            if '==' in condition:
                left, right = condition.split('==')
                return left.strip() == right.strip()
            elif '!=' in condition:
                left, right = condition.split('!=')
                return left.strip() != right.strip()
            elif '>' in condition:
                left, right = condition.split('>')
                return float(left.strip()) > float(right.strip())
            elif '<' in condition:
                left, right = condition.split('<')
                return float(left.strip()) < float(right.strip())
            else:
                # デフォルトはTrue
                return True
        except:
            return False
    
    def create_data_driven_scenario(self,
                                   base_scenario_id: str,
                                   data_sets: List[Dict[str, Any]]) -> List[TestScenario]:
        """データ駆動シナリオ生成"""
        if base_scenario_id not in self.scenarios:
            raise ValueError(f"Base scenario not found: {base_scenario_id}")
        
        base_scenario = self.scenarios[base_scenario_id]
        scenarios = []
        
        for i, data_set in enumerate(data_sets):
            # 変数設定
            old_vars = self.variables.copy()
            self.variables.update(data_set)
            
            # シナリオ複製と変数展開
            scenario_data = {
                'id': f"{base_scenario.scenario_id}_data_{i}",
                'name': f"{base_scenario.name} - Dataset {i}",
                'description': base_scenario.description,
                'user_profile': base_scenario.user_profile,
                'steps': [],
                'setup': base_scenario.setup_commands,
                'teardown': base_scenario.teardown_commands,
                'environment': base_scenario.environment,
                'timeout': base_scenario.timeout,
                'tags': base_scenario.tags + ['data_driven']
            }
            
            # ステップ複製と変数展開
            for step in base_scenario.steps:
                step_data = {
                    'id': f"{step.step_id}_data_{i}",
                    'action': step.action.value,
                    'target': self._expand_variables(step.target),
                    'value': self._expand_variables(step.value) if step.value else None,
                    'expected': self._expand_variables(step.expected) if step.expected else None,
                    'timeout': step.timeout,
                    'description': step.description,
                    'critical': step.critical
                }
                scenario_data['steps'].append(step_data)
            
            # シナリオ構築
            scenario = self._build_scenario(scenario_data)
            scenarios.append(scenario)
            
            # 変数復元
            self.variables = old_vars
        
        return scenarios
    
    def generate_random_scenario(self,
                                scenario_type: str,
                                step_count: int = 10) -> TestScenario:
        """ランダムシナリオ生成"""
        scenario_id = f"random_{scenario_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # シナリオタイプ別のアクション定義
        action_weights = {
            'developer': {
                UserAction.COMMAND: 0.4,
                UserAction.INPUT: 0.3,
                UserAction.VERIFY: 0.2,
                UserAction.WAIT: 0.1
            },
            'tester': {
                UserAction.VERIFY: 0.4,
                UserAction.COMMAND: 0.2,
                UserAction.INPUT: 0.2,
                UserAction.WAIT: 0.2
            },
            'user': {
                UserAction.CLICK: 0.3,
                UserAction.INPUT: 0.3,
                UserAction.NAVIGATE: 0.2,
                UserAction.WAIT: 0.2
            }
        }
        
        weights = action_weights.get(scenario_type, action_weights['developer'])
        actions = list(weights.keys())
        probabilities = list(weights.values())
        
        # ステップ生成
        steps = []
        for i in range(step_count):
            action = random.choices(actions, weights=probabilities)[0]
            
            step = UserStep(
                step_id=f"random_{i:03d}",
                action=action,
                target=self._generate_random_target(action),
                value=self._generate_random_value(action),
                expected=self._generate_random_expected(action) if random.random() > 0.5 else None,
                timeout=random.uniform(5.0, 60.0),
                description=f"Random {action.value} step",
                critical=random.random() > 0.3
            )
            
            steps.append(step)
        
        return TestScenario(
            scenario_id=scenario_id,
            name=f"Random {scenario_type.title()} Scenario",
            description=f"Randomly generated {scenario_type} scenario with {step_count} steps",
            user_profile={'role': scenario_type, 'generated': True},
            steps=steps,
            tags=['random', scenario_type, 'generated']
        )
    
    def _generate_random_target(self, action: UserAction) -> str:
        """ランダムターゲット生成"""
        targets = {
            UserAction.COMMAND: ["command_tower", "agent_coordinator", "quality_guardian"],
            UserAction.INPUT: ["test_file.py", "config.json", "data.csv"],
            UserAction.VERIFY: ["file:output.txt", "process:server", "http://localhost:8080"],
            UserAction.CLICK: ["#submit-button", ".nav-link", "button[type=submit]"],
            UserAction.NAVIGATE: ["/home", "/dashboard", "/settings"],
            UserAction.UPLOAD: ["input.txt", "image.png", "document.pdf"],
            UserAction.DOWNLOAD: ["report.pdf", "export.csv", "backup.zip"],
            UserAction.WAIT: ["page_load", "process_complete", "animation"]
        }
        
        return random.choice(targets.get(action, ["default_target"]))
    
    def _generate_random_value(self, action: UserAction) -> Any:
        """ランダム値生成"""
        if action == UserAction.COMMAND:
            commands = ["analyze", "optimize", "test", "deploy", "monitor"]
            return f"{random.choice(commands)} {self._random_string(8)}"
        elif action == UserAction.INPUT:
            return self._random_string(20)
        elif action == UserAction.WAIT:
            return random.uniform(0.5, 5.0)
        else:
            return None
    
    def _generate_random_expected(self, action: UserAction) -> Any:
        """ランダム期待値生成"""
        if action == UserAction.COMMAND:
            return {'status': random.choice(['completed', 'success', 'ok'])}
        elif action == UserAction.VERIFY:
            return self._random_string(10)
        else:
            return None
    
    def _random_string(self, length: int) -> str:
        """ランダム文字列生成"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def export_scenario(self, scenario: TestScenario, format: str = 'yaml') -> str:
        """シナリオエクスポート"""
        data = {
            'id': scenario.scenario_id,
            'name': scenario.name,
            'description': scenario.description,
            'user_profile': scenario.user_profile,
            'steps': [
                {
                    'id': step.step_id,
                    'action': step.action.value,
                    'target': step.target,
                    'value': step.value,
                    'expected': step.expected,
                    'timeout': step.timeout,
                    'description': step.description,
                    'critical': step.critical
                }
                for step in scenario.steps
            ],
            'setup': scenario.setup_commands,
            'teardown': scenario.teardown_commands,
            'environment': scenario.environment,
            'timeout': scenario.timeout,
            'tags': scenario.tags
        }
        
        if format == 'yaml':
            return yaml.dump(data, default_flow_style=False)
        elif format == 'json':
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def validate_scenario(self, scenario: TestScenario) -> List[str]:
        """シナリオ検証"""
        issues = []
        
        # 基本検証
        if not scenario.scenario_id:
            issues.append("Scenario ID is required")
        if not scenario.name:
            issues.append("Scenario name is required")
        if not scenario.steps:
            issues.append("Scenario must have at least one step")
        
        # ステップ検証
        step_ids = set()
        for i, step in enumerate(scenario.steps):
            if not step.step_id:
                issues.append(f"Step {i} is missing ID")
            elif step.step_id in step_ids:
                issues.append(f"Duplicate step ID: {step.step_id}")
            else:
                step_ids.add(step.step_id)
            
            if not step.target:
                issues.append(f"Step {step.step_id} is missing target")
            
            # アクション別検証
            if step.action == UserAction.COMMAND and not step.value:
                issues.append(f"Command step {step.step_id} is missing command value")
            elif step.action == UserAction.INPUT and step.value is None:
                issues.append(f"Input step {step.step_id} is missing input value")
            elif step.action == UserAction.VERIFY and not step.expected:
                issues.append(f"Verify step {step.step_id} is missing expected value")
        
        return issues


# サンプルYAML定義
SAMPLE_SCENARIO_YAML = """
variables:
  project_name: test_project
  api_endpoint: http://localhost:8080

templates:
  code_quality_check:
    steps:
      - id: quality_check_01
        action: command
        target: command_tower
        value: analyze_code ${project_path}
        expected:
          status: completed
      - id: quality_check_02
        action: verify
        target: file:${project_path}/quality_report.json
        expected: quality_score

scenarios:
  - id: full_development_cycle
    name: Full Development Cycle
    description: Complete development workflow from project creation to deployment
    user_profile:
      role: developer
      experience: senior
    
    steps:
      - id: create_project
        action: command
        target: command_tower
        value: create_project ${project_name}
        expected:
          status: completed
      
      - template: code_quality_check
        params:
          project_path: ${project_name}
      
      - loop:
          type: list
          var: file_name
          items: [main.py, utils.py, tests.py]
        steps:
          - id: create_file_${file_name}
            action: input
            target: ${project_name}/${file_name}
            value: "# ${file_name} content"
      
      - condition: "${api_endpoint} != ''"
        then:
          - id: test_api
            action: verify
            target: ${api_endpoint}/health
            expected: ok
        else:
          - id: skip_api
            action: wait
            target: skip
            value: 0
"""


if __name__ == "__main__":
    # シナリオビルダーのデモ
    builder = ScenarioBuilder()
    
    # YAMLからシナリオロード
    yaml_path = Path("sample_scenarios.yaml")
    yaml_path.write_text(SAMPLE_SCENARIO_YAML)
    
    scenarios = builder.load_scenario_yaml(yaml_path)
    print(f"Loaded {len(scenarios)} scenarios from YAML")
    
    # データ駆動シナリオ生成
    data_sets = [
        {'project_name': 'project_a', 'language': 'python'},
        {'project_name': 'project_b', 'language': 'javascript'},
        {'project_name': 'project_c', 'language': 'go'}
    ]
    
    if scenarios:
        data_driven_scenarios = builder.create_data_driven_scenario(
            scenarios[0].scenario_id,
            data_sets
        )
        print(f"Generated {len(data_driven_scenarios)} data-driven scenarios")
    
    # ランダムシナリオ生成
    random_scenario = builder.generate_random_scenario('developer', step_count=5)
    print(f"Generated random scenario: {random_scenario.name}")
    
    # シナリオエクスポート
    export_yaml = builder.export_scenario(random_scenario, format='yaml')
    print("\nExported scenario (YAML):")
    print(export_yaml)
    
    # クリーンアップ
    yaml_path.unlink()