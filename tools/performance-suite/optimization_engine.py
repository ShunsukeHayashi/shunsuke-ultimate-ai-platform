#!/usr/bin/env python3
"""
シュンスケ式最適化エンジン - Ultimate ShunsukeModel Ecosystem

パフォーマンスボトルネックを自動検出し、
コード・設定・リソースの最適化を実行する高度な自動最適化システム
"""

import asyncio
import ast
import logging
import time
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import inspect
import textwrap
import autopep8
import black
import isort
from functools import lru_cache, wraps
import concurrent.futures
import threading
import gc
import sys
import os


class OptimizationType(Enum):
    """最適化タイプ"""
    CODE = "code"
    MEMORY = "memory"
    CPU = "cpu"
    IO = "io"
    NETWORK = "network"
    DATABASE = "database"
    CACHING = "caching"
    PARALLELIZATION = "parallelization"
    ALGORITHM = "algorithm"


class OptimizationLevel(Enum):
    """最適化レベル"""
    CONSERVATIVE = "conservative"  # 安全な最適化のみ
    MODERATE = "moderate"          # 標準的な最適化
    AGGRESSIVE = "aggressive"      # 積極的な最適化


@dataclass
class OptimizationRule:
    """最適化ルール"""
    rule_id: str
    name: str
    description: str
    optimization_type: OptimizationType
    pattern: str  # 検出パターン（正規表現またはASTパターン）
    replacement: Optional[str] = None
    transform_function: Optional[Callable] = None
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 5  # 1-10, 高いほど優先
    risk_level: int = 1  # 1-5, 高いほどリスク
    performance_impact: str = "medium"  # low, medium, high
    applicable_to: List[str] = field(default_factory=lambda: ["python"])


@dataclass
class OptimizationResult:
    """最適化結果"""
    optimization_id: str
    timestamp: datetime
    optimization_type: OptimizationType
    target: str  # ファイルパスまたは対象
    original_code: Optional[str] = None
    optimized_code: Optional[str] = None
    rules_applied: List[str] = field(default_factory=list)
    performance_improvement: Optional[float] = None  # パーセンテージ
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    rollback_available: bool = True


@dataclass
class PerformanceBottleneck:
    """パフォーマンスボトルネック"""
    bottleneck_id: str
    detected_at: datetime
    location: str  # ファイル:行番号 または関数名
    bottleneck_type: str
    severity: float  # 0-100
    impact: str  # low, medium, high, critical
    description: str
    metrics: Dict[str, Any]
    suggested_optimizations: List[OptimizationType]
    auto_fixable: bool = False


