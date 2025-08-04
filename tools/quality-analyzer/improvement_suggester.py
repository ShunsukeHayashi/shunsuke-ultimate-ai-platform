"""
Ultimate ShunsukeModel Ecosystem - Improvement Suggester
自動改善提案システム

品質問題を解析し、AIを活用して具体的で実行可能な改善提案を自動生成
コード修正、アーキテクチャ改善、パフォーマンス最適化の提案を提供
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
import ast
import re
from datetime import datetime, timezone
import hashlib
import difflib

from .quality_guardian import QualityIssue, QualityReport, QualityMetric, QualitySeverity
from ...orchestration.communication.communication_protocol import CommunicationProtocol, MessageType


class ImprovementType(Enum):
    """改善タイプ"""
    CODE_REFACTORING = "code_refactoring"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_HARDENING = "security_hardening"
    DOCUMENTATION_ENHANCEMENT = "documentation_enhancement"
    TEST_COVERAGE = "test_coverage"
    ARCHITECTURAL_IMPROVEMENT = "architectural_improvement"
    STYLE_IMPROVEMENT = "style_improvement"
    MAINTAINABILITY = "maintainability"


class ImplementationDifficulty(Enum):
    """実装難易度"""
    TRIVIAL = "trivial"  # 自動修正可能
    EASY = "easy"  # 5分以内
    MODERATE = "moderate"  # 30分以内
    HARD = "hard"  # 数時間
    COMPLEX = "complex"  # 数日以上


class ImprovementPriority(Enum):
    """改善優先度"""
    CRITICAL = 1  # 即座に対応が必要
    HIGH = 2  # 高優先度
    MEDIUM = 3  # 中優先度
    LOW = 4  # 低優先度
    OPTIONAL = 5  # オプショナル


@dataclass
class CodeSuggestion:
    """コード改善提案"""
    id: str
    improvement_type: ImprovementType
    priority: ImprovementPriority
    difficulty: ImplementationDifficulty
    title: str
    description: str
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    original_code: Optional[str] = None
    suggested_code: Optional[str] = None
    explanation: str = ""
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)  # QualityIssue IDs
    auto_applicable: bool = False
    estimated_time_minutes: Optional[int] = None
    impact_score: float = 0.0  # 0.0 - 1.0
    confidence: float = 0.0  # 提案の信頼度 0.0 - 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImprovementPlan:
    """改善計画"""
    id: str
    project_path: str
    quality_report_id: str
    suggestions: List[CodeSuggestion] = field(default_factory=list)
    implementation_order: List[str] = field(default_factory=list)  # suggestion IDs
    estimated_total_time: int = 0  # minutes
    expected_quality_improvement: Dict[QualityMetric, float] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeAnalyzer:
    """コード解析エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def analyze_code_context(self, file_path: Path, line_number: Optional[int] = None) -> Dict[str, Any]:
        """コードコンテキスト分析"""
        context = {
            'file_info': {
                'path': str(file_path),
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'extension': file_path.suffix
            },
            'code_structure': {},
            'dependencies': [],
            'complexity_metrics': {},
            'style_issues': []
        }
        
        if not file_path.exists() or file_path.suffix != '.py':
            return context
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # コード構造分析
            context['code_structure'] = await self._analyze_structure(tree)
            
            # 依存関係分析
            context['dependencies'] = await self._analyze_dependencies(tree)
            
            # 複雑度メトリクス
            context['complexity_metrics'] = await self._calculate_complexity(tree)
            
            # 特定行周辺のコンテキスト
            if line_number:
                context['local_context'] = await self._get_local_context(content, line_number)
        
        except Exception as e:
            self.logger.error(f"Failed to analyze code context for {file_path}: {e}")
        
        return context
    
    async def _analyze_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """コード構造分析"""
        structure = {
            'classes': [],
            'functions': [],
            'imports': [],
            'global_variables': []
        }
        
        class StructureAnalyzer(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                structure['classes'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    'base_classes': [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else []
                })
                self.generic_visit(node)
            
            def visit_FunctionDef(self, node):
                structure['functions'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list] if hasattr(ast, 'unparse') else [],
                    'is_async': isinstance(node, ast.AsyncFunctionDef)
                })
                self.generic_visit(node)
            
            def visit_Import(self, node):
                for alias in node.names:
                    structure['imports'].append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            
            def visit_ImportFrom(self, node):
                for alias in node.names:
                    structure['imports'].append({
                        'module': node.module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
        
        analyzer = StructureAnalyzer()
        analyzer.visit(tree)
        
        return structure
    
    async def _analyze_dependencies(self, tree: ast.AST) -> List[str]:
        """依存関係分析"""
        dependencies = set()
        
        class DependencyExtractor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    dependencies.add(alias.name.split('.')[0])
            
            def visit_ImportFrom(self, node):
                if node.module:
                    dependencies.add(node.module.split('.')[0])
        
        extractor = DependencyExtractor()
        extractor.visit(tree)
        
        return list(dependencies)
    
    async def _calculate_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """複雑度メトリクス計算"""
        metrics = {
            'cyclomatic_complexity': 1,
            'cognitive_complexity': 0,
            'nesting_depth': 0,
            'function_count': 0,
            'class_count': 0
        }
        
        class ComplexityCalculator(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                self.max_depth = 0
            
            def visit_FunctionDef(self, node):
                metrics['function_count'] += 1
                old_depth = self.current_depth
                self.current_depth = 0
                self.generic_visit(node)
                self.current_depth = old_depth
            
            def visit_ClassDef(self, node):
                metrics['class_count'] += 1
                self.generic_visit(node)
            
            def visit_If(self, node):
                metrics['cyclomatic_complexity'] += 1
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            def visit_While(self, node):
                metrics['cyclomatic_complexity'] += 1
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            def visit_For(self, node):
                metrics['cyclomatic_complexity'] += 1
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
        
        calculator = ComplexityCalculator()
        calculator.visit(tree)
        metrics['nesting_depth'] = calculator.max_depth
        
        return metrics
    
    async def _get_local_context(self, content: str, line_number: int) -> Dict[str, Any]:
        """特定行周辺のローカルコンテキスト"""
        lines = content.split('\n')
        start_line = max(0, line_number - 5)
        end_line = min(len(lines), line_number + 5)
        
        return {
            'target_line': line_number,
            'context_lines': lines[start_line:end_line],
            'line_range': (start_line + 1, end_line + 1),
            'indentation': len(lines[line_number - 1]) - len(lines[line_number - 1].lstrip()) if line_number <= len(lines) else 0
        }


class SuggestionGenerator:
    """改善提案生成エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.code_analyzer = CodeAnalyzer(config.get('code_analyzer', {}))
        self.suggestion_templates: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        self._load_suggestion_templates()
    
    def _load_suggestion_templates(self):
        """提案テンプレート読み込み"""
        self.suggestion_templates = {
            'complexity_reduction': {
                'title': 'Reduce Function Complexity',
                'description': 'Break down complex function into smaller, more manageable functions',
                'improvement_type': ImprovementType.CODE_REFACTORING,
                'priority': ImprovementPriority.HIGH,
                'difficulty': ImplementationDifficulty.MODERATE,
                'benefits': [
                    'Improved readability and maintainability',
                    'Easier testing and debugging',
                    'Reduced cognitive load'
                ],
                'risks': [
                    'May introduce new interfaces',
                    'Requires careful refactoring to maintain functionality'
                ]
            },
            'performance_optimization': {
                'title': 'Optimize Performance',
                'description': 'Replace inefficient code patterns with optimized alternatives',
                'improvement_type': ImprovementType.PERFORMANCE_OPTIMIZATION,
                'priority': ImprovementPriority.MEDIUM,
                'difficulty': ImplementationDifficulty.EASY,
                'benefits': [
                    'Improved execution speed',
                    'Reduced resource consumption'
                ],
                'risks': [
                    'May reduce code readability',
                    'Requires performance testing'
                ]
            },
            'security_hardening': {
                'title': 'Security Improvement',
                'description': 'Address security vulnerabilities and harden code',
                'improvement_type': ImprovementType.SECURITY_HARDENING,
                'priority': ImprovementPriority.CRITICAL,
                'difficulty': ImplementationDifficulty.MODERATE,
                'benefits': [
                    'Improved security posture',
                    'Reduced attack surface'
                ],
                'risks': [
                    'May break existing functionality',
                    'Requires security testing'
                ]
            },
            'documentation_enhancement': {
                'title': 'Improve Documentation',
                'description': 'Add or improve code documentation',
                'improvement_type': ImprovementType.DOCUMENTATION_ENHANCEMENT,
                'priority': ImprovementPriority.MEDIUM,
                'difficulty': ImplementationDifficulty.EASY,
                'benefits': [
                    'Improved code understanding',
                    'Better maintainability',
                    'Easier onboarding for new developers'
                ],
                'risks': [
                    'Documentation may become outdated',
                    'Requires ongoing maintenance'
                ]
            }
        }
    
    async def generate_suggestions(self, quality_report: QualityReport) -> List[CodeSuggestion]:
        """品質レポートから改善提案を生成"""
        suggestions = []
        
        # 問題タイプ別にグループ化
        issues_by_type = {}
        for issue in quality_report.issues:
            metric = issue.metric
            if metric not in issues_by_type:
                issues_by_type[metric] = []
            issues_by_type[metric].append(issue)
        
        # 各問題タイプに対する提案生成
        for metric, issues in issues_by_type.items():
            metric_suggestions = await self._generate_metric_suggestions(metric, issues)
            suggestions.extend(metric_suggestions)
        
        # 全体的な改善提案
        holistic_suggestions = await self._generate_holistic_suggestions(quality_report)
        suggestions.extend(holistic_suggestions)
        
        # 提案の優先度付けと重複除去
        suggestions = await self._prioritize_and_deduplicate(suggestions)
        
        return suggestions
    
    async def _generate_metric_suggestions(self, metric: QualityMetric, issues: List[QualityIssue]) -> List[CodeSuggestion]:
        """特定メトリクスに対する提案生成"""
        suggestions = []
        
        if metric == QualityMetric.CODE_COMPLEXITY:
            suggestions.extend(await self._generate_complexity_suggestions(issues))
        elif metric == QualityMetric.PERFORMANCE:
            suggestions.extend(await self._generate_performance_suggestions(issues))
        elif metric == QualityMetric.SECURITY:
            suggestions.extend(await self._generate_security_suggestions(issues))
        elif metric == QualityMetric.DOCUMENTATION:
            suggestions.extend(await self._generate_documentation_suggestions(issues))
        elif metric == QualityMetric.MAINTAINABILITY:
            suggestions.extend(await self._generate_maintainability_suggestions(issues))
        
        return suggestions
    
    async def _generate_complexity_suggestions(self, issues: List[QualityIssue]) -> List[CodeSuggestion]:
        """複雑度改善提案生成"""
        suggestions = []
        
        for issue in issues:
            if not issue.file_path:
                continue
            
            # コードコンテキスト分析
            context = await self.code_analyzer.analyze_code_context(
                Path(issue.file_path), 
                issue.line_number
            )
            
            # 複雑度に基づく提案生成
            complexity = context.get('complexity_metrics', {}).get('cyclomatic_complexity', 0)
            
            if complexity > 15:
                suggestion = await self._create_complexity_reduction_suggestion(issue, context, 'major_refactoring')
            elif complexity > 10:
                suggestion = await self._create_complexity_reduction_suggestion(issue, context, 'moderate_refactoring')
            else:
                suggestion = await self._create_complexity_reduction_suggestion(issue, context, 'minor_refactoring')
            
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    async def _create_complexity_reduction_suggestion(
        self, 
        issue: QualityIssue, 
        context: Dict[str, Any], 
        refactoring_type: str
    ) -> Optional[CodeSuggestion]:
        """複雑度削減提案作成"""
        template = self.suggestion_templates['complexity_reduction']
        
        suggestion_id = f"complexity_reduction_{hashlib.md5(f'{issue.id}_{refactoring_type}'.encode()).hexdigest()[:8]}"
        
        # リファクタリングタイプに応じた詳細設定
        if refactoring_type == 'major_refactoring':
            difficulty = ImplementationDifficulty.HARD
            estimated_time = 180  # 3時間
            description = "This function has very high complexity and should be broken down into multiple smaller functions"
            suggested_code = await self._generate_refactored_code(issue, context, 'extract_functions')
        elif refactoring_type == 'moderate_refactoring':
            difficulty = ImplementationDifficulty.MODERATE
            estimated_time = 60  # 1時間
            description = "This function has high complexity and would benefit from extracting some logic into helper functions"
            suggested_code = await self._generate_refactored_code(issue, context, 'extract_methods')
        else:
            difficulty = ImplementationDifficulty.EASY
            estimated_time = 30  # 30分
            description = "This function could be simplified by reducing nested conditions"
            suggested_code = await self._generate_refactored_code(issue, context, 'simplify_conditions')
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.CODE_REFACTORING,
            priority=ImprovementPriority.HIGH,
            difficulty=difficulty,
            title=template['title'],
            description=description,
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number,
            suggested_code=suggested_code,
            explanation=f"Reducing complexity will improve maintainability and readability. Current complexity: {context.get('complexity_metrics', {}).get('cyclomatic_complexity', 'unknown')}",
            benefits=template['benefits'],
            risks=template['risks'],
            related_issues=[issue.id],
            estimated_time_minutes=estimated_time,
            impact_score=0.8,
            confidence=0.7
        )
    
    async def _generate_refactored_code(self, issue: QualityIssue, context: Dict[str, Any], strategy: str) -> str:
        """リファクタリングされたコードの生成"""
        # 実際の実装では、より高度なコード生成AIを使用
        # ここでは簡易的な例を示す
        
        if strategy == 'extract_functions':
            return '''# Refactored version - extract complex logic into separate functions

def helper_function_1(data):
    """Handle specific aspect of the logic."""
    # Extracted logic here
    return processed_data

def helper_function_2(result):
    """Handle another aspect of the logic."""
    # More extracted logic here
    return final_result

def original_function(input_data):
    """Original function with reduced complexity."""
    # Step 1: Use helper function
    intermediate_result = helper_function_1(input_data)
    
    # Step 2: Use another helper function
    final_result = helper_function_2(intermediate_result)
    
    return final_result'''
        
        elif strategy == 'extract_methods':
            return '''# Refactored version - extract methods within class

class ExampleClass:
    def _extract_validation_logic(self, data):
        """Extracted validation logic."""
        # Validation code here
        return validated_data
    
    def _extract_processing_logic(self, data):
        """Extracted processing logic."""
        # Processing code here
        return processed_data
    
    def original_method(self, input_data):
        """Original method with reduced complexity."""
        validated_data = self._extract_validation_logic(input_data)
        result = self._extract_processing_logic(validated_data)
        return result'''
        
        else:  # simplify_conditions
            return '''# Refactored version - simplified conditions

def original_function(data):
    """Original function with simplified conditions."""
    # Use early returns to reduce nesting
    if not data:
        return None
    
    if not data.is_valid():
        return handle_invalid_data(data)
    
    # Main logic here with reduced nesting
    result = process_valid_data(data)
    return result

def handle_invalid_data(data):
    """Handle invalid data separately."""
    # Invalid data handling logic
    return default_result

def process_valid_data(data):
    """Process valid data."""
    # Main processing logic
    return processed_result'''
    
    async def _generate_performance_suggestions(self, issues: List[QualityIssue]) -> List[CodeSuggestion]:
        """パフォーマンス改善提案生成"""
        suggestions = []
        
        for issue in issues:
            if issue.rule_id == 'performance_range_len':
                suggestions.append(await self._create_enumerate_suggestion(issue))
            elif issue.rule_id == 'performance_keys_membership':
                suggestions.append(await self._create_dict_membership_suggestion(issue))
            elif issue.rule_id == 'performance_list_keys':
                suggestions.append(await self._create_keys_optimization_suggestion(issue))
        
        return [s for s in suggestions if s is not None]
    
    async def _create_enumerate_suggestion(self, issue: QualityIssue) -> Optional[CodeSuggestion]:
        """enumerate使用提案作成"""
        if not issue.file_path:
            return None
        
        suggestion_id = f"enumerate_opt_{hashlib.md5(issue.id.encode()).hexdigest()[:8]}"
        
        # 元のコードを取得
        try:
            with open(issue.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if issue.line_number and issue.line_number <= len(lines):
                    original_line = lines[issue.line_number - 1].strip()
                    
                    # enumerate を使った改善版を生成
                    suggested_code = self._convert_to_enumerate(original_line)
                    
                    return CodeSuggestion(
                        id=suggestion_id,
                        improvement_type=ImprovementType.PERFORMANCE_OPTIMIZATION,
                        priority=ImprovementPriority.LOW,
                        difficulty=ImplementationDifficulty.TRIVIAL,
                        title="Use enumerate() instead of range(len())",
                        description="Replace range(len()) pattern with more pythonic enumerate()",
                        file_path=issue.file_path,
                        line_start=issue.line_number,
                        line_end=issue.line_number,
                        original_code=original_line,
                        suggested_code=suggested_code,
                        explanation="enumerate() is more readable and slightly more efficient than range(len())",
                        benefits=[
                            "Improved code readability",
                            "More pythonic approach",
                            "Slightly better performance"
                        ],
                        related_issues=[issue.id],
                        auto_applicable=True,
                        estimated_time_minutes=2,
                        impact_score=0.3,
                        confidence=0.9
                    )
        except Exception as e:
            self.logger.error(f"Failed to create enumerate suggestion: {e}")
        
        return None
    
    def _convert_to_enumerate(self, original_line: str) -> str:
        """range(len())パターンをenumerateに変換"""
        # 簡易的な置換（実際はより高度なパターンマッチングが必要）
        pattern = r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):'
        match = re.search(pattern, original_line)
        
        if match:
            index_var = match.group(1)
            list_var = match.group(2)
            indent = ' ' * (len(original_line) - len(original_line.lstrip()))
            return f"{indent}for {index_var}, item in enumerate({list_var}):"
        
        return original_line  # 変換できない場合は元のまま
    
    async def _create_dict_membership_suggestion(self, issue: QualityIssue) -> Optional[CodeSuggestion]:
        """辞書メンバーシップ最適化提案"""
        suggestion_id = f"dict_membership_{hashlib.md5(issue.id.encode()).hexdigest()[:8]}"
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.PERFORMANCE_OPTIMIZATION,
            priority=ImprovementPriority.LOW,
            difficulty=ImplementationDifficulty.TRIVIAL,
            title="Optimize dictionary membership check",
            description="Use 'key in dict' instead of 'key in dict.keys()'",
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number,
            explanation="Direct membership check on dictionary is more efficient than checking keys()",
            benefits=[
                "Better performance",
                "More readable code",
                "Standard Python idiom"
            ],
            related_issues=[issue.id],
            auto_applicable=True,
            estimated_time_minutes=1,
            impact_score=0.2,
            confidence=0.95
        )
    
    async def _create_keys_optimization_suggestion(self, issue: QualityIssue) -> Optional[CodeSuggestion]:
        """keys()最適化提案"""
        suggestion_id = f"keys_opt_{hashlib.md5(issue.id.encode()).hexdigest()[:8]}"
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.PERFORMANCE_OPTIMIZATION,
            priority=ImprovementPriority.LOW,
            difficulty=ImplementationDifficulty.EASY,
            title="Avoid unnecessary list(dict.keys())",
            description="Direct iteration over dictionary keys is more efficient",
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number,
            explanation="Converting dict.keys() to list is usually unnecessary and wastes memory",
            benefits=[
                "Reduced memory usage",
                "Better performance",
                "Cleaner code"
            ],
            related_issues=[issue.id],
            auto_applicable=False,  # コンテキストに依存するため
            estimated_time_minutes=5,
            impact_score=0.3,
            confidence=0.8
        )
    
    async def _generate_security_suggestions(self, issues: List[QualityIssue]) -> List[CodeSuggestion]:
        """セキュリティ改善提案生成"""
        suggestions = []
        
        for issue in issues:
            if issue.rule_id == 'security_hardcoded_password':
                suggestions.append(await self._create_password_security_suggestion(issue))
            elif issue.rule_id == 'security_eval':
                suggestions.append(await self._create_eval_security_suggestion(issue))
            elif issue.rule_id == 'security_shell_injection':
                suggestions.append(await self._create_shell_injection_suggestion(issue))
        
        return [s for s in suggestions if s is not None]
    
    async def _create_password_security_suggestion(self, issue: QualityIssue) -> Optional[CodeSuggestion]:
        """パスワードセキュリティ提案"""
        suggestion_id = f"password_security_{hashlib.md5(issue.id.encode()).hexdigest()[:8]}"
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.SECURITY_HARDENING,
            priority=ImprovementPriority.CRITICAL,
            difficulty=ImplementationDifficulty.MODERATE,
            title="Remove hardcoded password",
            description="Replace hardcoded password with secure configuration",
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number,
            suggested_code='''# Secure approach using environment variables
import os
from getpass import getpass

# Option 1: Environment variable
password = os.getenv('APP_PASSWORD')

# Option 2: Secure input
if not password:
    password = getpass('Enter password: ')

# Option 3: Configuration file (encrypted)
# password = load_encrypted_config()['password']''',
            explanation="Hardcoded passwords are a major security risk. Use environment variables, secure input, or encrypted configuration files.",
            benefits=[
                "Eliminates security vulnerability",
                "Allows different passwords per environment",
                "Prevents accidental password exposure"
            ],
            risks=[
                "Requires environment setup",
                "May complicate deployment"
            ],
            related_issues=[issue.id],
            estimated_time_minutes=30,
            impact_score=1.0,
            confidence=0.95
        )
    
    async def _create_eval_security_suggestion(self, issue: QualityIssue) -> Optional[CodeSuggestion]:
        """eval使用セキュリティ提案"""
        suggestion_id = f"eval_security_{hashlib.md5(issue.id.encode()).hexdigest()[:8]}"
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.SECURITY_HARDENING,
            priority=ImprovementPriority.HIGH,
            difficulty=ImplementationDifficulty.MODERATE,
            title="Replace dangerous eval() usage",
            description="Use safer alternatives to eval() function",
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number,
            suggested_code='''# Safer alternatives to eval()

# For JSON parsing:
import json
data = json.loads(json_string)

# For mathematical expressions:
import ast
def safe_eval(expr):
    node = ast.parse(expr, mode='eval')
    return eval(compile(node, '<string>', 'eval'))

# For configuration:
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

# For simple attribute access:
value = getattr(obj, attr_name, default_value)''',
            explanation="eval() can execute arbitrary code and is a major security risk. Use specific parsers or libraries instead.",
            benefits=[
                "Eliminates code injection vulnerability",
                "Improves code clarity",
                "Better error handling"
            ],
            risks=[
                "May require significant refactoring",
                "Alternative approaches may be more verbose"
            ],
            related_issues=[issue.id],
            estimated_time_minutes=60,
            impact_score=0.9,
            confidence=0.9
        )
    
    async def _generate_documentation_suggestions(self, issues: List[QualityIssue]) -> List[CodeSuggestion]:
        """ドキュメンテーション改善提案生成"""
        suggestions = []
        
        for issue in issues:
            if 'missing_doc' in issue.id:
                suggestions.append(await self._create_docstring_suggestion(issue))
        
        return [s for s in suggestions if s is not None]
    
    async def _create_docstring_suggestion(self, issue: QualityIssue) -> Optional[CodeSuggestion]:
        """docstring追加提案"""
        if not issue.file_path:
            return None
        
        suggestion_id = f"docstring_{hashlib.md5(issue.id.encode()).hexdigest()[:8]}"
        
        # 関数の詳細を取得してdocstringテンプレートを生成
        context = await self.code_analyzer.analyze_code_context(
            Path(issue.file_path), 
            issue.line_number
        )
        
        suggested_docstring = await self._generate_docstring_template(context, issue.line_number)
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.DOCUMENTATION_ENHANCEMENT,
            priority=ImprovementPriority.MEDIUM,
            difficulty=ImplementationDifficulty.EASY,
            title="Add missing docstring",
            description="Add comprehensive docstring to improve code documentation",
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number,
            suggested_code=suggested_docstring,
            explanation="Good documentation improves code maintainability and helps other developers understand the code",
            benefits=[
                "Improved code understanding",
                "Better IDE support",
                "Easier maintenance"
            ],
            related_issues=[issue.id],
            estimated_time_minutes=10,
            impact_score=0.5,
            confidence=0.8
        )
    
    async def _generate_docstring_template(self, context: Dict[str, Any], line_number: Optional[int]) -> str:
        """docstringテンプレート生成"""
        # 関数情報を取得
        functions = context.get('code_structure', {}).get('functions', [])
        target_function = None
        
        if line_number:
            for func in functions:
                if func['line'] == line_number:
                    target_function = func
                    break
        
        if target_function:
            args = target_function.get('args', [])
            function_name = target_function.get('name', 'function')
            
            docstring = f'    """{function_name.replace("_", " ").title()}.\n    \n'
            
            if args:
                docstring += '    Args:\n'
                for arg in args:
                    if arg != 'self':
                        docstring += f'        {arg}: Description of {arg}\n'
                docstring += '    \n'
            
            docstring += '    Returns:\n'
            docstring += '        Description of return value\n'
            docstring += '    """'
            
            return docstring
        
        return '    """Add description here."""'
    
    async def _generate_maintainability_suggestions(self, issues: List[QualityIssue]) -> List[CodeSuggestion]:
        """保守性改善提案生成"""
        suggestions = []
        
        for issue in issues:
            if 'long_line' in issue.id:
                suggestion = await self._create_line_length_suggestion(issue)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    async def _create_line_length_suggestion(self, issue: QualityIssue) -> Optional[CodeSuggestion]:
        """行長改善提案"""
        suggestion_id = f"line_length_{hashlib.md5(issue.id.encode()).hexdigest()[:8]}"
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.STYLE_IMPROVEMENT,
            priority=ImprovementPriority.LOW,
            difficulty=ImplementationDifficulty.EASY,
            title="Break long line",
            description="Break long line to improve readability",
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number,
            explanation="Long lines are harder to read and may not fit on screen",
            benefits=[
                "Improved readability",
                "Better diff visualization",
                "Easier code review"
            ],
            related_issues=[issue.id],
            auto_applicable=True,
            estimated_time_minutes=3,
            impact_score=0.2,
            confidence=0.8
        )
    
    async def _generate_holistic_suggestions(self, quality_report: QualityReport) -> List[CodeSuggestion]:
        """全体的改善提案生成"""
        suggestions = []
        
        # 全体スコアベースの提案
        if quality_report.overall_score < 0.5:
            suggestions.append(await self._create_comprehensive_refactoring_suggestion(quality_report))
        
        # テストカバレッジの提案
        test_coverage_score = quality_report.metric_scores.get(QualityMetric.TEST_COVERAGE, 1.0)
        if test_coverage_score < 0.7:
            suggestions.append(await self._create_test_coverage_suggestion(quality_report))
        
        # アーキテクチャ改善提案
        if len(quality_report.issues) > 50:
            suggestions.append(await self._create_architecture_improvement_suggestion(quality_report))
        
        return [s for s in suggestions if s is not None]
    
    async def _create_comprehensive_refactoring_suggestion(self, quality_report: QualityReport) -> CodeSuggestion:
        """包括的リファクタリング提案"""
        suggestion_id = f"comprehensive_refactoring_{hashlib.md5(quality_report.id.encode()).hexdigest()[:8]}"
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.ARCHITECTURAL_IMPROVEMENT,
            priority=ImprovementPriority.HIGH,
            difficulty=ImplementationDifficulty.COMPLEX,
            title="Comprehensive Code Refactoring",
            description="The codebase requires comprehensive refactoring to improve overall quality",
            explanation=f"Overall quality score is {quality_report.overall_score:.2f}, indicating significant issues that require systematic refactoring",
            benefits=[
                "Dramatically improved code quality",
                "Better maintainability",
                "Reduced technical debt",
                "Improved team productivity"
            ],
            risks=[
                "Large time investment required",
                "Risk of introducing bugs",
                "May require extensive testing"
            ],
            estimated_time_minutes=2400,  # 40 hours
            impact_score=1.0,
            confidence=0.8,
            metadata={
                'requires_planning': True,
                'should_be_phased': True,
                'needs_team_discussion': True
            }
        )
    
    async def _create_test_coverage_suggestion(self, quality_report: QualityReport) -> CodeSuggestion:
        """テストカバレッジ改善提案"""
        suggestion_id = f"test_coverage_{hashlib.md5(quality_report.id.encode()).hexdigest()[:8]}"
        
        return CodeSuggestion(
            id=suggestion_id,
            improvement_type=ImprovementType.TEST_COVERAGE,
            priority=ImprovementPriority.HIGH,
            difficulty=ImplementationDifficulty.MODERATE,
            title="Improve Test Coverage",
            description="Add comprehensive test coverage to improve code reliability",
            explanation="Current test coverage is below recommended levels",
            benefits=[
                "Improved code reliability",
                "Easier refactoring",
                "Better bug detection",
                "Increased confidence in changes"
            ],
            estimated_time_minutes=480,  # 8 hours
            impact_score=0.8,
            confidence=0.9
        )
    
    async def _prioritize_and_deduplicate(self, suggestions: List[CodeSuggestion]) -> List[CodeSuggestion]:
        """提案の優先度付けと重複除去"""
        # 重複除去（同じファイル・行の類似提案）
        unique_suggestions = {}
        for suggestion in suggestions:
            key = f"{suggestion.file_path}_{suggestion.line_start}_{suggestion.improvement_type.value}"
            if key not in unique_suggestions or suggestion.impact_score > unique_suggestions[key].impact_score:
                unique_suggestions[key] = suggestion
        
        # 優先度でソート
        sorted_suggestions = sorted(
            unique_suggestions.values(),
            key=lambda s: (s.priority.value, -s.impact_score, s.difficulty.value)
        )
        
        return sorted_suggestions


class ImprovementSuggester:
    """
    自動改善提案システム
    
    主要機能:
    1. 品質問題から改善提案の自動生成
    2. 提案の優先度付けと実装計画作成
    3. 自動修正の実行
    4. 改善効果の予測と追跡
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config
        self.suggestion_generator = SuggestionGenerator(config.get('generator', {}))
        self.improvement_plans: Dict[str, ImprovementPlan] = {}
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 通信プロトコル
        self.communication_protocol: Optional[CommunicationProtocol] = None
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'improvement-suggester.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """改善提案システム初期化"""
        try:
            self.logger.info("Improvement Suggester initialization started")
            
            # 通信プロトコル初期化
            if self.config.get('enable_communication', True):
                self.communication_protocol = CommunicationProtocol(
                    "improvement_suggester",
                    self.config.get('communication', {})
                )
                await self.communication_protocol.initialize()
            
            self.logger.info("Improvement Suggester initialization completed")
            
        except Exception as e:
            self.logger.error(f"Improvement Suggester initialization failed: {e}")
            raise
    
    async def create_improvement_plan(self, quality_report: QualityReport) -> ImprovementPlan:
        """改善計画作成"""
        self.logger.info(f"Creating improvement plan for quality report: {quality_report.id}")
        
        # 改善提案生成
        suggestions = await self.suggestion_generator.generate_suggestions(quality_report)
        
        # 実装順序決定
        implementation_order = await self._determine_implementation_order(suggestions)
        
        # 総実装時間計算
        total_time = sum(s.estimated_time_minutes or 0 for s in suggestions)
        
        # 期待される品質改善効果予測
        expected_improvement = await self._predict_quality_improvement(suggestions, quality_report)
        
        # 改善計画作成
        plan_id = f"improvement_plan_{hashlib.md5(f'{quality_report.id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"
        
        plan = ImprovementPlan(
            id=plan_id,
            project_path=quality_report.project_path,
            quality_report_id=quality_report.id,
            suggestions=suggestions,
            implementation_order=implementation_order,
            estimated_total_time=total_time,
            expected_quality_improvement=expected_improvement
        )
        
        # 改善計画保存
        self.improvement_plans[plan_id] = plan
        
        self.logger.info(f"Created improvement plan: {plan_id} with {len(suggestions)} suggestions")
        
        return plan
    
    async def _determine_implementation_order(self, suggestions: List[CodeSuggestion]) -> List[str]:
        """実装順序決定"""
        # 依存関係と優先度を考慮した順序決定
        ordered_suggestions = []
        
        # 1. クリティカルなセキュリティ問題を最優先
        security_critical = [s for s in suggestions 
                           if s.improvement_type == ImprovementType.SECURITY_HARDENING 
                           and s.priority == ImprovementPriority.CRITICAL]
        ordered_suggestions.extend(security_critical)
        
        # 2. 自動修正可能な問題
        auto_fixable = [s for s in suggestions 
                       if s.auto_applicable and s not in ordered_suggestions]
        auto_fixable.sort(key=lambda s: s.priority.value)
        ordered_suggestions.extend(auto_fixable)
        
        # 3. 高影響・低難易度の問題
        high_impact_easy = [s for s in suggestions 
                           if s.impact_score > 0.7 
                           and s.difficulty in [ImplementationDifficulty.TRIVIAL, ImplementationDifficulty.EASY]
                           and s not in ordered_suggestions]
        high_impact_easy.sort(key=lambda s: (-s.impact_score, s.difficulty.value))
        ordered_suggestions.extend(high_impact_easy)
        
        # 4. 残りの提案を優先度順
        remaining = [s for s in suggestions if s not in ordered_suggestions]
        remaining.sort(key=lambda s: (s.priority.value, -s.impact_score, s.difficulty.value))
        ordered_suggestions.extend(remaining)
        
        return [s.id for s in ordered_suggestions]
    
    async def _predict_quality_improvement(
        self, 
        suggestions: List[CodeSuggestion], 
        quality_report: QualityReport
    ) -> Dict[QualityMetric, float]:
        """品質改善効果予測"""
        expected_improvement = {}
        
        # 提案タイプ別の改善効果を推定
        improvement_effects = {
            ImprovementType.CODE_REFACTORING: {QualityMetric.CODE_COMPLEXITY: 0.3, QualityMetric.MAINTAINABILITY: 0.2},
            ImprovementType.PERFORMANCE_OPTIMIZATION: {QualityMetric.PERFORMANCE: 0.4},
            ImprovementType.SECURITY_HARDENING: {QualityMetric.SECURITY: 0.6},
            ImprovementType.DOCUMENTATION_ENHANCEMENT: {QualityMetric.DOCUMENTATION: 0.5},
            ImprovementType.TEST_COVERAGE: {QualityMetric.TEST_COVERAGE: 0.4, QualityMetric.RELIABILITY: 0.2},
        }
        
        # 各メトリクスの改善効果を累積
        for suggestion in suggestions:
            effects = improvement_effects.get(suggestion.improvement_type, {})
            for metric, base_effect in effects.items():
                # 影響スコアと信頼度で調整
                adjusted_effect = base_effect * suggestion.impact_score * suggestion.confidence
                
                current_score = quality_report.metric_scores.get(metric, 0.0)
                if metric not in expected_improvement:
                    expected_improvement[metric] = current_score
                
                # 改善効果を適用（上限は1.0）
                expected_improvement[metric] = min(1.0, expected_improvement[metric] + adjusted_effect)
        
        return expected_improvement
    
    async def apply_auto_fixes(self, plan: ImprovementPlan) -> Dict[str, Any]:
        """自動修正適用"""
        results = {
            'applied_fixes': [],
            'failed_fixes': [],
            'total_fixes': 0,
            'success_rate': 0.0
        }
        
        auto_fixable_suggestions = [s for s in plan.suggestions if s.auto_applicable]
        results['total_fixes'] = len(auto_fixable_suggestions)
        
        for suggestion in auto_fixable_suggestions:
            try:
                success = await self._apply_single_fix(suggestion)
                if success:
                    results['applied_fixes'].append(suggestion.id)
                    self.logger.info(f"Successfully applied auto-fix: {suggestion.id}")
                else:
                    results['failed_fixes'].append(suggestion.id)
                    self.logger.warning(f"Failed to apply auto-fix: {suggestion.id}")
            
            except Exception as e:
                results['failed_fixes'].append(suggestion.id)
                self.logger.error(f"Error applying auto-fix {suggestion.id}: {e}")
        
        results['success_rate'] = len(results['applied_fixes']) / results['total_fixes'] if results['total_fixes'] > 0 else 0
        
        self.logger.info(f"Auto-fix results: {len(results['applied_fixes'])}/{results['total_fixes']} successful")
        
        return results
    
    async def _apply_single_fix(self, suggestion: CodeSuggestion) -> bool:
        """単一修正の適用"""
        if not suggestion.file_path or not suggestion.suggested_code:
            return False
        
        try:
            file_path = Path(suggestion.file_path)
            
            # ファイルの読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 修正適用
            if suggestion.line_start and suggestion.line_end:
                start_idx = suggestion.line_start - 1
                end_idx = suggestion.line_end - 1
                
                # 元のコードの置換
                if suggestion.original_code:
                    # 元のコードが一致するかチェック
                    original_line = lines[start_idx].rstrip()
                    if suggestion.original_code.strip() not in original_line:
                        self.logger.warning(f"Original code mismatch for {suggestion.id}")
                        return False
                
                # 新しいコードで置換
                indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
                indented_code = suggestion.suggested_code.replace('\n', f'\n{" " * indent}')
                lines[start_idx] = indented_code + '\n'
            
            # ファイルの書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply fix {suggestion.id}: {e}")
            return False
    
    async def get_suggestion_summary(self) -> Dict[str, Any]:
        """提案サマリー取得"""
        if not self.improvement_plans:
            return {"message": "No improvement plans available"}
        
        all_suggestions = []
        for plan in self.improvement_plans.values():
            all_suggestions.extend(plan.suggestions)
        
        # 統計計算
        by_type = {}
        by_priority = {}
        by_difficulty = {}
        
        for suggestion in all_suggestions:
            # タイプ別集計
            type_key = suggestion.improvement_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # 優先度別集計
            priority_key = suggestion.priority.name
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
            
            # 難易度別集計
            difficulty_key = suggestion.difficulty.value
            by_difficulty[difficulty_key] = by_difficulty.get(difficulty_key, 0) + 1
        
        auto_fixable_count = len([s for s in all_suggestions if s.auto_applicable])
        total_estimated_time = sum(s.estimated_time_minutes or 0 for s in all_suggestions)
        average_impact = sum(s.impact_score for s in all_suggestions) / len(all_suggestions) if all_suggestions else 0
        
        return {
            "total_plans": len(self.improvement_plans),
            "total_suggestions": len(all_suggestions),
            "auto_fixable_suggestions": auto_fixable_count,
            "total_estimated_time_hours": total_estimated_time / 60,
            "average_impact_score": average_impact,
            "by_improvement_type": by_type,
            "by_priority": by_priority,
            "by_difficulty": by_difficulty
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """改善提案システム状態取得"""
        return {
            "improvement_plans": len(self.improvement_plans),
            "communication_enabled": self.communication_protocol is not None,
            "generator_config": self.config.get('generator', {})
        }
    
    async def shutdown(self):
        """改善提案システムシャットダウン"""
        self.logger.info("Improvement Suggester shutdown initiated")
        
        if self.communication_protocol:
            await self.communication_protocol.shutdown()
        
        self.logger.info("Improvement Suggester shutdown completed")


if __name__ == "__main__":
    # テスト実行
    async def test_improvement_suggester():
        from .quality_guardian import QualityGuardian
        
        # 設定
        config = {
            'generator': {
                'code_analyzer': {}
            },
            'enable_communication': False
        }
        
        # 改善提案システム初期化
        suggester = ImprovementSuggester(config)
        await suggester.initialize()
        
        # テスト用品質レポート作成
        quality_guardian = QualityGuardian({'analyzer': {}})
        await quality_guardian.initialize()
        
        test_project = Path.cwd()
        quality_report = await quality_guardian.analyze_project_quality(test_project)
        
        # 改善計画作成
        improvement_plan = await suggester.create_improvement_plan(quality_report)
        
        print(f"Improvement Plan: {improvement_plan.id}")
        print(f"Suggestions: {len(improvement_plan.suggestions)}")
        print(f"Estimated Time: {improvement_plan.estimated_total_time} minutes")
        
        # 自動修正適用
        if improvement_plan.suggestions:
            auto_fix_results = await suggester.apply_auto_fixes(improvement_plan)
            print(f"Auto-fix Results: {auto_fix_results}")
        
        # サマリー取得
        summary = await suggester.get_suggestion_summary()
        print("Suggestion Summary:", json.dumps(summary, indent=2))
        
        await suggester.shutdown()
        await quality_guardian.shutdown()
    
    asyncio.run(test_improvement_suggester())