"""
Ultimate ShunsukeModel Ecosystem - Meta Project Manager
メタプロジェクト管理システム

複数のプロジェクト間の依存関係、統合、リソース配分を管理
シュンスケ式統合開発フレームワークの中核コンポーネント
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
import networkx as nx
from datetime import datetime, timezone
import hashlib

from .project_orchestrator import ProjectOrchestrator, ProjectSpec, TaskSpec


class DependencyType(Enum):
    """依存関係タイプ"""
    BLOCKS = "blocks"  # ブロッキング依存
    REQUIRES = "requires"  # 必須依存
    ENHANCES = "enhances"  # 拡張依存
    CONFLICTS = "conflicts"  # 競合関係
    COMPLEMENTS = "complements"  # 補完関係


class ResourceType(Enum):
    """リソースタイプ"""
    COMPUTATIONAL = "computational"
    AGENT = "agent"
    STORAGE = "storage"
    NETWORK = "network"
    TIME = "time"


class IntegrationPattern(Enum):
    """統合パターン"""
    SEQUENTIAL = "sequential"  # 順次実行
    PARALLEL = "parallel"  # 並行実行
    PIPELINE = "pipeline"  # パイプライン
    MESH = "mesh"  # メッシュ統合
    HIERARCHICAL = "hierarchical"  # 階層統合


@dataclass
class ProjectDependency:
    """プロジェクト依存関係"""
    source_project: str
    target_project: str
    dependency_type: DependencyType
    strength: float = 1.0  # 依存強度 (0.0-1.0)
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ResourceAllocation:
    """リソース配分"""
    resource_type: ResourceType
    total_available: float
    allocated: Dict[str, float] = field(default_factory=dict)  # project_id -> amount
    reserved: Dict[str, float] = field(default_factory=dict)  # project_id -> amount
    
    @property
    def available(self) -> float:
        """利用可能量"""
        used = sum(self.allocated.values()) + sum(self.reserved.values())
        return max(0, self.total_available - used)
    
    @property
    def utilization_rate(self) -> float:
        """利用率"""
        used = sum(self.allocated.values())
        return used / self.total_available if self.total_available > 0 else 0


@dataclass
class IntegrationSpec:
    """統合仕様"""
    name: str
    description: str
    projects: List[str]
    pattern: IntegrationPattern
    coordination_points: List[Dict[str, Any]] = field(default_factory=list)
    data_flow: Dict[str, List[str]] = field(default_factory=dict)  # project -> [output_projects]
    quality_gates: List[Dict[str, Any]] = field(default_factory=list)
    rollback_strategy: Optional[Dict[str, Any]] = None


@dataclass
class MetaProject:
    """メタプロジェクト"""
    id: str
    name: str
    description: str
    sub_projects: List[str] = field(default_factory=list)
    dependencies: List[ProjectDependency] = field(default_factory=list)
    integration_specs: List[IntegrationSpec] = field(default_factory=list)
    resource_requirements: Dict[ResourceType, float] = field(default_factory=dict)
    priority: int = 5  # 1-10
    status: str = "planning"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetaProjectManager:
    """
    メタプロジェクト管理システム
    
    主要機能:
    1. 複数プロジェクト間の依存関係管理
    2. リソース配分とスケジューリング
    3. 統合パターンの管理
    4. 品質ゲートの実行
    5. 競合解決とロードバランシング
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config
        self.meta_projects: Dict[str, MetaProject] = {}
        self.resource_allocations: Dict[ResourceType, ResourceAllocation] = {}
        self.dependency_graph = nx.DiGraph()
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 設定値
        self.max_concurrent_projects = config.get('max_concurrent_projects', 5)
        self.resource_buffer_ratio = config.get('resource_buffer_ratio', 0.1)
        self.auto_conflict_resolution = config.get('auto_conflict_resolution', True)
        
        # 初期化状態
        self.is_initialized = False
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'meta-project-manager.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """メタプロジェクト管理システム初期化"""
        try:
            self.logger.info("Meta Project Manager initialization started")
            
            # リソース配分初期化
            await self._initialize_resource_allocations()
            
            # 既存メタプロジェクト読み込み
            await self._load_existing_meta_projects()
            
            # 依存関係グラフ構築
            await self._rebuild_dependency_graph()
            
            self.is_initialized = True
            self.logger.info("Meta Project Manager initialization completed")
            
        except Exception as e:
            self.logger.error(f"Meta Project Manager initialization failed: {e}")
            raise
    
    async def _initialize_resource_allocations(self):
        """リソース配分初期化"""
        # デフォルトリソース設定
        default_resources = {
            ResourceType.COMPUTATIONAL: 100.0,  # CPU/GPU units
            ResourceType.AGENT: 10.0,  # 同時実行可能エージェント数
            ResourceType.STORAGE: 1000.0,  # GB
            ResourceType.NETWORK: 100.0,  # Mbps
            ResourceType.TIME: 1440.0  # minutes per day
        }
        
        # 設定からリソース量を取得
        resource_config = self.config.get('resources', {})
        
        for resource_type, default_amount in default_resources.items():
            amount = resource_config.get(resource_type.value, default_amount)
            self.resource_allocations[resource_type] = ResourceAllocation(
                resource_type=resource_type,
                total_available=amount
            )
        
        self.logger.info(f"Initialized {len(self.resource_allocations)} resource types")
    
    async def _load_existing_meta_projects(self):
        """既存メタプロジェクト読み込み"""
        # 設定ファイルまたはデータベースから読み込み (実装予定)
        pass
    
    async def _rebuild_dependency_graph(self):
        """依存関係グラフ再構築"""
        self.dependency_graph.clear()
        
        # 全メタプロジェクトをノードとして追加
        for meta_project in self.meta_projects.values():
            self.dependency_graph.add_node(meta_project.id, meta_project=meta_project)
            
            # 依存関係をエッジとして追加
            for dependency in meta_project.dependencies:
                self.dependency_graph.add_edge(
                    dependency.source_project,
                    dependency.target_project,
                    dependency=dependency
                )
        
        self.logger.debug(f"Dependency graph rebuilt: {len(self.dependency_graph.nodes)} nodes, {len(self.dependency_graph.edges)} edges")
    
    async def create_meta_project(
        self,
        name: str,
        description: str,
        sub_projects: List[str],
        integration_pattern: IntegrationPattern = IntegrationPattern.SEQUENTIAL
    ) -> str:
        """
        メタプロジェクト作成
        
        Args:
            name: メタプロジェクト名
            description: 説明
            sub_projects: サブプロジェクトIDリスト
            integration_pattern: 統合パターン
            
        Returns:
            作成されたメタプロジェクトID
        """
        # メタプロジェクトID生成
        meta_id = self._generate_meta_project_id(name)
        
        # メタプロジェクト作成
        meta_project = MetaProject(
            id=meta_id,
            name=name,
            description=description,
            sub_projects=sub_projects
        )
        
        # 統合仕様作成
        if len(sub_projects) > 1:
            integration_spec = IntegrationSpec(
                name=f"{name}_integration",
                description=f"Integration specification for {name}",
                projects=sub_projects,
                pattern=integration_pattern
            )
            meta_project.integration_specs.append(integration_spec)
        
        # 依存関係解析
        dependencies = await self._analyze_project_dependencies(sub_projects)
        meta_project.dependencies.extend(dependencies)
        
        # リソース要件計算
        resource_requirements = await self._calculate_resource_requirements(sub_projects)
        meta_project.resource_requirements = resource_requirements
        
        # メタプロジェクト登録
        self.meta_projects[meta_id] = meta_project
        
        # 依存関係グラフ更新
        await self._rebuild_dependency_graph()
        
        self.logger.info(f"Created meta project: {name} ({meta_id}) with {len(sub_projects)} sub-projects")
        
        return meta_id
    
    def _generate_meta_project_id(self, name: str) -> str:
        """メタプロジェクトID生成"""
        # 名前をハッシュ化してユニークIDを生成
        hash_input = f"{name}_{datetime.now().isoformat()}"
        hash_object = hashlib.md5(hash_input.encode())
        return f"meta_{hash_object.hexdigest()[:8]}"
    
    async def _analyze_project_dependencies(self, projects: List[str]) -> List[ProjectDependency]:
        """プロジェクト依存関係解析"""
        dependencies = []
        
        # プロジェクト間の依存関係を推定 (簡易実装)
        for i, project_a in enumerate(projects):
            for project_b in projects[i+1:]:
                # プロジェクト名やタイプから依存関係を推定
                dependency_type = self._infer_dependency_type(project_a, project_b)
                
                if dependency_type:
                    dependency = ProjectDependency(
                        source_project=project_a,
                        target_project=project_b,
                        dependency_type=dependency_type,
                        strength=0.5,  # デフォルト強度
                        description=f"Inferred dependency between {project_a} and {project_b}"
                    )
                    dependencies.append(dependency)
        
        return dependencies
    
    def _infer_dependency_type(self, project_a: str, project_b: str) -> Optional[DependencyType]:
        """依存関係タイプ推定"""
        # 簡易的な推定ロジック
        a_lower = project_a.lower()
        b_lower = project_b.lower()
        
        # MCP系プロジェクトの依存関係
        if 'mcp' in a_lower and 'integration' in b_lower:
            return DependencyType.REQUIRES
        
        # ドキュメント系の依存関係
        if 'doc' in a_lower and any(term in b_lower for term in ['api', 'code', 'implementation']):
            return DependencyType.REQUIRES
        
        # 品質分析の依存関係
        if 'quality' in a_lower and any(term in b_lower for term in ['test', 'implementation']):
            return DependencyType.REQUIRES
        
        # パフォーマンス最適化の依存関係
        if 'performance' in a_lower and 'implementation' in b_lower:
            return DependencyType.ENHANCES
        
        return None
    
    async def _calculate_resource_requirements(self, projects: List[str]) -> Dict[ResourceType, float]:
        """リソース要件計算"""
        requirements = {resource_type: 0.0 for resource_type in ResourceType}
        
        # プロジェクトタイプ別のリソース要件 (簡易実装)
        for project in projects:
            project_lower = project.lower()
            
            if 'mcp' in project_lower or 'server' in project_lower:
                requirements[ResourceType.COMPUTATIONAL] += 10.0
                requirements[ResourceType.AGENT] += 2.0
                requirements[ResourceType.STORAGE] += 50.0
                requirements[ResourceType.TIME] += 120.0
            
            elif 'documentation' in project_lower or 'doc' in project_lower:
                requirements[ResourceType.COMPUTATIONAL] += 5.0
                requirements[ResourceType.AGENT] += 1.0
                requirements[ResourceType.STORAGE] += 20.0
                requirements[ResourceType.TIME] += 60.0
            
            elif 'quality' in project_lower or 'test' in project_lower:
                requirements[ResourceType.COMPUTATIONAL] += 8.0
                requirements[ResourceType.AGENT] += 1.5
                requirements[ResourceType.STORAGE] += 30.0
                requirements[ResourceType.TIME] += 90.0
            
            elif 'performance' in project_lower or 'optimization' in project_lower:
                requirements[ResourceType.COMPUTATIONAL] += 15.0
                requirements[ResourceType.AGENT] += 2.5
                requirements[ResourceType.STORAGE] += 40.0
                requirements[ResourceType.TIME] += 150.0
        
        return requirements
    
    async def allocate_resources(self, meta_project_id: str) -> Dict[str, Any]:
        """
        メタプロジェクトへのリソース配分
        
        Args:
            meta_project_id: メタプロジェクトID
            
        Returns:
            配分結果
        """
        if meta_project_id not in self.meta_projects:
            raise ValueError(f"Meta project not found: {meta_project_id}")
        
        meta_project = self.meta_projects[meta_project_id]
        allocation_result = {"allocated": {}, "insufficient": {}, "warnings": []}
        
        # 各リソースタイプについて配分を試行
        for resource_type, required_amount in meta_project.resource_requirements.items():
            allocation = self.resource_allocations[resource_type]
            
            # 利用可能量チェック
            if allocation.available >= required_amount:
                # 配分実行
                allocation.allocated[meta_project_id] = required_amount
                allocation_result["allocated"][resource_type.value] = required_amount
                
                self.logger.info(f"Allocated {required_amount} {resource_type.value} to {meta_project_id}")
            else:
                # 不足リソース記録
                allocation_result["insufficient"][resource_type.value] = {
                    "required": required_amount,
                    "available": allocation.available
                }
                
                # 部分配分
                if allocation.available > 0:
                    allocation.allocated[meta_project_id] = allocation.available
                    allocation_result["allocated"][resource_type.value] = allocation.available
                    allocation_result["warnings"].append(
                        f"Partial allocation for {resource_type.value}: {allocation.available}/{required_amount}"
                    )
        
        return allocation_result
    
    async def get_execution_plan(self, meta_project_id: str) -> Dict[str, Any]:
        """
        実行プラン生成
        
        Args:
            meta_project_id: メタプロジェクトID
            
        Returns:
            実行プラン
        """
        if meta_project_id not in self.meta_projects:
            raise ValueError(f"Meta project not found: {meta_project_id}")
        
        meta_project = self.meta_projects[meta_project_id]
        
        # 依存関係に基づく実行順序決定
        execution_order = await self._calculate_execution_order(meta_project.sub_projects)
        
        # 並行実行可能性解析
        parallel_groups = await self._identify_parallel_groups(execution_order, meta_project.dependencies)
        
        # 品質ゲート設定
        quality_gates = await self._setup_quality_gates(meta_project)
        
        # 実行プラン作成
        execution_plan = {
            "meta_project_id": meta_project_id,
            "execution_strategy": meta_project.integration_specs[0].pattern.value if meta_project.integration_specs else "sequential",
            "phases": [],
            "quality_gates": quality_gates,
            "estimated_duration": self._estimate_total_duration(meta_project),
            "resource_allocation": meta_project.resource_requirements,
            "rollback_points": []
        }
        
        # フェーズ構築
        for i, group in enumerate(parallel_groups):
            phase = {
                "phase_id": f"phase_{i+1}",
                "projects": group,
                "execution_type": "parallel" if len(group) > 1 else "sequential",
                "dependencies": [
                    dep for dep in meta_project.dependencies
                    if dep.source_project in group or dep.target_project in group
                ],
                "quality_checks": [gate for gate in quality_gates if gate.get("phase") == i+1]
            }
            execution_plan["phases"].append(phase)
        
        return execution_plan
    
    async def _calculate_execution_order(self, projects: List[str]) -> List[str]:
        """実行順序計算"""
        # サブグラフ作成
        subgraph = self.dependency_graph.subgraph(projects)
        
        try:
            # トポロジカルソート
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXError:
            # 循環依存がある場合は警告してプロジェクト順序をそのまま返す
            self.logger.warning("Circular dependency detected, using original order")
            return projects
    
    async def _identify_parallel_groups(
        self,
        execution_order: List[str],
        dependencies: List[ProjectDependency]
    ) -> List[List[str]]:
        """並行実行グループ識別"""
        groups = []
        remaining = execution_order.copy()
        
        while remaining:
            # 依存関係のないプロジェクトを見つける
            ready_projects = []
            for project in remaining:
                # このプロジェクトをブロックする依存関係があるかチェック
                blocked = any(
                    dep.target_project == project and dep.source_project in remaining
                    for dep in dependencies
                    if dep.dependency_type in [DependencyType.BLOCKS, DependencyType.REQUIRES]
                )
                
                if not blocked:
                    ready_projects.append(project)
            
            if not ready_projects:
                # デッドロック状態 - 残りを全て1つのグループに
                groups.append(remaining)
                break
            
            # 準備完了プロジェクトを1つのグループに
            groups.append(ready_projects)
            
            # 処理済みプロジェクトを削除
            for project in ready_projects:
                remaining.remove(project)
        
        return groups
    
    async def _setup_quality_gates(self, meta_project: MetaProject) -> List[Dict[str, Any]]:
        """品質ゲート設定"""
        gates = []
        
        # 各統合仕様から品質ゲートを抽出
        for integration_spec in meta_project.integration_specs:
            gates.extend(integration_spec.quality_gates)
        
        # デフォルト品質ゲート
        if not gates:
            gates = [
                {
                    "name": "Initial Quality Check",
                    "phase": 1,
                    "criteria": {
                        "code_quality": 0.8,
                        "test_coverage": 0.7,
                        "documentation": 0.6
                    }
                },
                {
                    "name": "Integration Quality Check",
                    "phase": "integration",
                    "criteria": {
                        "integration_tests": 0.9,
                        "performance": 0.8,
                        "compatibility": 0.9
                    }
                },
                {
                    "name": "Final Quality Check",
                    "phase": "final",
                    "criteria": {
                        "overall_quality": 0.85,
                        "user_acceptance": 0.8,
                        "deployment_readiness": 0.9
                    }
                }
            ]
        
        return gates
    
    def _estimate_total_duration(self, meta_project: MetaProject) -> float:
        """総実行時間推定"""
        # 簡易推定: プロジェクト数と複雑度に基づく
        base_duration = len(meta_project.sub_projects) * 60  # 基本60分/プロジェクト
        complexity_factor = 1.0
        
        # 依存関係の複雑度
        if len(meta_project.dependencies) > len(meta_project.sub_projects):
            complexity_factor += 0.3
        
        # 統合パターンの複雑度
        for spec in meta_project.integration_specs:
            if spec.pattern in [IntegrationPattern.MESH, IntegrationPattern.HIERARCHICAL]:
                complexity_factor += 0.5
            elif spec.pattern == IntegrationPattern.PIPELINE:
                complexity_factor += 0.3
        
        return base_duration * complexity_factor
    
    async def resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """競合解決"""
        resolution_result = {"resolved": [], "unresolved": [], "actions": []}
        
        for conflict in conflicts:
            conflict_type = conflict.get("type", "unknown")
            
            if conflict_type == "resource_contention":
                # リソース競合解決
                action = await self._resolve_resource_conflict(conflict)
                if action:
                    resolution_result["resolved"].append(conflict)
                    resolution_result["actions"].append(action)
                else:
                    resolution_result["unresolved"].append(conflict)
            
            elif conflict_type == "dependency_conflict":
                # 依存関係競合解決
                action = await self._resolve_dependency_conflict(conflict)
                if action:
                    resolution_result["resolved"].append(conflict)
                    resolution_result["actions"].append(action)
                else:
                    resolution_result["unresolved"].append(conflict)
            
            else:
                resolution_result["unresolved"].append(conflict)
        
        return resolution_result
    
    async def _resolve_resource_conflict(self, conflict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """リソース競合解決"""
        # 優先度ベースの解決
        competing_projects = conflict.get("projects", [])
        resource_type = ResourceType(conflict.get("resource_type", "computational"))
        
        if not competing_projects:
            return None
        
        # プロジェクト優先度取得
        project_priorities = {}
        for project_id in competing_projects:
            if project_id in self.meta_projects:
                project_priorities[project_id] = self.meta_projects[project_id].priority
            else:
                project_priorities[project_id] = 5  # デフォルト優先度
        
        # 最高優先度プロジェクトにリソース配分
        highest_priority_project = max(project_priorities, key=project_priorities.get)
        
        return {
            "type": "resource_reallocation",
            "winner": highest_priority_project,
            "resource_type": resource_type.value,
            "description": f"Allocated {resource_type.value} to highest priority project {highest_priority_project}"
        }
    
    async def _resolve_dependency_conflict(self, conflict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """依存関係競合解決"""
        # 循環依存の検出と解決
        involved_projects = conflict.get("projects", [])
        
        if len(involved_projects) < 2:
            return None
        
        # 依存関係の一部を非同期化して解決
        return {
            "type": "dependency_decoupling",
            "projects": involved_projects,
            "solution": "async_communication",
            "description": f"Resolved circular dependency by introducing async communication between {involved_projects}"
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """メタプロジェクトマネージャー状態取得"""
        # リソース利用率計算
        resource_utilization = {}
        for resource_type, allocation in self.resource_allocations.items():
            resource_utilization[resource_type.value] = {
                "total": allocation.total_available,
                "allocated": sum(allocation.allocated.values()),
                "available": allocation.available,
                "utilization_rate": allocation.utilization_rate
            }
        
        return {
            "initialized": self.is_initialized,
            "meta_projects": len(self.meta_projects),
            "active_projects": len([p for p in self.meta_projects.values() if p.status in ["active", "running"]]),
            "dependency_graph": {
                "nodes": len(self.dependency_graph.nodes),
                "edges": len(self.dependency_graph.edges)
            },
            "resource_utilization": resource_utilization,
            "max_concurrent_projects": self.max_concurrent_projects
        }
    
    async def shutdown(self):
        """メタプロジェクトマネージャーシャットダウン"""
        self.logger.info("Meta Project Manager shutdown initiated")
        
        # アクティブなプロジェクトの状態保存
        active_projects = [p for p in self.meta_projects.values() if p.status in ["active", "running"]]
        if active_projects:
            self.logger.warning(f"Shutting down with {len(active_projects)} active projects")
        
        self.is_initialized = False
        self.logger.info("Meta Project Manager shutdown completed")


if __name__ == "__main__":
    # テスト実行
    async def test_meta_manager():
        config = {
            'max_concurrent_projects': 3,
            'resources': {
                'computational': 50.0,
                'agent': 5.0,
                'storage': 500.0,
                'time': 720.0
            }
        }
        
        manager = MetaProjectManager(config)
        await manager.initialize()
        
        # テストメタプロジェクト作成
        meta_id = await manager.create_meta_project(
            name="Test Integrated System",
            description="Test meta project for integrated system development",
            sub_projects=["mcp_server_project", "documentation_project", "quality_analysis_project"],
            integration_pattern=IntegrationPattern.PIPELINE
        )
        
        # リソース配分
        allocation_result = await manager.allocate_resources(meta_id)
        print("Resource allocation:", json.dumps(allocation_result, indent=2))
        
        # 実行プラン取得
        execution_plan = await manager.get_execution_plan(meta_id)
        print("Execution plan:", json.dumps(execution_plan, indent=2, default=str))
        
        # ステータス確認
        status = await manager.get_status()
        print("Manager status:", json.dumps(status, indent=2))
        
        await manager.shutdown()
    
    asyncio.run(test_meta_manager())