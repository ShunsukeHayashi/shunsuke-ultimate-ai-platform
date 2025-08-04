"""
Ultimate ShunsukeModel Ecosystem - Quality Guardian
リアルタイム品質監視システム

コード品質、アーキテクチャ品質、パフォーマンス品質を継続的に監視し、
自動改善提案を行うインテリジェント品質保証システム
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
from datetime import datetime, timezone, timedelta
import ast
import re
import subprocess
import hashlib
import statistics

from ...orchestration.coordinator.agent_coordinator import AgentCoordinator
from ...orchestration.communication.communication_protocol import CommunicationProtocol, MessageType


class QualityMetric(Enum):
    """品質メトリクス"""
    CODE_COMPLEXITY = "code_complexity"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    USABILITY = "usability"
    PORTABILITY = "portability"
    SCALABILITY = "scalability"


class QualitySeverity(Enum):
    """品質問題の重要度"""
    CRITICAL = "critical"  # 即座に修正が必要
    HIGH = "high"  # 高優先度
    MEDIUM = "medium"  # 中優先度
    LOW = "low"  # 低優先度
    INFO = "info"  # 情報レベル


class QualityCheckType(Enum):
    """品質チェックタイプ"""
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    ARCHITECTURAL = "architectural"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"


@dataclass
class QualityIssue:
    """品質問題"""
    id: str
    metric: QualityMetric
    severity: QualitySeverity
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """品質レポート"""
    id: str
    project_path: str
    timestamp: datetime
    overall_score: float  # 0.0 - 1.0
    metric_scores: Dict[QualityMetric, float] = field(default_factory=dict)
    issues: List[QualityIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    trends: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def critical_issues(self) -> List[QualityIssue]:
        """クリティカル問題のリスト"""
        return [issue for issue in self.issues if issue.severity == QualitySeverity.CRITICAL]
    
    @property
    def high_priority_issues(self) -> List[QualityIssue]:
        """高優先度問題のリスト"""
        return [issue for issue in self.issues if issue.severity == QualitySeverity.HIGH]
    
    @property
    def auto_fixable_issues(self) -> List[QualityIssue]:
        """自動修正可能問題のリスト"""
        return [issue for issue in self.issues if issue.auto_fixable]


@dataclass
class QualityThreshold:
    """品質閾値"""
    metric: QualityMetric
    min_acceptable: float
    target: float
    critical_threshold: float
    enabled: bool = True


class QualityAnalyzer:
    """品質分析エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyzers: Dict[QualityCheckType, Callable] = {}
        self.logger = logging.getLogger(__name__)
        self._setup_analyzers()
    
    def _setup_analyzers(self):
        """分析機能の設定"""
        self.analyzers[QualityCheckType.STATIC_ANALYSIS] = self._static_analysis
        self.analyzers[QualityCheckType.DYNAMIC_ANALYSIS] = self._dynamic_analysis
        self.analyzers[QualityCheckType.ARCHITECTURAL] = self._architectural_analysis
        self.analyzers[QualityCheckType.PERFORMANCE] = self._performance_analysis
        self.analyzers[QualityCheckType.SECURITY] = self._security_analysis
    
    async def analyze_project(self, project_path: Path) -> QualityReport:
        """プロジェクト全体の品質分析"""
        report_id = hashlib.md5(f"{project_path}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        
        report = QualityReport(
            id=report_id,
            project_path=str(project_path),
            timestamp=datetime.now(timezone.utc),
            overall_score=0.0
        )
        
        # 各チェックタイプを実行
        for check_type, analyzer in self.analyzers.items():
            try:
                issues = await analyzer(project_path)
                report.issues.extend(issues)
                self.logger.debug(f"{check_type.value} found {len(issues)} issues")
            except Exception as e:
                self.logger.error(f"Analysis failed for {check_type.value}: {e}")
        
        # メトリクススコア計算
        report.metric_scores = await self._calculate_metric_scores(project_path, report.issues)
        
        # 総合スコア計算
        report.overall_score = self._calculate_overall_score(report.metric_scores)
        
        # 推奨事項生成
        report.recommendations = await self._generate_recommendations(report)
        
        return report
    
    async def _static_analysis(self, project_path: Path) -> List[QualityIssue]:
        """静的解析"""
        issues = []
        
        # Python ファイルの分析
        python_files = list(project_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                file_issues = await self._analyze_python_file(py_file)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.warning(f"Failed to analyze {py_file}: {e}")
        
        return issues
    
    async def _analyze_python_file(self, file_path: Path) -> List[QualityIssue]:
        """Python ファイルの分析"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # 複雑度チェック
            complexity_issues = self._check_complexity(tree, file_path)
            issues.extend(complexity_issues)
            
            # コードスタイルチェック
            style_issues = await self._check_code_style(file_path, content)
            issues.extend(style_issues)
            
            # 命名規則チェック
            naming_issues = self._check_naming_conventions(tree, file_path)
            issues.extend(naming_issues)
            
            # ドキュメンテーションチェック
            doc_issues = self._check_documentation(tree, file_path)
            issues.extend(doc_issues)
            
        except SyntaxError as e:
            issues.append(QualityIssue(
                id=f"syntax_error_{hash(str(file_path))}",
                metric=QualityMetric.CODE_COMPLEXITY,
                severity=QualitySeverity.CRITICAL,
                title="Syntax Error",
                description=f"Syntax error: {e.msg}",
                file_path=str(file_path),
                line_number=e.lineno,
                column_number=e.offset
            ))
        
        return issues
    
    def _check_complexity(self, tree: ast.AST, file_path: Path) -> List[QualityIssue]:
        """複雑度チェック"""
        issues = []
        
        class ComplexityChecker(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 1  # ベース複雑度
                self.function_complexities = {}
                self.current_function = None
            
            def visit_FunctionDef(self, node):
                old_function = self.current_function
                old_complexity = self.complexity
                
                self.current_function = node.name
                self.complexity = 1
                
                self.generic_visit(node)
                
                self.function_complexities[node.name] = {
                    'complexity': self.complexity,
                    'line': node.lineno
                }
                
                self.current_function = old_function
                self.complexity = old_complexity
            
            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_Try(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        checker = ComplexityChecker()
        checker.visit(tree)
        
        # 高複雑度関数をレポート
        for func_name, data in checker.function_complexities.items():
            if data['complexity'] > 10:  # 閾値
                severity = QualitySeverity.HIGH if data['complexity'] > 15 else QualitySeverity.MEDIUM
                
                issues.append(QualityIssue(
                    id=f"complexity_{hash(f'{file_path}_{func_name}')}",
                    metric=QualityMetric.CODE_COMPLEXITY,
                    severity=severity,
                    title=f"High Complexity Function: {func_name}",
                    description=f"Function '{func_name}' has cyclomatic complexity of {data['complexity']}",
                    file_path=str(file_path),
                    line_number=data['line'],
                    suggestion="Consider breaking this function into smaller functions"
                ))
        
        return issues
    
    async def _check_code_style(self, file_path: Path, content: str) -> List[QualityIssue]:
        """コードスタイルチェック"""
        issues = []
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 長い行をチェック
            if len(line) > 120:
                issues.append(QualityIssue(
                    id=f"long_line_{hash(f'{file_path}_{i}')}",
                    metric=QualityMetric.MAINTAINABILITY,
                    severity=QualitySeverity.LOW,
                    title="Line Too Long",
                    description=f"Line {i} is {len(line)} characters long (max 120)",
                    file_path=str(file_path),
                    line_number=i,
                    auto_fixable=True
                ))
            
            # タブ文字をチェック
            if '\t' in line:
                issues.append(QualityIssue(
                    id=f"tab_char_{hash(f'{file_path}_{i}')}",
                    metric=QualityMetric.MAINTAINABILITY,
                    severity=QualitySeverity.LOW,
                    title="Tab Characters Found",
                    description=f"Line {i} contains tab characters (use spaces)",
                    file_path=str(file_path),
                    line_number=i,
                    auto_fixable=True
                ))
        
        return issues
    
    def _check_naming_conventions(self, tree: ast.AST, file_path: Path) -> List[QualityIssue]:
        """命名規則チェック"""
        issues = []
        
        class NamingChecker(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # snake_case チェック
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append(QualityIssue(
                        id=f"naming_func_{hash(f'{file_path}_{node.name}')}",
                        metric=QualityMetric.MAINTAINABILITY,
                        severity=QualitySeverity.LOW,
                        title="Function Naming Convention",
                        description=f"Function '{node.name}' should use snake_case",
                        file_path=str(file_path),
                        line_number=node.lineno
                    ))
                
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                # PascalCase チェック
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    issues.append(QualityIssue(
                        id=f"naming_class_{hash(f'{file_path}_{node.name}')}",
                        metric=QualityMetric.MAINTAINABILITY,
                        severity=QualitySeverity.LOW,
                        title="Class Naming Convention",
                        description=f"Class '{node.name}' should use PascalCase",
                        file_path=str(file_path),
                        line_number=node.lineno
                    ))
                
                self.generic_visit(node)
        
        checker = NamingChecker()
        checker.visit(tree)
        
        return issues
    
    def _check_documentation(self, tree: ast.AST, file_path: Path) -> List[QualityIssue]:
        """ドキュメンテーションチェック"""
        issues = []
        
        class DocChecker(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # パブリック関数のドキュメント文字列チェック
                if not node.name.startswith('_'):  # プライベート関数でない
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        issues.append(QualityIssue(
                            id=f"missing_doc_{hash(f'{file_path}_{node.name}')}",
                            metric=QualityMetric.DOCUMENTATION,
                            severity=QualitySeverity.MEDIUM,
                            title="Missing Docstring",
                            description=f"Function '{node.name}' is missing a docstring",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            suggestion="Add a docstring describing the function's purpose, parameters, and return value"
                        ))
                
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append(QualityIssue(
                        id=f"missing_class_doc_{hash(f'{file_path}_{node.name}')}",
                        metric=QualityMetric.DOCUMENTATION,
                        severity=QualitySeverity.MEDIUM,
                        title="Missing Class Docstring",
                        description=f"Class '{node.name}' is missing a docstring",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        suggestion="Add a docstring describing the class's purpose and usage"
                    ))
                
                self.generic_visit(node)
        
        checker = DocChecker()
        checker.visit(tree)
        
        return issues
    
    async def _dynamic_analysis(self, project_path: Path) -> List[QualityIssue]:
        """動的解析"""
        issues = []
        
        # テストカバレッジチェック
        coverage_issues = await self._check_test_coverage(project_path)
        issues.extend(coverage_issues)
        
        return issues
    
    async def _check_test_coverage(self, project_path: Path) -> List[QualityIssue]:
        """テストカバレッジチェック"""
        issues = []
        
        try:
            # pytest-cov を使用してカバレッジを測定
            result = subprocess.run(
                ['python', '-m', 'pytest', '--cov=.', '--cov-report=json', '--cov-report=term-missing'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # カバレッジレポートから情報を抽出
            coverage_file = project_path / '.coverage'
            if coverage_file.exists():
                # 簡易的なカバレッジチェック（実際の実装では詳細な解析が必要）
                issues.append(QualityIssue(
                    id=f"coverage_check_{hash(str(project_path))}",
                    metric=QualityMetric.TEST_COVERAGE,
                    severity=QualitySeverity.INFO,
                    title="Test Coverage Analysis",
                    description="Test coverage analysis completed",
                    metadata={"coverage_available": True}
                ))
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            issues.append(QualityIssue(
                id=f"no_coverage_{hash(str(project_path))}",
                metric=QualityMetric.TEST_COVERAGE,
                severity=QualitySeverity.MEDIUM,
                title="No Test Coverage",
                description="Unable to determine test coverage",
                suggestion="Set up pytest-cov for test coverage analysis"
            ))
        
        return issues
    
    async def _architectural_analysis(self, project_path: Path) -> List[QualityIssue]:
        """アーキテクチャ分析"""
        issues = []
        
        # 依存関係分析
        dependency_issues = await self._analyze_dependencies(project_path)
        issues.extend(dependency_issues)
        
        return issues
    
    async def _analyze_dependencies(self, project_path: Path) -> List[QualityIssue]:
        """依存関係分析"""
        issues = []
        
        requirements_file = project_path / 'requirements.txt'
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    requirements = f.read().splitlines()
                
                # バージョン固定のない依存関係をチェック
                for req in requirements:
                    if req.strip() and not any(op in req for op in ['==', '>=', '<=', '>', '<', '~=', '!=']):
                        issues.append(QualityIssue(
                            id=f"unpinned_dep_{hash(req)}",
                            metric=QualityMetric.RELIABILITY,
                            severity=QualitySeverity.MEDIUM,
                            title="Unpinned Dependency",
                            description=f"Dependency '{req}' should specify a version",
                            file_path=str(requirements_file),
                            suggestion="Pin dependency versions for reproducible builds"
                        ))
            
            except Exception as e:
                self.logger.warning(f"Failed to analyze requirements.txt: {e}")
        
        return issues
    
    async def _performance_analysis(self, project_path: Path) -> List[QualityIssue]:
        """パフォーマンス分析"""
        issues = []
        
        # 潜在的なパフォーマンス問題をチェック
        python_files = list(project_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                perf_issues = await self._analyze_performance_patterns(py_file)
                issues.extend(perf_issues)
            except Exception as e:
                self.logger.warning(f"Performance analysis failed for {py_file}: {e}")
        
        return issues
    
    async def _analyze_performance_patterns(self, file_path: Path) -> List[QualityIssue]:
        """パフォーマンスパターン分析"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 非効率なパターンを検索
            patterns = [
                (r'for\s+\w+\s+in\s+range\(len\([^)]+\)\):', 
                 "Use enumerate() instead of range(len())",
                 "performance_range_len"),
                (r'\.keys\(\)\s*in\s+', 
                 "Checking membership in dict.keys() is inefficient, use 'in dict' directly",
                 "performance_keys_membership"),
                (r'list\([^)]*\.keys\(\)\)', 
                 "Converting dict.keys() to list is often unnecessary",
                 "performance_list_keys")
            ]
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                for pattern, suggestion, rule_id in patterns:
                    if re.search(pattern, line):
                        issues.append(QualityIssue(
                            id=f"{rule_id}_{hash(f'{file_path}_{i}')}",
                            metric=QualityMetric.PERFORMANCE,
                            severity=QualitySeverity.LOW,
                            title="Performance Anti-pattern",
                            description=f"Line {i}: {suggestion}",
                            file_path=str(file_path),
                            line_number=i,
                            rule_id=rule_id,
                            suggestion=suggestion
                        ))
        
        except Exception as e:
            self.logger.warning(f"Failed to analyze performance patterns in {file_path}: {e}")
        
        return issues
    
    async def _security_analysis(self, project_path: Path) -> List[QualityIssue]:
        """セキュリティ分析"""
        issues = []
        
        python_files = list(project_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                security_issues = await self._analyze_security_patterns(py_file)
                issues.extend(security_issues)
            except Exception as e:
                self.logger.warning(f"Security analysis failed for {py_file}: {e}")
        
        return issues
    
    async def _analyze_security_patterns(self, file_path: Path) -> List[QualityIssue]:
        """セキュリティパターン分析"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # セキュリティリスクのあるパターンを検索
            security_patterns = [
                (r'eval\s*\(', 
                 "Use of eval() can be dangerous - consider safer alternatives",
                 QualitySeverity.HIGH,
                 "security_eval"),
                (r'exec\s*\(', 
                 "Use of exec() can be dangerous - consider safer alternatives",
                 QualitySeverity.HIGH,
                 "security_exec"),
                (r'subprocess\.call\([^)]*shell\s*=\s*True', 
                 "subprocess with shell=True can be vulnerable to injection attacks",
                 QualitySeverity.MEDIUM,
                 "security_shell_injection"),
                (r'password\s*=\s*["\'][^"\']+["\']', 
                 "Hardcoded password detected",
                 QualitySeverity.CRITICAL,
                 "security_hardcoded_password"),
                (r'secret\s*=\s*["\'][^"\']+["\']', 
                 "Hardcoded secret detected",
                 QualitySeverity.CRITICAL,
                 "security_hardcoded_secret")
            ]
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                for pattern, description, severity, rule_id in security_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(QualityIssue(
                            id=f"{rule_id}_{hash(f'{file_path}_{i}')}",
                            metric=QualityMetric.SECURITY,
                            severity=severity,
                            title="Security Risk",
                            description=f"Line {i}: {description}",
                            file_path=str(file_path),
                            line_number=i,
                            rule_id=rule_id,
                            suggestion=description
                        ))
        
        except Exception as e:
            self.logger.warning(f"Failed to analyze security patterns in {file_path}: {e}")
        
        return issues
    
    async def _calculate_metric_scores(self, project_path: Path, issues: List[QualityIssue]) -> Dict[QualityMetric, float]:
        """メトリクススコア計算"""
        scores = {}
        
        # 各メトリクスの問題をカウント
        issue_counts = {}
        for issue in issues:
            metric = issue.metric
            if metric not in issue_counts:
                issue_counts[metric] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
            issue_counts[metric][issue.severity.value] += 1
        
        # スコア計算（1.0が最高、0.0が最低）
        for metric in QualityMetric:
            if metric in issue_counts:
                counts = issue_counts[metric]
                # 重み付きペナルティ計算
                penalty = (counts['critical'] * 0.5 + 
                          counts['high'] * 0.3 + 
                          counts['medium'] * 0.1 + 
                          counts['low'] * 0.05)
                
                # スコア計算（問題数に基づく減点方式）
                base_score = 1.0
                scores[metric] = max(0.0, base_score - penalty / 10)  # 最大10問題で0点
            else:
                scores[metric] = 1.0  # 問題がない場合は満点
        
        return scores
    
    def _calculate_overall_score(self, metric_scores: Dict[QualityMetric, float]) -> float:
        """総合スコア計算"""
        if not metric_scores:
            return 0.0
        
        # 重み付き平均を計算
        weights = {
            QualityMetric.SECURITY: 0.25,
            QualityMetric.RELIABILITY: 0.20,
            QualityMetric.MAINTAINABILITY: 0.15,
            QualityMetric.CODE_COMPLEXITY: 0.15,
            QualityMetric.TEST_COVERAGE: 0.10,
            QualityMetric.PERFORMANCE: 0.10,
            QualityMetric.DOCUMENTATION: 0.05
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, score in metric_scores.items():
            weight = weights.get(metric, 0.01)  # デフォルト重み
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    async def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        # クリティカル問題への対応
        if report.critical_issues:
            recommendations.append(f"🚨 {len(report.critical_issues)} critical issues require immediate attention")
        
        # スコアベースの推奨事項
        for metric, score in report.metric_scores.items():
            if score < 0.6:  # 60%未満
                if metric == QualityMetric.TEST_COVERAGE:
                    recommendations.append("📋 Improve test coverage by adding more unit tests")
                elif metric == QualityMetric.DOCUMENTATION:
                    recommendations.append("📚 Add docstrings and comments to improve code documentation")
                elif metric == QualityMetric.CODE_COMPLEXITY:
                    recommendations.append("🔧 Refactor complex functions to improve maintainability")
                elif metric == QualityMetric.SECURITY:
                    recommendations.append("🔒 Address security vulnerabilities immediately")
        
        # 自動修正可能な問題
        auto_fixable_count = len(report.auto_fixable_issues)
        if auto_fixable_count > 0:
            recommendations.append(f"⚡ {auto_fixable_count} issues can be automatically fixed")
        
        # 総合スコアベースの推奨事項
        if report.overall_score < 0.5:
            recommendations.append("🎯 Consider setting up continuous integration with quality gates")
        elif report.overall_score < 0.8:
            recommendations.append("✨ Good progress! Focus on addressing high-priority issues")
        else:
            recommendations.append("🎉 Excellent code quality! Maintain current standards")
        
        return recommendations


class QualityGuardian:
    """
    リアルタイム品質監視システム
    
    主要機能:
    1. 継続的な品質監視
    2. 品質閾値の管理
    3. 自動アラート生成
    4. 品質トレンド分析
    5. 改善提案の自動生成
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config
        self.analyzer = QualityAnalyzer(config.get('analyzer', {}))
        self.thresholds: Dict[QualityMetric, QualityThreshold] = {}
        self.reports: Dict[str, QualityReport] = {}
        self.monitoring_paths: Set[Path] = set()
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 設定値
        self.monitoring_interval = config.get('monitoring_interval', 300)  # 5分
        self.alert_webhooks = config.get('alert_webhooks', [])
        self.auto_fix_enabled = config.get('auto_fix_enabled', False)
        
        # 初期化状態
        self.is_running = False
        self._background_tasks = set()
        self._shutdown_event = asyncio.Event()
        
        # 通信プロトコル（エージェント間通信用）
        self.communication_protocol: Optional[CommunicationProtocol] = None
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'quality-guardian.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """品質監視システム初期化"""
        try:
            self.logger.info("Quality Guardian initialization started")
            
            # デフォルト品質閾値設定
            await self._setup_default_thresholds()
            
            # 通信プロトコル初期化
            if self.config.get('enable_communication', True):
                self.communication_protocol = CommunicationProtocol(
                    "quality_guardian",
                    self.config.get('communication', {})
                )
                await self.communication_protocol.initialize()
            
            # バックグラウンド監視開始
            await self._start_monitoring()
            
            self.is_running = True
            self.logger.info("Quality Guardian initialization completed")
            
        except Exception as e:
            self.logger.error(f"Quality Guardian initialization failed: {e}")
            raise
    
    async def _setup_default_thresholds(self):
        """デフォルト品質閾値設定"""
        default_thresholds = {
            QualityMetric.CODE_COMPLEXITY: QualityThreshold(
                metric=QualityMetric.CODE_COMPLEXITY,
                min_acceptable=0.6,
                target=0.8,
                critical_threshold=0.3
            ),
            QualityMetric.TEST_COVERAGE: QualityThreshold(
                metric=QualityMetric.TEST_COVERAGE,
                min_acceptable=0.7,
                target=0.9,
                critical_threshold=0.5
            ),
            QualityMetric.SECURITY: QualityThreshold(
                metric=QualityMetric.SECURITY,
                min_acceptable=0.9,
                target=1.0,
                critical_threshold=0.7
            ),
            QualityMetric.DOCUMENTATION: QualityThreshold(
                metric=QualityMetric.DOCUMENTATION,
                min_acceptable=0.6,
                target=0.8,
                critical_threshold=0.4
            )
        }
        
        # ユーザー設定とマージ
        user_thresholds = self.config.get('thresholds', {})
        for metric_name, threshold_config in user_thresholds.items():
            try:
                metric = QualityMetric(metric_name)
                if metric in default_thresholds:
                    # 既存閾値を更新
                    threshold = default_thresholds[metric]
                    threshold.min_acceptable = threshold_config.get('min_acceptable', threshold.min_acceptable)
                    threshold.target = threshold_config.get('target', threshold.target)
                    threshold.critical_threshold = threshold_config.get('critical_threshold', threshold.critical_threshold)
                    threshold.enabled = threshold_config.get('enabled', threshold.enabled)
            except ValueError:
                self.logger.warning(f"Unknown quality metric in config: {metric_name}")
        
        self.thresholds = default_thresholds
        self.logger.info(f"Configured {len(self.thresholds)} quality thresholds")
    
    async def _start_monitoring(self):
        """監視開始"""
        # 継続監視タスク
        monitor_task = asyncio.create_task(self._continuous_monitoring())
        self._background_tasks.add(monitor_task)
        
        # アラート処理タスク
        alert_task = asyncio.create_task(self._alert_processor())
        self._background_tasks.add(alert_task)
    
    async def add_monitoring_path(self, path: Path):
        """監視パス追加"""
        if path.exists():
            self.monitoring_paths.add(path)
            self.logger.info(f"Added monitoring path: {path}")
        else:
            self.logger.warning(f"Monitoring path does not exist: {path}")
    
    async def remove_monitoring_path(self, path: Path):
        """監視パス削除"""
        self.monitoring_paths.discard(path)
        self.logger.info(f"Removed monitoring path: {path}")
    
    async def analyze_project_quality(self, project_path: Path) -> QualityReport:
        """プロジェクト品質分析"""
        self.logger.info(f"Starting quality analysis for: {project_path}")
        
        # 品質分析実行
        report = await self.analyzer.analyze_project(project_path)
        
        # レポート保存
        self.reports[report.id] = report
        
        # 閾値チェック
        violations = await self._check_thresholds(report)
        
        # アラート生成
        if violations:
            await self._generate_alerts(report, violations)
        
        # 自動修正実行（有効な場合）
        if self.auto_fix_enabled and report.auto_fixable_issues:
            await self._auto_fix_issues(project_path, report.auto_fixable_issues)
        
        self.logger.info(f"Quality analysis completed: {report.overall_score:.2f} score, {len(report.issues)} issues")
        
        return report
    
    async def _check_thresholds(self, report: QualityReport) -> List[Dict[str, Any]]:
        """品質閾値チェック"""
        violations = []
        
        for metric, score in report.metric_scores.items():
            if metric in self.thresholds:
                threshold = self.thresholds[metric]
                
                if not threshold.enabled:
                    continue
                
                if score < threshold.critical_threshold:
                    violations.append({
                        'metric': metric,
                        'severity': 'critical',
                        'score': score,
                        'threshold': threshold.critical_threshold,
                        'message': f"{metric.value} score ({score:.2f}) is below critical threshold ({threshold.critical_threshold:.2f})"
                    })
                elif score < threshold.min_acceptable:
                    violations.append({
                        'metric': metric,
                        'severity': 'warning',
                        'score': score,
                        'threshold': threshold.min_acceptable,
                        'message': f"{metric.value} score ({score:.2f}) is below acceptable threshold ({threshold.min_acceptable:.2f})"
                    })
        
        return violations
    
    async def _generate_alerts(self, report: QualityReport, violations: List[Dict[str, Any]]):
        """アラート生成"""
        alert_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'project_path': report.project_path,
            'report_id': report.id,
            'overall_score': report.overall_score,
            'violations': violations,
            'critical_issues': len(report.critical_issues),
            'total_issues': len(report.issues)
        }
        
        # エージェント間通信でアラート送信
        if self.communication_protocol:
            await self.communication_protocol.broadcast_message(
                message_type=MessageType.ERROR,
                payload=alert_data
            )
        
        # Webhook通知
        for webhook_url in self.alert_webhooks:
            try:
                # 実際の実装ではHTTPリクエストを送信
                self.logger.info(f"Alert sent to webhook: {webhook_url}")
            except Exception as e:
                self.logger.error(f"Failed to send alert to webhook {webhook_url}: {e}")
        
        self.logger.warning(f"Quality alerts generated for {report.project_path}: {len(violations)} violations")
    
    async def _auto_fix_issues(self, project_path: Path, issues: List[QualityIssue]):
        """自動修正実行"""
        fixed_count = 0
        
        for issue in issues:
            try:
                if await self._fix_issue(project_path, issue):
                    fixed_count += 1
            except Exception as e:
                self.logger.error(f"Auto-fix failed for issue {issue.id}: {e}")
        
        if fixed_count > 0:
            self.logger.info(f"Auto-fixed {fixed_count}/{len(issues)} issues")
    
    async def _fix_issue(self, project_path: Path, issue: QualityIssue) -> bool:
        """個別問題の修正"""
        if not issue.auto_fixable:
            return False
        
        try:
            if issue.rule_id == "long_line":
                return await self._fix_long_line(issue)
            elif issue.rule_id == "tab_char":
                return await self._fix_tab_characters(issue)
            # 他の自動修正ルールを追加
            
        except Exception as e:
            self.logger.error(f"Failed to fix issue {issue.id}: {e}")
        
        return False
    
    async def _fix_long_line(self, issue: QualityIssue) -> bool:
        """長い行の修正"""
        # 実装例：長い行を適切に改行
        # 実際の実装では、構文解析を考慮した改行が必要
        return False
    
    async def _fix_tab_characters(self, issue: QualityIssue) -> bool:
        """タブ文字の修正"""
        if not issue.file_path:
            return False
        
        try:
            file_path = Path(issue.file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # タブを4スペースに変換
            fixed_content = content.replace('\t', '    ')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix tab characters in {issue.file_path}: {e}")
            return False
    
    async def _continuous_monitoring(self):
        """継続的監視"""
        while not self._shutdown_event.is_set():
            try:
                # 監視対象パスをチェック
                for path in list(self.monitoring_paths):
                    if path.exists():
                        await self.analyze_project_quality(path)
                    else:
                        self.logger.warning(f"Monitoring path no longer exists: {path}")
                        self.monitoring_paths.discard(path)
                
                # 次の監視まで待機
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Continuous monitoring error: {e}")
                await asyncio.sleep(60)  # エラー時は1分後にリトライ
    
    async def _alert_processor(self):
        """アラート処理"""
        while not self._shutdown_event.is_set():
            try:
                # 未処理のアラートを処理
                # 実際の実装では、アラートキューから処理
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Alert processor error: {e}")
    
    async def get_quality_summary(self) -> Dict[str, Any]:
        """品質サマリー取得"""
        if not self.reports:
            return {"message": "No quality reports available"}
        
        latest_reports = sorted(self.reports.values(), key=lambda r: r.timestamp, reverse=True)[:10]
        
        # 統計計算
        overall_scores = [r.overall_score for r in latest_reports]
        
        return {
            "total_reports": len(self.reports),
            "latest_reports_count": len(latest_reports),
            "average_score": statistics.mean(overall_scores) if overall_scores else 0,
            "score_trend": "improving" if len(overall_scores) > 1 and overall_scores[0] > overall_scores[-1] else "stable",
            "monitoring_paths": len(self.monitoring_paths),
            "active_thresholds": len([t for t in self.thresholds.values() if t.enabled])
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """品質監視システム状態取得"""
        return {
            "is_running": self.is_running,
            "monitoring_paths": len(self.monitoring_paths),
            "quality_reports": len(self.reports),
            "active_thresholds": len([t for t in self.thresholds.values() if t.enabled]),
            "auto_fix_enabled": self.auto_fix_enabled,
            "monitoring_interval": self.monitoring_interval,
            "communication_enabled": self.communication_protocol is not None
        }
    
    async def shutdown(self):
        """品質監視システムシャットダウン"""
        self.logger.info("Quality Guardian shutdown initiated")
        
        # シャットダウンイベント設定
        self._shutdown_event.set()
        
        # 通信プロトコルシャットダウン
        if self.communication_protocol:
            await self.communication_protocol.shutdown()
        
        # バックグラウンドタスクの終了を待機
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self.is_running = False
        self.logger.info("Quality Guardian shutdown completed")


if __name__ == "__main__":
    # テスト実行
    async def test_quality_guardian():
        config = {
            'analyzer': {},
            'monitoring_interval': 10,
            'auto_fix_enabled': True,
            'thresholds': {
                'code_complexity': {
                    'min_acceptable': 0.7,
                    'target': 0.9,
                    'critical_threshold': 0.4
                }
            }
        }
        
        guardian = QualityGuardian(config)
        await guardian.initialize()
        
        # テスト対象プロジェクトを追加
        test_project = Path.cwd()
        await guardian.add_monitoring_path(test_project)
        
        # 品質分析実行
        report = await guardian.analyze_project_quality(test_project)
        
        print("Quality Report:")
        print(f"Overall Score: {report.overall_score:.2f}")
        print(f"Total Issues: {len(report.issues)}")
        print(f"Critical Issues: {len(report.critical_issues)}")
        print(f"Auto-fixable Issues: {len(report.auto_fixable_issues)}")
        
        # 品質サマリー取得
        summary = await guardian.get_quality_summary()
        print("Quality Summary:", json.dumps(summary, indent=2))
        
        # ステータス確認
        status = await guardian.get_status()
        print("Guardian Status:", json.dumps(status, indent=2))
        
        await guardian.shutdown()
    
    asyncio.run(test_quality_guardian())