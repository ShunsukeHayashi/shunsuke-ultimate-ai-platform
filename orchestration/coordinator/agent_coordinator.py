"""
Ultimate ShunsukeModel Ecosystem - Agent Coordinator
AIエージェント協調システム

複数のAIエージェントの協調実行、リソース管理、通信調整を行う
シュンスケ式マルチエージェント協調フレームワークの中核
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
from datetime import datetime, timezone
import uuid

from ...agents.scout_mcp.scout_agent import ScoutAgent
from ...agents.code_striker.code_striker_agent import CodeStrikerAgent
from ...agents.doc_architect.doc_architect_agent import DocArchitectAgent
from ...agents.quality_guardian.quality_guardian_agent import QualityGuardianAgent
from ...agents.review_libero.review_libero_agent import ReviewLiberoAgent


class AgentType(Enum):
    """エージェントタイプ"""
    SCOUT = "scout"  # 情報収集・分析
    CODE_STRIKER = "code_striker"  # コード生成・実装
    DOC_ARCHITECT = "doc_architect"  # ドキュメント作成
    QUALITY_GUARDIAN = "quality_guardian"  # 品質保証
    REVIEW_LIBERO = "review_libero"  # コードレビュー・最適化
    PERFORMANCE_OPTIMIZER = "performance_optimizer"  # パフォーマンス最適化
    INTEGRATION_SPECIALIST = "integration_specialist"  # 統合専門


class AgentStatus(Enum):
    """エージェント状態"""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """タスク優先度"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class AgentCapability:
    """エージェント能力"""
    name: str
    description: str
    complexity_level: int = 1  # 1-10
    resource_requirement: float = 1.0
    execution_time_estimate: float = 60.0  # seconds
    success_rate: float = 0.9
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentInstance:
    """エージェントインスタンス"""
    id: str
    agent_type: AgentType
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[AgentCapability] = field(default_factory=list)
    current_task: Optional[str] = None
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    # 実際のエージェントオブジェクト
    agent_object: Optional[Any] = None


@dataclass
class CollaborativeTask:
    """協調タスク"""
    id: str
    name: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    required_agents: List[AgentType] = field(default_factory=list)
    assigned_agents: List[str] = field(default_factory=list)  # agent instance IDs
    dependencies: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None
    status: str = "pending"
    progress: float = 0.0
    results: Dict[str, Any] = field(default_factory=dict)
    communication_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AgentMessage:
    """エージェント間メッセージ"""
    id: str
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requires_response: bool = False
    response_timeout: Optional[float] = None