class OptimizationEngine:
    """
    シュンスケ式最適化エンジン
    
    機能:
    - パフォーマンスボトルネックの自動検出
    - コード最適化の自動実行
    - リソース使用の最適化
    - キャッシング戦略の実装
    - 並列化・非同期化の提案と実装
    - アルゴリズム改善
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 最適化設定
        self.optimization_level = OptimizationLevel(
            self.config.get('level', OptimizationLevel.MODERATE.value)
        )
        self.auto_apply = self.config.get('auto_apply', False)
        self.backup_enabled = self.config.get('backup', True)
        
        # 最適化ルール
        self.optimization_rules = self._initialize_optimization_rules()
        
        # 最適化履歴
        self.optimization_history: List[OptimizationResult] = []
        self.bottleneck_history: List[PerformanceBottleneck] = []
        
        # キャッシュ
        self._ast_cache = {}
        self._analysis_cache = {}
        
        # 統計
        self.stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'failed_optimizations': 0,
            'performance_improvements': [],
            'optimizations_by_type': defaultdict(int)
        }
        
        # スレッドプール
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    
    def _initialize_optimization_rules(self) -> List[OptimizationRule]:
        """最適化ルール初期化"""
        rules = []
        
        # リスト内包表記の最適化
        rules.append(OptimizationRule(
            rule_id="list_comprehension",
            name="Convert loops to list comprehensions",
            description="Convert simple for loops to list comprehensions",
            optimization_type=OptimizationType.CODE,
            pattern=r"result\s*=\s*\[\]\s*\nfor\s+(\w+)\s+in\s+(\w+):\s*\n\s+result\.append\(([^)]+)\)",
            replacement=r"result = [\3 for \1 in \2]",
            priority=7,
            risk_level=1,
            performance_impact="medium"
        ))
        
        # 文字列結合の最適化
        rules.append(OptimizationRule(
            rule_id="string_join",
            name="Optimize string concatenation",
            description="Use join() instead of + for multiple string concatenations",
            optimization_type=OptimizationType.CODE,
            pattern=None,  # ASTベースで検出
            transform_function=self._optimize_string_concatenation,
            priority=6,
            risk_level=1,
            performance_impact="high"
        ))
        
        # メモ化の追加
        rules.append(OptimizationRule(
            rule_id="memoization",
            name="Add memoization to recursive functions",
            description="Add @lru_cache decorator to recursive functions",
            optimization_type=OptimizationType.CACHING,
            pattern=None,  # ASTベースで検出
            transform_function=self._add_memoization,
            priority=8,
            risk_level=2,
            performance_impact="high"
        ))
        
        # 非同期化
        rules.append(OptimizationRule(
            rule_id="asyncio_conversion",
            name="Convert I/O operations to async",
            description="Convert blocking I/O operations to async/await",
            optimization_type=OptimizationType.IO,
            pattern=None,  # ASTベースで検出
            transform_function=self._convert_to_async,
            priority=9,
            risk_level=3,
            performance_impact="high",
            conditions=[{"min_io_operations": 3}]
        ))
        
        # ジェネレータへの変換
        rules.append(OptimizationRule(
            rule_id="generator_conversion",
            name="Convert large lists to generators",
            description="Convert functions returning large lists to generators",
            optimization_type=OptimizationType.MEMORY,
            pattern=None,  # ASTベースで検出
            transform_function=self._convert_to_generator,
            priority=7,
            risk_level=2,
            performance_impact="high"
        ))
        
        # データ構造の最適化
        rules.append(OptimizationRule(
            rule_id="data_structure_optimization",
            name="Optimize data structure usage",
            description="Use appropriate data structures (set vs list, etc.)",
            optimization_type=OptimizationType.ALGORITHM,
            pattern=None,  # ASTベースで検出
            transform_function=self._optimize_data_structures,
            priority=6,
            risk_level=2,
            performance_impact="medium"
        ))
        
        # SQL クエリ最適化
        rules.append(OptimizationRule(
            rule_id="sql_optimization",
            name="Optimize SQL queries",
            description="Add indexes, optimize joins, use query caching",
            optimization_type=OptimizationType.DATABASE,
            pattern=r"SELECT\s+\*\s+FROM",
            replacement=None,  # カスタム処理
            transform_function=self._optimize_sql_query,
            priority=8,
            risk_level=3,
            performance_impact="high"
        ))
        
        # 並列処理の追加
        rules.append(OptimizationRule(
            rule_id="parallelization",
            name="Add parallel processing",
            description="Use multiprocessing for CPU-bound operations",
            optimization_type=OptimizationType.PARALLELIZATION,
            pattern=None,  # ASTベースで検出
            transform_function=self._add_parallelization,
            priority=9,
            risk_level=4,
            performance_impact="high",
            conditions=[{"min_iterations": 1000}]
        ))
        
        return rules
    
    async def analyze_code(self, file_path: Path) -> List[PerformanceBottleneck]:
        """コード分析"""
        try:
            bottlenecks = []
            
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # AST解析
            tree = ast.parse(code)
            
            # 各種分析
            bottlenecks.extend(await self._analyze_loops(tree, file_path))
            bottlenecks.extend(await self._analyze_functions(tree, file_path))
            bottlenecks.extend(await self._analyze_io_operations(tree, file_path))
            bottlenecks.extend(await self._analyze_data_structures(tree, file_path))
            bottlenecks.extend(await self._analyze_memory_usage(tree, file_path))
            
            # 履歴に追加
            self.bottleneck_history.extend(bottlenecks)
            
            return bottlenecks
            
        except Exception as e:
            self.logger.error(f"Code analysis error: {e}")
            return []
    
    async def _analyze_loops(self, tree: ast.AST, file_path: Path) -> List[PerformanceBottleneck]:
        """ループ分析"""
        bottlenecks = []
        
        class LoopAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.loops = []
            
            def visit_For(self, node):
                # ネストレベル計算
                nest_level = 0
                parent = node
                while hasattr(parent, 'parent'):
                    parent = parent.parent
                    if isinstance(parent, (ast.For, ast.While)):
                        nest_level += 1
                
                self.loops.append({
                    'node': node,
                    'line': node.lineno,
                    'nest_level': nest_level,
                    'has_append': self._has_append_in_loop(node),
                    'iterations': self._estimate_iterations(node)
                })
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.loops.append({
                    'node': node,
                    'line': node.lineno,
                    'nest_level': 0,
                    'is_infinite': self._is_infinite_loop(node)
                })
                self.generic_visit(node)
            
            def _has_append_in_loop(self, node):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, 'attr') and child.func.attr == 'append':
                            return True
                return False
            
            def _estimate_iterations(self, node):
                # 簡易的な反復回数推定
                if isinstance(node.iter, ast.Call):
                    if hasattr(node.iter.func, 'id') and node.iter.func.id == 'range':
                        if node.iter.args:
                            if isinstance(node.iter.args[0], ast.Constant):
                                return node.iter.args[0].value
                return None
            
            def _is_infinite_loop(self, node):
                # While True パターン検出
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    return True
                return False
        
        # 親ノード情報を追加
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        
        analyzer = LoopAnalyzer()
        analyzer.visit(tree)
        
        # ボトルネック判定
        for loop_info in analyzer.loops:
            severity = 0
            suggestions = []
            
            # ネストレベルチェック
            if loop_info['nest_level'] >= 3:
                severity += 30
                suggestions.append(OptimizationType.ALGORITHM)
            
            # リスト追加パターン
            if loop_info.get('has_append'):
                severity += 20
                suggestions.append(OptimizationType.CODE)
            
            # 大量反復
            if loop_info.get('iterations') and loop_info['iterations'] > 10000:
                severity += 40
                suggestions.extend([OptimizationType.PARALLELIZATION, OptimizationType.ALGORITHM])
            
            if severity > 30:
                bottleneck = PerformanceBottleneck(
                    bottleneck_id=f"loop_{file_path.name}_{loop_info['line']}",
                    detected_at=datetime.now(),
                    location=f"{file_path}:{loop_info['line']}",
                    bottleneck_type="inefficient_loop",
                    severity=severity,
                    impact="high" if severity > 60 else "medium",
                    description=f"Potentially inefficient loop at line {loop_info['line']}",
                    metrics={
                        'nest_level': loop_info['nest_level'],
                        'has_append': loop_info.get('has_append', False),
                        'estimated_iterations': loop_info.get('iterations')
                    },
                    suggested_optimizations=suggestions,
                    auto_fixable=True
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _analyze_functions(self, tree: ast.AST, file_path: Path) -> List[PerformanceBottleneck]:
        """関数分析"""
        bottlenecks = []
        
        class FunctionAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.functions = []
            
            def visit_FunctionDef(self, node):
                metrics = {
                    'name': node.name,
                    'line': node.lineno,
                    'lines_of_code': self._count_lines(node),
                    'complexity': self._calculate_complexity(node),
                    'is_recursive': self._is_recursive(node),
                    'has_io': self._has_io_operations(node),
                    'return_size': self._estimate_return_size(node)
                }
                self.functions.append(metrics)
                self.generic_visit(node)
            
            def _count_lines(self, node):
                return node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
            
            def _calculate_complexity(self, node):
                # McCabe複雑度の簡易計算
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        complexity += 1
                return complexity
            
            def _is_recursive(self, node):
                function_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, 'id') and child.func.id == function_name:
                            return True
                return False
            
            def _has_io_operations(self, node):
                io_functions = {'open', 'read', 'write', 'requests', 'urlopen'}
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, 'id') and child.func.id in io_functions:
                            return True
                return False
            
            def _estimate_return_size(self, node):
                # 戻り値のサイズ推定（リストや辞書の場合）
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        if isinstance(child.value, (ast.List, ast.Dict)):
                            return "large"
                return "normal"
        
        analyzer = FunctionAnalyzer()
        analyzer.visit(tree)
        
        # ボトルネック判定
        for func_metrics in analyzer.functions:
            severity = 0
            suggestions = []
            
            # 複雑度チェック
            if func_metrics['complexity'] > 10:
                severity += 30
                suggestions.append(OptimizationType.ALGORITHM)
            
            # 再帰関数でメモ化なし
            if func_metrics['is_recursive']:
                severity += 40
                suggestions.append(OptimizationType.CACHING)
            
            # I/O操作
            if func_metrics['has_io']:
                severity += 20
                suggestions.append(OptimizationType.IO)
            
            # 大きな戻り値
            if func_metrics['return_size'] == "large":
                severity += 25
                suggestions.append(OptimizationType.MEMORY)
            
            if severity > 30:
                bottleneck = PerformanceBottleneck(
                    bottleneck_id=f"func_{file_path.name}_{func_metrics['name']}",
                    detected_at=datetime.now(),
                    location=f"{file_path}:{func_metrics['line']}",
                    bottleneck_type="inefficient_function",
                    severity=severity,
                    impact="high" if severity > 60 else "medium",
                    description=f"Performance issues in function '{func_metrics['name']}'",
                    metrics=func_metrics,
                    suggested_optimizations=suggestions,
                    auto_fixable=True
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _analyze_io_operations(self, tree: ast.AST, file_path: Path) -> List[PerformanceBottleneck]:
        """I/O操作分析"""
        bottlenecks = []
        
        class IOAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.io_operations = []
            
            def visit_Call(self, node):
                # ファイルI/O
                if hasattr(node.func, 'id'):
                    if node.func.id in ['open', 'read', 'write']:
                        self.io_operations.append({
                            'type': 'file_io',
                            'function': node.func.id,
                            'line': node.lineno,
                            'in_loop': self._is_in_loop(node)
                        })
                
                # ネットワークI/O
                if hasattr(node.func, 'attr'):
                    if node.func.attr in ['get', 'post', 'request']:
                        self.io_operations.append({
                            'type': 'network_io',
                            'function': node.func.attr,
                            'line': node.lineno,
                            'in_loop': self._is_in_loop(node)
                        })
                
                self.generic_visit(node)
            
            def _is_in_loop(self, node):
                parent = node
                while hasattr(parent, 'parent'):
                    parent = parent.parent
                    if isinstance(parent, (ast.For, ast.While)):
                        return True
                return False
        
        # 親ノード情報を追加
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        
        analyzer = IOAnalyzer()
        analyzer.visit(tree)
        
        # I/O操作の集計
        io_in_loops = sum(1 for op in analyzer.io_operations if op['in_loop'])
        total_io = len(analyzer.io_operations)
        
        if total_io > 5 or io_in_loops > 0:
            severity = min(100, total_io * 10 + io_in_loops * 30)
            
            bottleneck = PerformanceBottleneck(
                bottleneck_id=f"io_{file_path.name}",
                detected_at=datetime.now(),
                location=str(file_path),
                bottleneck_type="excessive_io",
                severity=severity,
                impact="critical" if io_in_loops > 0 else "high",
                description=f"Excessive I/O operations detected ({total_io} total, {io_in_loops} in loops)",
                metrics={
                    'total_io_operations': total_io,
                    'io_in_loops': io_in_loops,
                    'io_types': Counter(op['type'] for op in analyzer.io_operations)
                },
                suggested_optimizations=[OptimizationType.IO, OptimizationType.CACHING],
                auto_fixable=True
            )
            bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _analyze_data_structures(self, tree: ast.AST, file_path: Path) -> List[PerformanceBottleneck]:
        """データ構造分析"""
        bottlenecks = []
        
        class DataStructureAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.inefficiencies = []
            
            def visit_For(self, node):
                # リスト内での in 演算子使用
                if isinstance(node.iter, ast.Name):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Compare):
                            for op in child.ops:
                                if isinstance(op, ast.In):
                                    self.inefficiencies.append({
                                        'type': 'list_membership_test',
                                        'line': child.lineno,
                                        'description': 'Using "in" operator on list in loop'
                                    })
                
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # 非効率なメソッド呼び出し
                if hasattr(node.func, 'attr'):
                    # list.count() in loop
                    if node.func.attr == 'count' and self._is_in_loop(node):
                        self.inefficiencies.append({
                            'type': 'repeated_count',
                            'line': node.lineno,
                            'description': 'Repeated count() calls in loop'
                        })
                
                self.generic_visit(node)
            
            def _is_in_loop(self, node):
                parent = node
                while hasattr(parent, 'parent'):
                    parent = parent.parent
                    if isinstance(parent, (ast.For, ast.While)):
                        return True
                return False
        
        # 親ノード情報を追加
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        
        analyzer = DataStructureAnalyzer()
        analyzer.visit(tree)
        
        if analyzer.inefficiencies:
            severity = min(100, len(analyzer.inefficiencies) * 20)
            
            bottleneck = PerformanceBottleneck(
                bottleneck_id=f"datastructure_{file_path.name}",
                detected_at=datetime.now(),
                location=str(file_path),
                bottleneck_type="inefficient_data_structures",
                severity=severity,
                impact="medium",
                description="Inefficient data structure usage detected",
                metrics={
                    'inefficiencies': len(analyzer.inefficiencies),
                    'types': Counter(i['type'] for i in analyzer.inefficiencies)
                },
                suggested_optimizations=[OptimizationType.ALGORITHM, OptimizationType.CODE],
                auto_fixable=True
            )
            bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _analyze_memory_usage(self, tree: ast.AST, file_path: Path) -> List[PerformanceBottleneck]:
        """メモリ使用量分析"""
        bottlenecks = []
        
        class MemoryAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.large_allocations = []
            
            def visit_ListComp(self, node):
                # 大きなリスト内包表記
                if self._has_large_range(node):
                    self.large_allocations.append({
                        'type': 'large_list_comprehension',
                        'line': node.lineno
                    })
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # range() の大きな呼び出し
                if hasattr(node.func, 'id') and node.func.id == 'range':
                    if node.args and isinstance(node.args[0], ast.Constant):
                        if node.args[0].value > 1000000:
                            self.large_allocations.append({
                                'type': 'large_range',
                                'line': node.lineno,
                                'size': node.args[0].value
                            })
                
                self.generic_visit(node)
            
            def _has_large_range(self, node):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, 'id') and child.func.id == 'range':
                            if child.args and isinstance(child.args[0], ast.Constant):
                                if child.args[0].value > 100000:
                                    return True
                return False
        
        analyzer = MemoryAnalyzer()
        analyzer.visit(tree)
        
        if analyzer.large_allocations:
            severity = min(100, len(analyzer.large_allocations) * 25)
            
            bottleneck = PerformanceBottleneck(
                bottleneck_id=f"memory_{file_path.name}",
                detected_at=datetime.now(),
                location=str(file_path),
                bottleneck_type="high_memory_usage",
                severity=severity,
                impact="high",
                description="Potential high memory usage detected",
                metrics={
                    'large_allocations': len(analyzer.large_allocations),
                    'types': Counter(a['type'] for a in analyzer.large_allocations)
                },
                suggested_optimizations=[OptimizationType.MEMORY, OptimizationType.CODE],
                auto_fixable=True
            )
            bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def optimize_code(self, file_path: Path, bottlenecks: List[PerformanceBottleneck]) -> List[OptimizationResult]:
        """コード最適化実行"""
        results = []
        
        try:
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # バックアップ作成
            if self.backup_enabled:
                backup_path = file_path.with_suffix(f'.bak.{int(time.time())}')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_code)
            
            # 最適化実行
            optimized_code = original_code
            applied_rules = []
            
            for bottleneck in bottlenecks:
                if bottleneck.auto_fixable:
                    for opt_type in bottleneck.suggested_optimizations:
                        # 適用可能なルールを検索
                        applicable_rules = [
                            rule for rule in self.optimization_rules
                            if rule.optimization_type == opt_type
                            and self._is_rule_applicable(rule, bottleneck)
                        ]
                        
                        # 優先度順にソート
                        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
                        
                        # ルール適用
                        for rule in applicable_rules:
                            if self._should_apply_rule(rule):
                                try:
                                    new_code = await self._apply_optimization_rule(
                                        rule, optimized_code, bottleneck
                                    )
                                    if new_code != optimized_code:
                                        optimized_code = new_code
                                        applied_rules.append(rule.rule_id)
                                        self.logger.info(f"Applied optimization rule: {rule.name}")
                                except Exception as e:
                                    self.logger.error(f"Failed to apply rule {rule.rule_id}: {e}")
            
            # 結果の作成
            if optimized_code != original_code:
                # コードフォーマット
                optimized_code = self._format_code(optimized_code)
                
                # ファイル更新（auto_applyが有効な場合）
                if self.auto_apply:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(optimized_code)
                
                result = OptimizationResult(
                    optimization_id=f"opt_{file_path.name}_{int(time.time())}",
                    timestamp=datetime.now(),
                    optimization_type=OptimizationType.CODE,
                    target=str(file_path),
                    original_code=original_code,
                    optimized_code=optimized_code,
                    rules_applied=applied_rules,
                    success=True,
                    rollback_available=self.backup_enabled
                )
                
                results.append(result)
                self.optimization_history.append(result)
                self.stats['total_optimizations'] += 1
                self.stats['successful_optimizations'] += 1
                
                for rule_id in applied_rules:
                    self.stats['optimizations_by_type'][rule_id] += 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"Code optimization error: {e}")
            self.stats['failed_optimizations'] += 1
            return []
    
    def _is_rule_applicable(self, rule: OptimizationRule, bottleneck: PerformanceBottleneck) -> bool:
        """ルールが適用可能かチェック"""
        # 最適化タイプの一致確認
        if rule.optimization_type not in bottleneck.suggested_optimizations:
            return False
        
        # 条件チェック
        for condition in rule.conditions:
            for key, value in condition.items():
                if key in bottleneck.metrics:
                    if bottleneck.metrics[key] < value:
                        return False
        
        return True
    
    def _should_apply_rule(self, rule: OptimizationRule) -> bool:
        """ルールを適用すべきかチェック"""
        # 最適化レベルに基づく判定
        if self.optimization_level == OptimizationLevel.CONSERVATIVE:
            return rule.risk_level <= 2
        elif self.optimization_level == OptimizationLevel.MODERATE:
            return rule.risk_level <= 3
        else:  # AGGRESSIVE
            return True
    
    async def _apply_optimization_rule(self, 
                                     rule: OptimizationRule,
                                     code: str,
                                     bottleneck: PerformanceBottleneck) -> str:
        """最適化ルール適用"""
        if rule.pattern and rule.replacement:
            # 正規表現ベースの置換
            return re.sub(rule.pattern, rule.replacement, code)
        elif rule.transform_function:
            # カスタム変換関数
            return await rule.transform_function(code, bottleneck)
        else:
            return code
    
    def _optimize_string_concatenation(self, code: str, bottleneck: PerformanceBottleneck) -> str:
        """文字列結合の最適化"""
        # AST変換による最適化
        tree = ast.parse(code)
        
        class StringOptimizer(ast.NodeTransformer):
            def visit_BinOp(self, node):
                # 文字列の + 演算を検出
                if isinstance(node.op, ast.Add):
                    if self._is_string_concat(node):
                        # join() への変換
                        return self._convert_to_join(node)
                return self.generic_visit(node)
            
            def _is_string_concat(self, node):
                # 簡易的な文字列結合判定
                return True  # 実際は型推論が必要
            
            def _convert_to_join(self, node):
                # "".join([...]) への変換
                # 実装は複雑なため省略
                return node
        
        optimizer = StringOptimizer()
        optimized_tree = optimizer.visit(tree)
        
        return ast.unparse(optimized_tree)
    
    async def _add_memoization(self, code: str, bottleneck: PerformanceBottleneck) -> str:
        """メモ化の追加"""
        tree = ast.parse(code)
        
        class MemoizationAdder(ast.NodeTransformer):
            def __init__(self):
                self.imports_added = False
            
            def visit_Module(self, node):
                # functools import追加
                if not self.imports_added:
                    import_node = ast.ImportFrom(
                        module='functools',
                        names=[ast.alias(name='lru_cache', asname=None)],
                        level=0
                    )
                    node.body.insert(0, import_node)
                    self.imports_added = True
                
                return self.generic_visit(node)
            
            def visit_FunctionDef(self, node):
                # 再帰関数にデコレータ追加
                if self._is_recursive_function(node):
                    decorator = ast.Name(id='lru_cache', ctx=ast.Load())
                    decorator_call = ast.Call(
                        func=decorator,
                        args=[],
                        keywords=[]
                    )
                    node.decorator_list.insert(0, decorator_call)
                
                return self.generic_visit(node)
            
            def _is_recursive_function(self, node):
                function_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, 'id') and child.func.id == function_name:
                            return True
                return False
        
        adder = MemoizationAdder()
        optimized_tree = adder.visit(tree)
        
        return ast.unparse(optimized_tree)
    
    async def _convert_to_async(self, code: str, bottleneck: PerformanceBottleneck) -> str:
        """非同期化変換"""
        # 複雑な実装のため簡略化
        # 実際にはI/O操作を識別してasync/awaitに変換
        return code
    
    async def _convert_to_generator(self, code: str, bottleneck: PerformanceBottleneck) -> str:
        """ジェネレータへの変換"""
        tree = ast.parse(code)
        
        class GeneratorConverter(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                # 大きなリストを返す関数をジェネレータに変換
                if self._returns_large_list(node):
                    return self._convert_to_generator_function(node)
                return self.generic_visit(node)
            
            def _returns_large_list(self, node):
                # 戻り値がリストかチェック
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        if isinstance(child.value, ast.List):
                            return True
                        if isinstance(child.value, ast.ListComp):
                            return True
                return False
            
            def _convert_to_generator_function(self, node):
                # yield を使った実装に変換
                # 実装は複雑なため省略
                return node
        
        converter = GeneratorConverter()
        optimized_tree = converter.visit(tree)
        
        return ast.unparse(optimized_tree)
    
    def _optimize_data_structures(self, code: str, bottleneck: PerformanceBottleneck) -> str:
        """データ構造の最適化"""
        # リストからセットへの変換など
        # 実装は複雑なため省略
        return code
    
    def _optimize_sql_query(self, code: str, bottleneck: PerformanceBottleneck) -> str:
        """SQLクエリ最適化"""
        # SELECT * の具体的なカラム指定への変換
        # インデックスヒントの追加など
        return code
    
    async def _add_parallelization(self, code: str, bottleneck: PerformanceBottleneck) -> str:
        """並列処理の追加"""
        # multiprocessing.Pool を使った並列化
        # 実装は複雑なため省略
        return code
    
    def _format_code(self, code: str) -> str:
        """コードフォーマット"""
        try:
            # Black でフォーマット
            code = black.format_str(code, mode=black.Mode())
            
            # isort でインポート整理
            code = isort.code(code)
            
            # autopep8 で追加整形
            code = autopep8.fix_code(code)
            
            return code
        except Exception as e:
            self.logger.error(f"Code formatting error: {e}")
            return code
    
    async def analyze_performance_impact(self, 
                                       original_code: str,
                                       optimized_code: str) -> Dict[str, Any]:
        """パフォーマンス影響分析"""
        try:
            # 簡易的なパフォーマンステスト
            impact = {
                'code_size_reduction': (len(original_code) - len(optimized_code)) / len(original_code) * 100,
                'complexity_reduction': 0,  # TODO: 実装
                'estimated_speedup': 0,     # TODO: 実装
            }
            
            return impact
            
        except Exception as e:
            self.logger.error(f"Performance impact analysis error: {e}")
            return {}
    
    async def rollback_optimization(self, optimization_id: str) -> bool:
        """最適化のロールバック"""
        try:
            # 最適化結果を検索
            optimization = None
            for opt in self.optimization_history:
                if opt.optimization_id == optimization_id:
                    optimization = opt
                    break
            
            if not optimization or not optimization.rollback_available:
                return False
            
            # 元のコードに戻す
            if optimization.original_code and optimization.target:
                with open(optimization.target, 'w', encoding='utf-8') as f:
                    f.write(optimization.original_code)
                
                self.logger.info(f"Rolled back optimization: {optimization_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Rollback error: {e}")
            return False
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """最適化レポート生成"""
        try:
            # 最近の最適化
            recent_optimizations = self.optimization_history[-10:] if self.optimization_history else []
            
            # パフォーマンス改善の平均
            avg_improvement = 0
            if self.stats['performance_improvements']:
                avg_improvement = np.mean(self.stats['performance_improvements'])
            
            return {
                'summary': {
                    'total_optimizations': self.stats['total_optimizations'],
                    'successful': self.stats['successful_optimizations'],
                    'failed': self.stats['failed_optimizations'],
                    'success_rate': self.stats['successful_optimizations'] / max(self.stats['total_optimizations'], 1) * 100,
                    'average_improvement': f"{avg_improvement:.1f}%"
                },
                'optimizations_by_type': dict(self.stats['optimizations_by_type']),
                'recent_optimizations': [
                    {
                        'id': opt.optimization_id,
                        'timestamp': opt.timestamp.isoformat(),
                        'type': opt.optimization_type.value,
                        'target': opt.target,
                        'rules_applied': opt.rules_applied,
                        'success': opt.success
                    }
                    for opt in recent_optimizations
                ],
                'detected_bottlenecks': len(self.bottleneck_history),
                'auto_fixable_bottlenecks': sum(1 for b in self.bottleneck_history if b.auto_fixable),
                'optimization_level': self.optimization_level.value,
                'auto_apply_enabled': self.auto_apply
            }
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            return {'error': str(e)}
    
    def __del__(self):
        """クリーンアップ"""
        self.executor.shutdown(wait=False)


# 最適化エンジンのファクトリー関数
def create_optimization_engine(config: Optional[Dict[str, Any]] = None) -> OptimizationEngine:
    """最適化エンジン作成"""
    return OptimizationEngine(config)


if __name__ == "__main__":
    # テスト実行
    async def test_optimization_engine():
        # テストコード作成
        test_code = '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data_list):
    result = []
    for item in data_list:
        if item > 0:
            result.append(item * 2)
    return result

def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates

def read_large_file(filename):
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            lines.append(line.strip())
    return lines
'''
        
        # テストファイル作成
        test_file = Path("test_optimization.py")
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # 最適化エンジン作成
        engine = create_optimization_engine({
            'level': 'moderate',
            'auto_apply': False,
            'backup': True
        })
        
        print("Analyzing code for bottlenecks...")
        bottlenecks = await engine.analyze_code(test_file)
        
        print(f"\nFound {len(bottlenecks)} bottlenecks:")
        for bottleneck in bottlenecks:
            print(f"- {bottleneck.description}")
            print(f"  Location: {bottleneck.location}")
            print(f"  Severity: {bottleneck.severity}")
            print(f"  Suggested optimizations: {[o.value for o in bottleneck.suggested_optimizations]}")
        
        print("\nApplying optimizations...")
        results = await engine.optimize_code(test_file, bottlenecks)
        
        if results:
            result = results[0]
            print(f"\nOptimization successful!")
            print(f"Rules applied: {result.rules_applied}")
            print("\nOptimized code preview:")
            print(result.optimized_code[:500] + "..." if len(result.optimized_code) > 500 else result.optimized_code)
        
        # レポート生成
        report = await engine.get_optimization_report()
        print("\nOptimization Report:")
        print(json.dumps(report, indent=2))
        
        # クリーンアップ
        test_file.unlink()
    
    asyncio.run(test_optimization_engine())