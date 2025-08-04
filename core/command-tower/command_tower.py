"""
Ultimate ShunsukeModel Ecosystem - Command Tower System
シュンスケ式 精密司令塔プロンプト

統合プラットフォームの中央司令塔として、全てのエージェントとツールを統制管理
CLAUDE.mdの「Repository-Based Project Management Workflow」に基づく実装
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
from datetime import datetime, timezone

from ..meta_framework.project_orchestrator import ProjectOrchestrator
from ..meta_framework.meta_project_manager import MetaProjectManager
from ...orchestration.coordinator.agent_coordinator import AgentCoordinator
from ...integration.claude_integration.claude_bridge import ClaudeBridge


class TaskStatus(Enum):
    """タスクステータス - ログドリブン + 消し込みスタイル"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"  # 消し込み済み
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class Priority(Enum):
    """優先度レベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CommandTask:
    """司令塔管理タスク"""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    assigned_agents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None  # 消し込み日時
    metadata: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_log(self, action: str, details: Dict[str, Any] = None):
        """ログエントリを追加"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details or {},
            "status": self.status.value
        }
        self.logs.append(log_entry)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_completed(self):
        """タスクを完了マーク"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.add_log("task_completed", {"completion_time": self.completed_at.isoformat()})
    
    def archive_task(self, reason: str = "workflow_completion"):
        """タスクを消し込み（アーカイブ）"""
        self.status = TaskStatus.ARCHIVED
        self.archived_at = datetime.now(timezone.utc)
        self.add_log("task_archived", {
            "archive_time": self.archived_at.isoformat(),
            "reason": reason
        })


@dataclass
class CommandContext:
    """司令塔実行コンテキスト"""
    session_id: str
    user_intent: str
    current_phase: str
    active_agents: List[str] = field(default_factory=list)
    resource_allocation: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    quality_thresholds: Dict[str, float] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)


class CommandTower:
    """
    シュンスケ式精密司令塔 - Ultimate ShunsukeModel Ecosystem の中央制御システム
    
    主要機能:
    1. タスク管理とワークフロー制御
    2. エージェント協調とリソース配分
    3. 品質監視とパフォーマンス最適化
    4. ログドリブン開発支援
    5. 消し込みスタイルによるタスク完了管理
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """司令塔初期化"""
        self.config_path = config_path or Path.home() / '.claude' / 'shunsuke-ecosystem' / 'command-tower.yaml'
        self.config = self._load_config()
        
        # コンポーネント初期化
        self.project_orchestrator = ProjectOrchestrator(self.config.get('orchestrator', {}))
        self.meta_manager = MetaProjectManager(self.config.get('meta_manager', {}))
        self.agent_coordinator = AgentCoordinator(self.config.get('coordinator', {}))
        self.claude_bridge = ClaudeBridge(self.config.get('claude_integration', {}))
        
        # タスク管理
        self.tasks: Dict[str, CommandTask] = {}
        self.active_contexts: Dict[str, CommandContext] = {}
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 司令塔状態
        self.is_active = False
        self.startup_time = None
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # デフォルト設定
        default_config = {
            "command_tower": {
                "max_concurrent_tasks": 10,
                "task_timeout_minutes": 30,
                "quality_threshold": 0.8,
                "auto_archive_completed": True,
                "log_level": "INFO"
            },
            "orchestrator": {
                "max_agents_per_task": 5,
                "resource_allocation_strategy": "balanced"
            },
            "meta_manager": {
                "project_tracking_enabled": True,
                "auto_dependency_resolution": True
            },
            "coordinator": {
                "communication_protocol": "async",
                "heartbeat_interval": 30
            },
            "claude_integration": {
                "auto_slash_commands": True,
                "hook_integration": True,
                "subagent_management": True
            }
        }
        
        # 設定ファイル作成
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        return default_config
    
    def _setup_logging(self):
        """ログ設定"""
        log_level = self.config.get('command_tower', {}).get('log_level', 'INFO')
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'command-tower.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, log_level.upper()))
    
    async def initialize(self) -> bool:
        """司令塔システム初期化"""
        try:
            self.logger.info("Command Tower initialization started")
            
            # コンポーネント初期化
            await self.project_orchestrator.initialize()
            await self.meta_manager.initialize()
            await self.agent_coordinator.initialize()
            await self.claude_bridge.initialize()
            
            self.is_active = True
            self.startup_time = datetime.now(timezone.utc)
            
            self.logger.info("Command Tower initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Command Tower initialization failed: {e}")
            return False
    
    async def execute_command_sequence(
        self,
        user_intent: str,
        context: Optional[CommandContext] = None
    ) -> Dict[str, Any]:
        """
        シュンスケ式コマンドシーケンス実行
        
        Args:
            user_intent: ユーザーの意図・要求
            context: 実行コンテキスト
            
        Returns:
            実行結果とメトリクス
        """
        if not self.is_active:
            raise RuntimeError("Command Tower is not initialized")
        
        # コンテキスト準備
        session_id = f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if context is None:
            context = CommandContext(
                session_id=session_id,
                user_intent=user_intent,
                current_phase="analysis"
            )
        
        self.active_contexts[session_id] = context
        
        try:
            self.logger.info(f"Command sequence started: {user_intent}")
            
            # フェーズ1: 意図解析とタスク分解
            analysis_result = await self._analyze_user_intent(user_intent, context)
            context.current_phase = "task_planning"
            
            # フェーズ2: タスクプランニング
            task_plan = await self._create_task_plan(analysis_result, context)
            context.current_phase = "agent_allocation"
            
            # フェーズ3: エージェント配置
            agent_allocation = await self._allocate_agents(task_plan, context)
            context.current_phase = "execution"
            
            # フェーズ4: 実行とモニタリング
            execution_result = await self._execute_task_plan(task_plan, agent_allocation, context)
            context.current_phase = "quality_analysis"
            
            # フェーズ5: 品質分析
            quality_result = await self._analyze_quality(execution_result, context)
            context.current_phase = "completion"
            
            # フェーズ6: 完了処理
            completion_result = await self._complete_command_sequence(
                execution_result, quality_result, context
            )
            
            # 成功ログ
            self.logger.info(f"Command sequence completed successfully: {session_id}")
            
            return {
                "session_id": session_id,
                "status": "completed",
                "results": completion_result,
                "quality_metrics": quality_result,
                "execution_time": (datetime.now(timezone.utc) - context.execution_history[0]["timestamp"]).total_seconds(),
                "context": context
            }
            
        except Exception as e:
            self.logger.error(f"Command sequence failed: {e}", exc_info=True)
            context.current_phase = "error"
            
            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e),
                "context": context
            }
        
        finally:
            # コンテキストクリーンアップ
            if session_id in self.active_contexts:
                del self.active_contexts[session_id]
    
    async def _analyze_user_intent(self, user_intent: str, context: CommandContext) -> Dict[str, Any]:
        """ユーザー意図の解析"""
        self.logger.debug(f"Analyzing user intent: {user_intent}")
        
        # Claude Bridge を使用した意図解析
        analysis = await self.claude_bridge.analyze_intent(user_intent)
        
        context.execution_history.append({
            "phase": "intent_analysis",
            "timestamp": datetime.now(timezone.utc),
            "input": user_intent,
            "output": analysis
        })
        
        return analysis
    
    async def _create_task_plan(self, analysis: Dict[str, Any], context: CommandContext) -> List[CommandTask]:
        """タスクプラン作成"""
        self.logger.debug("Creating task plan")
        
        # プロジェクトオーケストレーターによるタスク分解
        task_breakdown = await self.project_orchestrator.create_task_breakdown(analysis)
        
        tasks = []
        for i, task_info in enumerate(task_breakdown):
            task = CommandTask(
                id=f"{context.session_id}_task_{i:03d}",
                name=task_info.get("name", f"Task {i+1}"),
                description=task_info.get("description", ""),
                priority=Priority(task_info.get("priority", "medium")),
                metadata=task_info.get("metadata", {})
            )
            
            task.add_log("task_created", {"source": "command_tower"})
            tasks.append(task)
            self.tasks[task.id] = task
        
        context.execution_history.append({
            "phase": "task_planning",
            "timestamp": datetime.now(timezone.utc),
            "task_count": len(tasks),
            "tasks": [{"id": t.id, "name": t.name} for t in tasks]
        })
        
        return tasks
    
    async def _allocate_agents(self, tasks: List[CommandTask], context: CommandContext) -> Dict[str, List[str]]:
        """エージェント配置"""
        self.logger.debug(f"Allocating agents for {len(tasks)} tasks")
        
        # AgentCoordinator によるエージェント配置
        allocation = await self.agent_coordinator.allocate_agents_to_tasks(
            [{"id": t.id, "requirements": t.metadata.get("agent_requirements", {})} for t in tasks]
        )
        
        # タスクにエージェント情報を更新
        for task in tasks:
            if task.id in allocation:
                task.assigned_agents = allocation[task.id]
                task.add_log("agents_allocated", {"agents": task.assigned_agents})
        
        context.active_agents = list(set([agent for agents in allocation.values() for agent in agents]))
        context.resource_allocation = allocation
        
        context.execution_history.append({
            "phase": "agent_allocation",
            "timestamp": datetime.now(timezone.utc),
            "allocation": allocation,
            "total_agents": len(context.active_agents)
        })
        
        return allocation
    
    async def _execute_task_plan(
        self,
        tasks: List[CommandTask],
        allocation: Dict[str, List[str]],
        context: CommandContext
    ) -> Dict[str, Any]:
        """タスクプラン実行"""
        self.logger.info(f"Executing task plan with {len(tasks)} tasks")
        
        execution_results = {}
        failed_tasks = []
        
        # 依存関係に基づくタスク実行順序決定
        execution_order = self._resolve_task_dependencies(tasks)
        
        for task in execution_order:
            try:
                task.status = TaskStatus.IN_PROGRESS
                task.add_log("execution_started")
                
                # エージェント協調による実行
                result = await self.agent_coordinator.execute_task_with_agents(
                    task_id=task.id,
                    agents=task.assigned_agents,
                    task_spec={
                        "name": task.name,
                        "description": task.description,
                        "metadata": task.metadata
                    }
                )
                
                if result.get("success", False):
                    task.mark_completed()
                    execution_results[task.id] = result
                    self.logger.info(f"Task completed successfully: {task.name}")
                else:
                    task.status = TaskStatus.BLOCKED
                    task.add_log("execution_failed", {"error": result.get("error")})
                    failed_tasks.append(task)
                    self.logger.warning(f"Task failed: {task.name} - {result.get('error')}")
                
            except Exception as e:
                task.status = TaskStatus.BLOCKED
                task.add_log("execution_error", {"exception": str(e)})
                failed_tasks.append(task)
                self.logger.error(f"Task execution error: {task.name} - {e}")
        
        context.execution_history.append({
            "phase": "task_execution",
            "timestamp": datetime.now(timezone.utc),
            "completed_tasks": len(execution_results),
            "failed_tasks": len(failed_tasks),
            "results": execution_results
        })
        
        return {
            "successful_tasks": execution_results,
            "failed_tasks": [{"id": t.id, "name": t.name, "error": t.logs[-1].get("details", {})} for t in failed_tasks],
            "completion_rate": len(execution_results) / len(tasks) if tasks else 0
        }
    
    def _resolve_task_dependencies(self, tasks: List[CommandTask]) -> List[CommandTask]:
        """タスク依存関係解決"""
        # 単純な依存関係解決 (実際はより複雑なアルゴリズムが必要)
        task_map = {task.id: task for task in tasks}
        resolved = []
        remaining = tasks.copy()
        
        while remaining:
            # 依存関係のないタスクを探す
            ready_tasks = [
                task for task in remaining
                if all(dep_id in [t.id for t in resolved] for dep_id in task.dependencies)
            ]
            
            if not ready_tasks:
                # 循環依存または未解決依存関係
                self.logger.warning("Circular dependency detected or unresolved dependencies")
                resolved.extend(remaining)
                break
            
            # 優先度順でソート
            ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
            selected = ready_tasks[0]
            
            resolved.append(selected)
            remaining.remove(selected)
        
        return resolved
    
    async def _analyze_quality(self, execution_result: Dict[str, Any], context: CommandContext) -> Dict[str, Any]:
        """品質分析"""
        self.logger.debug("Analyzing execution quality")
        
        # 品質メトリクス計算
        completion_rate = execution_result.get("completion_rate", 0)
        error_rate = len(execution_result.get("failed_tasks", [])) / (
            len(execution_result.get("successful_tasks", {})) + len(execution_result.get("failed_tasks", []))
        ) if (execution_result.get("successful_tasks") or execution_result.get("failed_tasks")) else 0
        
        quality_score = max(0, 1.0 - error_rate) * completion_rate
        
        quality_result = {
            "overall_score": quality_score,
            "completion_rate": completion_rate,
            "error_rate": error_rate,
            "meets_threshold": quality_score >= self.config.get("command_tower", {}).get("quality_threshold", 0.8),
            "recommendations": []
        }
        
        # 改善提案
        if error_rate > 0.1:
            quality_result["recommendations"].append("Consider reviewing failed tasks and improving error handling")
        
        if completion_rate < 0.9:
            quality_result["recommendations"].append("Review task dependencies and resource allocation")
        
        context.quality_thresholds = quality_result
        context.execution_history.append({
            "phase": "quality_analysis",
            "timestamp": datetime.now(timezone.utc),
            "quality_metrics": quality_result
        })
        
        return quality_result
    
    async def _complete_command_sequence(
        self,
        execution_result: Dict[str, Any],
        quality_result: Dict[str, Any],
        context: CommandContext
    ) -> Dict[str, Any]:
        """コマンドシーケンス完了処理"""
        self.logger.info("Completing command sequence")
        
        # 完了したタスクの消し込み処理
        if self.config.get("command_tower", {}).get("auto_archive_completed", True):
            completed_tasks = [
                task for task in self.tasks.values()
                if task.status == TaskStatus.COMPLETED and context.session_id in task.id
            ]
            
            for task in completed_tasks:
                task.archive_task("command_sequence_completion")
        
        # 最終結果レポート生成
        completion_result = {
            "session_summary": {
                "user_intent": context.user_intent,
                "execution_phases": len(context.execution_history),
                "total_tasks": len([t for t in self.tasks.values() if context.session_id in t.id]),
                "completed_tasks": len(execution_result.get("successful_tasks", {})),
                "failed_tasks": len(execution_result.get("failed_tasks", [])),
            },
            "quality_assessment": quality_result,
            "performance_metrics": {
                "total_execution_time": sum(
                    (h.get("timestamp", datetime.now(timezone.utc)) - context.execution_history[0]["timestamp"]).total_seconds()
                    for h in context.execution_history[1:]
                ),
                "average_task_time": None  # 実装予定
            },
            "deliverables": execution_result.get("successful_tasks", {}),
            "next_steps": self._generate_next_steps(execution_result, quality_result)
        }
        
        context.execution_history.append({
            "phase": "completion",
            "timestamp": datetime.now(timezone.utc),
            "final_result": completion_result
        })
        
        return completion_result
    
    def _generate_next_steps(self, execution_result: Dict[str, Any], quality_result: Dict[str, Any]) -> List[str]:
        """次のステップ提案"""
        next_steps = []
        
        if execution_result.get("failed_tasks"):
            next_steps.append("Review and retry failed tasks with improved configurations")
        
        if not quality_result.get("meets_threshold", True):
            next_steps.append("Implement quality improvement recommendations")
        
        if quality_result.get("overall_score", 0) > 0.9:
            next_steps.append("Consider expanding scope or optimizing performance further")
        
        next_steps.append("Archive completed tasks and update project documentation")
        
        return next_steps
    
    async def get_system_status(self) -> Dict[str, Any]:
        """システムステータス取得"""
        return {
            "command_tower": {
                "active": self.is_active,
                "startup_time": self.startup_time.isoformat() if self.startup_time else None,
                "active_contexts": len(self.active_contexts),
                "total_tasks": len(self.tasks),
                "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                "in_progress_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
                "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                "archived_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.ARCHIVED])
            },
            "components": {
                "project_orchestrator": await self.project_orchestrator.get_status(),
                "meta_manager": await self.meta_manager.get_status(),
                "agent_coordinator": await self.agent_coordinator.get_status(),
                "claude_bridge": await self.claude_bridge.get_status()
            }
        }
    
    async def shutdown(self):
        """司令塔シャットダウン"""
        self.logger.info("Command Tower shutdown initiated")
        
        # アクティブなコンテキストの保存
        for session_id, context in self.active_contexts.items():
            self.logger.warning(f"Active context during shutdown: {session_id}")
        
        # コンポーネントシャットダウン
        await self.claude_bridge.shutdown()
        await self.agent_coordinator.shutdown()
        await self.meta_manager.shutdown()
        await self.project_orchestrator.shutdown()
        
        self.is_active = False
        self.logger.info("Command Tower shutdown completed")


# グローバルインスタンス
_command_tower_instance: Optional[CommandTower] = None


async def get_command_tower() -> CommandTower:
    """Command Tower インスタンス取得"""
    global _command_tower_instance
    
    if _command_tower_instance is None:
        _command_tower_instance = CommandTower()
        await _command_tower_instance.initialize()
    
    return _command_tower_instance


async def execute_shunsuke_command(user_intent: str) -> Dict[str, Any]:
    """シュンスケ式コマンド実行のエントリーポイント"""
    tower = await get_command_tower()
    return await tower.execute_command_sequence(user_intent)


if __name__ == "__main__":
    # テスト実行
    async def test_command_tower():
        tower = CommandTower()
        await tower.initialize()
        
        result = await tower.execute_command_sequence(
            "Create a comprehensive documentation system with quality analysis"
        )
        
        print(json.dumps(result, indent=2, default=str))
        
        await tower.shutdown()
    
    asyncio.run(test_command_tower())