class AgentCoordinator:
    """
    AIエージェント協調システム
    
    主要機能:
    1. エージェント管理とライフサイクル制御
    2. タスク配分と負荷分散
    3. エージェント間通信の調整
    4. リソース管理と最適化
    5. パフォーマンス監視と改善
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config
        self.agents: Dict[str, AgentInstance] = {}
        self.tasks: Dict[str, CollaborativeTask] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.communication_channels: Dict[str, asyncio.Queue] = {}
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 設定値
        self.max_concurrent_tasks = config.get('max_concurrent_tasks', 10)
        self.agent_timeout = config.get('agent_timeout', 300)  # 5 minutes
        self.heartbeat_interval = config.get('heartbeat_interval', 30)  # 30 seconds
        self.auto_scaling_enabled = config.get('auto_scaling', True)
        
        # 協調戦略
        self.collaboration_strategies = {
            'sequential': self._execute_sequential,
            'parallel': self._execute_parallel,
            'pipeline': self._execute_pipeline,
            'hierarchical': self._execute_hierarchical
        }
        
        # 初期化状態
        self.is_initialized = False
        self._shutdown_event = asyncio.Event()
        self._background_tasks = set()
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'agent-coordinator.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """エージェント協調システム初期化"""
        try:
            self.logger.info("Agent Coordinator initialization started")
            
            # エージェントインスタンス作成
            await self._create_agent_instances()
            
            # 通信チャネル初期化
            await self._initialize_communication_channels()
            
            # バックグラウンドタスク開始
            await self._start_background_tasks()
            
            self.is_initialized = True
            self.logger.info("Agent Coordinator initialization completed")
            
        except Exception as e:
            self.logger.error(f"Agent Coordinator initialization failed: {e}")
            raise
    
    async def _create_agent_instances(self):
        """エージェントインスタンス作成"""
        # 設定からエージェント定義を読み込み
        agent_configs = self.config.get('agents', {})
        
        # デフォルトエージェント設定
        default_agents = {
            AgentType.SCOUT: {
                'count': 2,
                'capabilities': [
                    AgentCapability(
                        name="web_content_analysis",
                        description="Web content extraction and analysis",
                        complexity_level=5,
                        execution_time_estimate=120.0
                    ),
                    AgentCapability(
                        name="context_structuring",
                        description="Hierarchical context structure creation",
                        complexity_level=6,
                        execution_time_estimate=90.0
                    )
                ]
            },
            AgentType.CODE_STRIKER: {
                'count': 2,
                'capabilities': [
                    AgentCapability(
                        name="code_generation",
                        description="High-quality code generation",
                        complexity_level=8,
                        execution_time_estimate=180.0
                    ),
                    AgentCapability(
                        name="refactoring",
                        description="Code refactoring and optimization",
                        complexity_level=7,
                        execution_time_estimate=150.0
                    )
                ]
            },
            AgentType.DOC_ARCHITECT: {
                'count': 1,
                'capabilities': [
                    AgentCapability(
                        name="documentation_generation",
                        description="Comprehensive documentation creation",
                        complexity_level=6,
                        execution_time_estimate=120.0
                    ),
                    AgentCapability(
                        name="api_documentation",
                        description="API documentation and examples",
                        complexity_level=5,
                        execution_time_estimate=90.0
                    )
                ]
            },
            AgentType.QUALITY_GUARDIAN: {
                'count': 1,
                'capabilities': [
                    AgentCapability(
                        name="quality_analysis",
                        description="Comprehensive quality assessment",
                        complexity_level=7,
                        execution_time_estimate=100.0
                    ),
                    AgentCapability(
                        name="test_generation",
                        description="Automated test case generation",
                        complexity_level=6,
                        execution_time_estimate=120.0
                    )
                ]
            },
            AgentType.REVIEW_LIBERO: {
                'count': 1,
                'capabilities': [
                    AgentCapability(
                        name="code_review",
                        description="Thorough code review and suggestions",
                        complexity_level=8,
                        execution_time_estimate=150.0
                    ),
                    AgentCapability(
                        name="optimization_suggestions",
                        description="Performance and structure optimization",
                        complexity_level=7,
                        execution_time_estimate=120.0
                    )
                ]
            }
        }
        
        # エージェントインスタンス生成
        for agent_type, config in default_agents.items():
            count = agent_configs.get(agent_type.value, {}).get('count', config['count'])
            
            for i in range(count):
                agent_id = f"{agent_type.value}_{i+1}"
                
                # エージェントオブジェクト作成
                agent_object = await self._create_agent_object(agent_type, agent_id)
                
                # エージェントインスタンス作成
                instance = AgentInstance(
                    id=agent_id,
                    agent_type=agent_type,
                    capabilities=config['capabilities'].copy(),
                    agent_object=agent_object,
                    configuration=agent_configs.get(agent_type.value, {})
                )
                
                self.agents[agent_id] = instance
                
                # 通信チャネル作成
                self.communication_channels[agent_id] = asyncio.Queue()
                
                self.logger.info(f"Created agent instance: {agent_id}")
        
        self.logger.info(f"Created {len(self.agents)} agent instances")
    
    async def _create_agent_object(self, agent_type: AgentType, agent_id: str):
        """エージェントオブジェクト作成"""
        # エージェントタイプに応じて実際のエージェントオブジェクトを作成
        if agent_type == AgentType.SCOUT:
            return ScoutAgent(agent_id, self.config.get('scout', {}))
        elif agent_type == AgentType.CODE_STRIKER:
            return CodeStrikerAgent(agent_id, self.config.get('code_striker', {}))
        elif agent_type == AgentType.DOC_ARCHITECT:
            return DocArchitectAgent(agent_id, self.config.get('doc_architect', {}))
        elif agent_type == AgentType.QUALITY_GUARDIAN:
            return QualityGuardianAgent(agent_id, self.config.get('quality_guardian', {}))
        elif agent_type == AgentType.REVIEW_LIBERO:
            return ReviewLiberoAgent(agent_id, self.config.get('review_libero', {}))
        else:
            # プレースホルダーエージェント
            return MockAgent(agent_id, agent_type)
    
    async def _initialize_communication_channels(self):
        """通信チャネル初期化"""
        # メッセージ処理タスク開始
        message_processor = asyncio.create_task(self._process_messages())
        self._background_tasks.add(message_processor)
        
        self.logger.info("Communication channels initialized")
    
    async def _start_background_tasks(self):
        """バックグラウンドタスク開始"""
        # ハートビート監視
        heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        self._background_tasks.add(heartbeat_task)
        
        # パフォーマンス監視
        performance_task = asyncio.create_task(self._performance_monitor())
        self._background_tasks.add(performance_task)
        
        # タスクスケジューラー
        scheduler_task = asyncio.create_task(self._task_scheduler())
        self._background_tasks.add(scheduler_task)
        
        self.logger.info("Background tasks started")
    
    async def allocate_agents_to_tasks(self, task_requests: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        タスクにエージェントを配分
        
        Args:
            task_requests: タスク要求リスト [{"id": str, "requirements": Dict}, ...]
            
        Returns:
            タスクIDとエージェントIDリストのマッピング
        """
        allocation = {}
        
        for task_request in task_requests:
            task_id = task_request['id']
            requirements = task_request.get('requirements', {})
            
            # 必要なエージェントタイプを特定
            required_types = self._determine_required_agent_types(requirements)
            
            # 利用可能なエージェントを検索
            allocated_agents = []
            for agent_type in required_types:
                available_agent = await self._find_available_agent(agent_type)
                if available_agent:
                    allocated_agents.append(available_agent.id)
                    available_agent.status = AgentStatus.BUSY
                    available_agent.current_task = task_id
                    
                    self.logger.info(f"Allocated agent {available_agent.id} to task {task_id}")
            
            allocation[task_id] = allocated_agents
        
        return allocation
    
    def _determine_required_agent_types(self, requirements: Dict[str, Any]) -> List[AgentType]:
        """必要なエージェントタイプを決定"""
        required_types = []
        
        # 要求内容からエージェントタイプを推定
        req_lower = str(requirements).lower()
        
        if any(keyword in req_lower for keyword in ['web', 'crawl', 'extract', 'analyze']):
            required_types.append(AgentType.SCOUT)
        
        if any(keyword in req_lower for keyword in ['code', 'implement', 'develop', 'program']):
            required_types.append(AgentType.CODE_STRIKER)
        
        if any(keyword in req_lower for keyword in ['document', 'doc', 'guide', 'manual']):
            required_types.append(AgentType.DOC_ARCHITECT)
        
        if any(keyword in req_lower for keyword in ['quality', 'test', 'validate', 'check']):
            required_types.append(AgentType.QUALITY_GUARDIAN)
        
        if any(keyword in req_lower for keyword in ['review', 'optimize', 'improve', 'refactor']):
            required_types.append(AgentType.REVIEW_LIBERO)
        
        # デフォルト: SCOUT エージェント
        if not required_types:
            required_types.append(AgentType.SCOUT)
        
        return required_types
    
    async def _find_available_agent(self, agent_type: AgentType) -> Optional[AgentInstance]:
        """利用可能なエージェントを検索"""
        candidates = [
            agent for agent in self.agents.values()
            if agent.agent_type == agent_type and agent.status == AgentStatus.IDLE
        ]
        
        if not candidates:
            return None
        
        # パフォーマンスメトリクスに基づいて最適なエージェントを選択
        return min(candidates, key=lambda a: a.resource_usage.get('cpu', 0))
    
    async def execute_task_with_agents(
        self,
        task_id: str,
        agents: List[str],
        task_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        エージェントを使用してタスクを実行
        
        Args:
            task_id: タスクID
            agents: 割り当てられたエージェントIDリスト
            task_spec: タスク仕様
            
        Returns:
            実行結果
        """
        if not agents:
            return {"success": False, "error": "No agents allocated"}
        
        # 協調タスク作成
        task = CollaborativeTask(
            id=task_id,
            name=task_spec.get('name', 'Unnamed Task'),
            description=task_spec.get('description', ''),
            assigned_agents=agents,
            priority=TaskPriority(task_spec.get('priority', 3))
        )
        
        self.tasks[task_id] = task
        
        try:
            # 協調戦略の決定
            strategy = self._determine_collaboration_strategy(task, agents)
            
            # タスク実行
            result = await self.collaboration_strategies[strategy](task)
            
            # 結果の統合
            final_result = await self._integrate_results(task, result)
            
            # エージェントステータス更新
            await self._release_agents(agents)
            
            task.status = "completed"
            task.progress = 1.0
            task.updated_at = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "task_id": task_id,
                "result": final_result,
                "agents_used": agents,
                "execution_time": (task.updated_at - task.created_at).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {task_id} - {e}")
            
            # エラー時のクリーンアップ
            await self._release_agents(agents)
            task.status = "failed"
            task.updated_at = datetime.now(timezone.utc)
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
                "agents_used": agents
            }
    
    def _determine_collaboration_strategy(self, task: CollaborativeTask, agents: List[str]) -> str:
        """協調戦略決定"""
        # エージェントタイプを分析
        agent_types = [self.agents[agent_id].agent_type for agent_id in agents]
        
        # 単一エージェント
        if len(agents) == 1:
            return 'sequential'
        
        # 異なるタイプのエージェント -> パイプライン
        if len(set(agent_types)) == len(agent_types):
            return 'pipeline'
        
        # 同じタイプのエージェント -> 並列
        if len(set(agent_types)) == 1:
            return 'parallel'
        
        # 混合 -> 階層的
        return 'hierarchical'
    
    async def _execute_sequential(self, task: CollaborativeTask) -> Dict[str, Any]:
        """順次実行戦略"""
        results = {}
        
        for agent_id in task.assigned_agents:
            agent = self.agents[agent_id]
            
            # エージェントにタスクを送信
            result = await self._send_task_to_agent(agent, task, results)
            results[agent_id] = result
            
            # 進捗更新
            task.progress = len(results) / len(task.assigned_agents)
        
        return results
    
    async def _execute_parallel(self, task: CollaborativeTask) -> Dict[str, Any]:
        """並列実行戦略"""
        # 全エージェントに並行してタスクを送信
        tasks = []
        for agent_id in task.assigned_agents:
            agent = self.agents[agent_id]
            agent_task = asyncio.create_task(
                self._send_task_to_agent(agent, task, {})
            )
            tasks.append((agent_id, agent_task))
        
        # 結果を収集
        results = {}
        for agent_id, agent_task in tasks:
            try:
                result = await agent_task
                results[agent_id] = result
            except Exception as e:
                self.logger.error(f"Agent {agent_id} failed: {e}")
                results[agent_id] = {"success": False, "error": str(e)}
        
        return results
    
    async def _execute_pipeline(self, task: CollaborativeTask) -> Dict[str, Any]:
        """パイプライン実行戦略"""
        results = {}
        pipeline_data = {}
        
        for i, agent_id in enumerate(task.assigned_agents):
            agent = self.agents[agent_id]
            
            # 前段の結果を入力として使用
            input_data = pipeline_data if i > 0 else {}
            
            result = await self._send_task_to_agent(agent, task, input_data)
            results[agent_id] = result
            
            # 次段への出力を準備
            if result.get('success', False):
                pipeline_data.update(result.get('output', {}))
            
            task.progress = (i + 1) / len(task.assigned_agents)
        
        return results
    
    async def _execute_hierarchical(self, task: CollaborativeTask) -> Dict[str, Any]:
        """階層実行戦略"""
        # エージェントタイプ別にグループ化
        agent_groups = {}
        for agent_id in task.assigned_agents:
            agent = self.agents[agent_id]
            agent_type = agent.agent_type
            
            if agent_type not in agent_groups:
                agent_groups[agent_type] = []
            agent_groups[agent_type].append(agent_id)
        
        # 階層順序定義 (依存関係に基づく)
        hierarchy_order = [
            AgentType.SCOUT,  # 情報収集
            AgentType.CODE_STRIKER,  # 実装
            AgentType.QUALITY_GUARDIAN,  # 品質確認
            AgentType.DOC_ARCHITECT,  # ドキュメント作成
            AgentType.REVIEW_LIBERO  # 最終レビュー
        ]
        
        results = {}
        accumulated_data = {}
        
        for agent_type in hierarchy_order:
            if agent_type in agent_groups:
                # このタイプのエージェントを並列実行
                group_agents = agent_groups[agent_type]
                group_tasks = []
                
                for agent_id in group_agents:
                    agent = self.agents[agent_id]
                    agent_task = asyncio.create_task(
                        self._send_task_to_agent(agent, task, accumulated_data)
                    )
                    group_tasks.append((agent_id, agent_task))
                
                # グループ結果を収集
                for agent_id, agent_task in group_tasks:
                    result = await agent_task
                    results[agent_id] = result
                    
                    if result.get('success', False):
                        accumulated_data.update(result.get('output', {}))
        
        return results
    
    async def _send_task_to_agent(
        self,
        agent: AgentInstance,
        task: CollaborativeTask,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """エージェントにタスクを送信"""
        try:
            # タスクメッセージ作成
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender="coordinator",
                receiver=agent.id,
                message_type="task_execution",
                content={
                    "task_id": task.id,
                    "task_name": task.name,
                    "task_description": task.description,
                    "context_data": context_data,
                    "priority": task.priority.value
                },
                requires_response=True,
                response_timeout=self.agent_timeout
            )
            
            # エージェントの実行メソッドを呼び出し
            if agent.agent_object and hasattr(agent.agent_object, 'execute_task'):
                result = await agent.agent_object.execute_task(message.content)
            else:
                # モックエージェントの場合
                result = await self._mock_agent_execution(agent, message.content)
            
            # 通信ログに記録
            task.communication_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sender": "coordinator",
                "receiver": agent.id,
                "action": "task_sent",
                "result": "success"
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send task to agent {agent.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent.id
            }
    
    async def _mock_agent_execution(self, agent: AgentInstance, task_content: Dict[str, Any]) -> Dict[str, Any]:
        """モックエージェント実行"""
        # デモ用の簡易実行
        await asyncio.sleep(1)  # 処理時間をシミュレート
        
        return {
            "success": True,
            "agent_id": agent.id,
            "agent_type": agent.agent_type.value,
            "task_id": task_content.get("task_id"),
            "output": {
                "message": f"Task completed by {agent.agent_type.value}",
                "capabilities_used": [cap.name for cap in agent.capabilities],
                "execution_time": 1.0
            }
        }
    
    async def _integrate_results(self, task: CollaborativeTask, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """結果統合"""
        integrated_result = {
            "task_id": task.id,
            "task_name": task.name,
            "agents_participated": len(agent_results),
            "successful_agents": len([r for r in agent_results.values() if r.get('success', False)]),
            "agent_results": agent_results,
            "combined_output": {},
            "quality_metrics": {},
            "recommendations": []
        }
        
        # 成功した結果を統合
        successful_results = [r for r in agent_results.values() if r.get('success', False)]
        
        if successful_results:
            # 出力データを統合
            for result in successful_results:
                if 'output' in result:
                    integrated_result["combined_output"].update(result['output'])
            
            # 品質メトリクス計算
            success_rate = len(successful_results) / len(agent_results)
            integrated_result["quality_metrics"] = {
                "success_rate": success_rate,
                "agent_performance": {
                    agent_id: result.get('output', {}).get('execution_time', 0)
                    for agent_id, result in agent_results.items()
                }
            }
            
            # 推奨事項生成
            if success_rate < 1.0:
                integrated_result["recommendations"].append(
                    "Some agents failed to complete their tasks. Consider reviewing agent configurations."
                )
        
        return integrated_result
    
    async def _release_agents(self, agent_ids: List[str]):
        """エージェントを解放"""
        for agent_id in agent_ids:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.status = AgentStatus.IDLE
                agent.current_task = None
                agent.last_activity = datetime.now(timezone.utc)
                
                self.logger.debug(f"Released agent: {agent_id}")
    
    async def _process_messages(self):
        """メッセージ処理"""
        while not self._shutdown_event.is_set():
            try:
                # メッセージキューからメッセージを取得 (タイムアウト付き)
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                # メッセージ処理
                await self._handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
    
    async def _handle_message(self, message: AgentMessage):
        """メッセージ処理"""
        # 受信者が存在するかチェック
        if message.receiver not in self.agents:
            self.logger.warning(f"Message receiver not found: {message.receiver}")
            return
        
        # メッセージタイプに応じた処理
        if message.message_type == "status_update":
            await self._handle_status_update(message)
        elif message.message_type == "performance_report":
            await self._handle_performance_report(message)
        elif message.message_type == "error_report":
            await self._handle_error_report(message)
    
    async def _handle_status_update(self, message: AgentMessage):
        """ステータス更新処理"""
        agent_id = message.sender
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            status_data = message.content
            
            # ステータス更新
            if 'status' in status_data:
                agent.status = AgentStatus(status_data['status'])
            
            if 'resource_usage' in status_data:
                agent.resource_usage.update(status_data['resource_usage'])
            
            agent.last_activity = datetime.now(timezone.utc)
    
    async def _handle_performance_report(self, message: AgentMessage):
        """パフォーマンスレポート処理"""
        agent_id = message.sender
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            performance_data = message.content
            
            agent.performance_metrics.update(performance_data)
    
    async def _handle_error_report(self, message: AgentMessage):
        """エラーレポート処理"""
        agent_id = message.sender
        error_data = message.content
        
        self.logger.error(f"Agent {agent_id} reported error: {error_data}")
        
        # エラーを受けたエージェントのステータス更新
        if agent_id in self.agents:
            self.agents[agent_id].status = AgentStatus.ERROR
    
    async def _heartbeat_monitor(self):
        """ハートビート監視"""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.now(timezone.utc)
                timeout_threshold = current_time - timedelta(seconds=self.heartbeat_interval * 2)
                
                # タイムアウトエージェントをチェック
                for agent in self.agents.values():
                    if agent.last_activity < timeout_threshold and agent.status != AgentStatus.OFFLINE:
                        self.logger.warning(f"Agent {agent.id} appears to be unresponsive")
                        agent.status = AgentStatus.ERROR
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"Heartbeat monitor error: {e}")
    
    async def _performance_monitor(self):
        """パフォーマンス監視"""
        while not self._shutdown_event.is_set():
            try:
                # パフォーマンスメトリクス収集
                for agent in self.agents.values():
                    if agent.status == AgentStatus.BUSY:
                        # CPU使用率等の更新 (実際の実装では外部モニタリングツールと連携)
                        agent.resource_usage['cpu'] = agent.resource_usage.get('cpu', 0) + 0.1
                
                await asyncio.sleep(60)  # 1分間隔
                
            except Exception as e:
                self.logger.error(f"Performance monitor error: {e}")
    
    async def _task_scheduler(self):
        """タスクスケジューラー"""
        while not self._shutdown_event.is_set():
            try:
                # 待機中のタスクをチェック
                pending_tasks = [t for t in self.tasks.values() if t.status == "pending"]
                
                for task in pending_tasks:
                    # リソースが利用可能かチェック
                    if await self._can_execute_task(task):
                        task.status = "ready"
                        self.logger.info(f"Task {task.id} is ready for execution")
                
                await asyncio.sleep(10)  # 10秒間隔
                
            except Exception as e:
                self.logger.error(f"Task scheduler error: {e}")
    
    async def _can_execute_task(self, task: CollaborativeTask) -> bool:
        """タスク実行可能性チェック"""
        # 必要なエージェントが利用可能かチェック
        available_agents = [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
        
        return len(available_agents) >= len(task.required_agents)
    
    async def get_status(self) -> Dict[str, Any]:
        """エージェント協調システム状態取得"""
        agent_status_counts = {}
        for status in AgentStatus:
            agent_status_counts[status.value] = len([
                a for a in self.agents.values() if a.status == status
            ])
        
        return {
            "initialized": self.is_initialized,
            "total_agents": len(self.agents),
            "agent_status": agent_status_counts,
            "active_tasks": len([t for t in self.tasks.values() if t.status in ["pending", "running"]]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
            "communication_channels": len(self.communication_channels),
            "message_queue_size": self.message_queue.qsize()
        }
    
    async def shutdown(self):
        """エージェント協調システムシャットダウン"""
        self.logger.info("Agent Coordinator shutdown initiated")
        
        # シャットダウンイベント設定
        self._shutdown_event.set()
        
        # アクティブなタスクの保存
        active_tasks = [t for t in self.tasks.values() if t.status in ["pending", "running"]]
        if active_tasks:
            self.logger.warning(f"Shutting down with {len(active_tasks)} active tasks")
        
        # エージェントシャットダウン
        for agent in self.agents.values():
            if agent.agent_object and hasattr(agent.agent_object, 'shutdown'):
                try:
                    await agent.agent_object.shutdown()
                except Exception as e:
                    self.logger.error(f"Error shutting down agent {agent.id}: {e}")
        
        # バックグラウンドタスクの終了を待機
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self.is_initialized = False
        self.logger.info("Agent Coordinator shutdown completed")


class MockAgent:
    """モックエージェント（開発用）"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
    
    async def execute_task(self, task_content: Dict[str, Any]) -> Dict[str, Any]:
        """タスク実行"""
        await asyncio.sleep(0.5)  # 処理時間をシミュレート
        
        return {
            "success": True,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "output": {
                "message": f"Mock execution by {self.agent_type.value}",
                "task_id": task_content.get("task_id"),
                "execution_time": 0.5
            }
        }
    
    async def shutdown(self):
        """シャットダウン"""
        pass


if __name__ == "__main__":
    # テスト実行
    async def test_coordinator():
        config = {
            'max_concurrent_tasks': 5,
            'agents': {
                'scout': {'count': 1},
                'code_striker': {'count': 1},
                'doc_architect': {'count': 1}
            }
        }
        
        coordinator = AgentCoordinator(config)
        await coordinator.initialize()
        
        # テストタスク配分
        task_requests = [
            {
                "id": "test_task_1",
                "requirements": {"web": True, "code": True, "documentation": True}
            }
        ]
        
        allocation = await coordinator.allocate_agents_to_tasks(task_requests)
        print("Agent allocation:", allocation)
        
        # テストタスク実行
        if allocation["test_task_1"]:
            result = await coordinator.execute_task_with_agents(
                "test_task_1",
                allocation["test_task_1"],
                {
                    "name": "Test Collaborative Task",
                    "description": "Test task for agent coordination"
                }
            )
            print("Task result:", json.dumps(result, indent=2, default=str))
        
        # ステータス確認
        status = await coordinator.get_status()
        print("Coordinator status:", json.dumps(status, indent=2))
        
        await coordinator.shutdown()
    
    asyncio.run(test_coordinator())