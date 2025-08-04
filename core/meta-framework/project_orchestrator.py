"""
Ultimate ShunsukeModel Ecosystem - Project Orchestrator
プロジェクトオーケストレーター

Command Tower の指示に基づいて具体的なプロジェクト管理を実行
GitHub Issue ベースのタスク管理と消し込みスタイルワークフローを実装
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
from datetime import datetime, timezone
import subprocess
import tempfile
import shutil

from ...integration.claude_integration.claude_bridge import ClaudeBridge


class ProjectType(Enum):
    """プロジェクトタイプ"""
    MCP_SERVER = "mcp_server"
    CLAUDE_INTEGRATION = "claude_integration"
    DOCUMENTATION = "documentation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    QUALITY_ANALYSIS = "quality_analysis"
    WORKFLOW_AUTOMATION = "workflow_automation"
    UNIFIED_PLATFORM = "unified_platform"


class TaskType(Enum):
    """タスクタイプ"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    INTEGRATION = "integration"


@dataclass
class ProjectSpec:
    """プロジェクト仕様"""
    name: str
    description: str
    project_type: ProjectType
    requirements: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    quality_criteria: Dict[str, float] = field(default_factory=dict)
    timeline: Optional[Dict[str, str]] = None
    dependencies: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSpec:
    """タスク仕様"""
    id: str
    name: str
    description: str
    task_type: TaskType
    project_id: str
    priority: int = 5  # 1-10 scale
    estimated_hours: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    required_agents: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ProjectTemplate:
    """プロジェクトテンプレート"""
    name: str
    description: str
    project_type: ProjectType
    default_structure: Dict[str, Any]
    required_files: List[str]
    optional_files: List[str]
    task_templates: List[Dict[str, Any]]
    agent_requirements: Dict[str, List[str]]


class ProjectOrchestrator:
    """
    プロジェクトオーケストレーター
    
    主要機能:
    1. プロジェクト仕様の解析と分解
    2. タスクの自動生成と依存関係管理
    3. プロジェクトテンプレートの管理
    4. GitHub Issue 統合
    5. 品質基準の管理
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化"""
        self.config = config
        self.templates: Dict[str, ProjectTemplate] = {}
        self.active_projects: Dict[str, ProjectSpec] = {}
        self.task_registry: Dict[str, TaskSpec] = {}
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # GitHub integration
        self.github_enabled = config.get('github_integration', {}).get('enabled', False)
        self.repo_path = config.get('github_integration', {}).get('repo_path')
        
        # Claude integration
        self.claude_bridge = None
        
        # 初期化状態
        self.is_initialized = False
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'project-orchestrator.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """オーケストレーター初期化"""
        try:
            self.logger.info("Project Orchestrator initialization started")
            
            # Claude Bridge 初期化
            if self.config.get('claude_integration', {}).get('enabled', True):
                claude_config = self.config.get('claude_integration', {})
                self.claude_bridge = ClaudeBridge(claude_config)
                await self.claude_bridge.initialize()
            
            # プロジェクトテンプレート読み込み
            await self._load_project_templates()
            
            # GitHub リポジトリ初期化
            if self.github_enabled and self.repo_path:
                await self._initialize_github_repo()
            
            self.is_initialized = True
            self.logger.info("Project Orchestrator initialization completed")
            
        except Exception as e:
            self.logger.error(f"Project Orchestrator initialization failed: {e}")
            raise
    
    async def _load_project_templates(self):
        """プロジェクトテンプレート読み込み"""
        # MCP Server テンプレート
        mcp_template = ProjectTemplate(
            name="MCP Server Template",
            description="Standard MCP Server implementation template",
            project_type=ProjectType.MCP_SERVER,
            default_structure={
                "src/": {"tools/": {}, "utils/": {}, "config.py": None, "server.py": None},
                "tests/": {"test_tools.py": None, "test_server.py": None},
                "docs/": {"API.md": None, "README.md": None},
                "requirements.txt": None,
                "setup.py": None
            },
            required_files=["src/server.py", "requirements.txt", "README.md"],
            optional_files=["setup.py", "Dockerfile", ".github/workflows/"],
            task_templates=[
                {"name": "Setup project structure", "type": "development", "priority": 10},
                {"name": "Implement MCP tools", "type": "development", "priority": 9},
                {"name": "Write tests", "type": "testing", "priority": 7},
                {"name": "Create documentation", "type": "documentation", "priority": 6},
                {"name": "Performance optimization", "type": "optimization", "priority": 5}
            ],
            agent_requirements={
                "development": ["code-striker", "scout-mcp"],
                "testing": ["quality-guardian"],
                "documentation": ["doc-architect"],
                "optimization": ["performance-optimizer"]
            }
        )
        
        # Claude Integration テンプレート
        claude_template = ProjectTemplate(
            name="Claude Integration Template",
            description="Claude Code and Desktop integration template",
            project_type=ProjectType.CLAUDE_INTEGRATION,
            default_structure={
                ".claude/": {
                    "commands/": {},
                    "agents/": {},
                    "hooks/": {},
                    "settings.json": None
                },
                "src/": {"integration/": {}, "hooks/": {}},
                "docs/": {"integration-guide.md": None}
            },
            required_files=[".claude/settings.json", "docs/integration-guide.md"],
            optional_files=[".claude/commands/", ".claude/agents/"],
            task_templates=[
                {"name": "Create slash commands", "type": "development", "priority": 9},
                {"name": "Setup hooks", "type": "integration", "priority": 8},
                {"name": "Configure sub-agents", "type": "integration", "priority": 7},
                {"name": "Test integration", "type": "testing", "priority": 6}
            ],
            agent_requirements={
                "development": ["code-striker"],
                "integration": ["claude-integration-specialist"],
                "testing": ["integration-tester"]
            }
        )
        
        # Documentation テンプレート
        docs_template = ProjectTemplate(
            name="Documentation Template",
            description="Comprehensive documentation system template",
            project_type=ProjectType.DOCUMENTATION,
            default_structure={
                "docs/": {
                    "api/": {},
                    "guides/": {},
                    "examples/": {},
                    "README.md": None,
                    "index.md": None
                },
                "generated_contexts/": {},
                "templates/": {}
            },
            required_files=["docs/README.md", "docs/index.md"],
            optional_files=["docs/api/", "generated_contexts/"],
            task_templates=[
                {"name": "Create documentation structure", "type": "documentation", "priority": 10},
                {"name": "Generate API documentation", "type": "documentation", "priority": 8},
                {"name": "Write user guides", "type": "documentation", "priority": 7},
                {"name": "Create examples", "type": "documentation", "priority": 6}
            ],
            agent_requirements={
                "documentation": ["doc-architect", "content-synthesizer"]
            }
        )
        
        self.templates = {
            ProjectType.MCP_SERVER.value: mcp_template,
            ProjectType.CLAUDE_INTEGRATION.value: claude_template,
            ProjectType.DOCUMENTATION.value: docs_template
        }
        
        self.logger.info(f"Loaded {len(self.templates)} project templates")
    
    async def _initialize_github_repo(self):
        """GitHub リポジトリ初期化"""
        if not self.repo_path or not Path(self.repo_path).exists():
            self.logger.warning("GitHub repository path not found")
            return
        
        try:
            # Git status check
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("GitHub repository initialized successfully")
            else:
                self.logger.warning("Repository exists but git status failed")
                
        except Exception as e:
            self.logger.error(f"GitHub repository initialization failed: {e}")
    
    async def create_task_breakdown(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        意図解析結果からタスク分解を実行
        
        Args:
            analysis: Claude Bridge からの意図解析結果
            
        Returns:
            タスク情報のリスト
        """
        self.logger.info("Creating task breakdown from analysis")
        
        # プロジェクトタイプの推定
        project_type = await self._infer_project_type(analysis)
        self.logger.debug(f"Inferred project type: {project_type}")
        
        # プロジェクト仕様生成
        project_spec = await self._generate_project_spec(analysis, project_type)
        
        # タスク分解実行
        tasks = await self._decompose_into_tasks(project_spec)
        
        # タスクの詳細化
        detailed_tasks = await self._elaborate_tasks(tasks, project_spec)
        
        self.logger.info(f"Generated {len(detailed_tasks)} tasks for project: {project_spec.name}")
        
        return detailed_tasks
    
    async def _infer_project_type(self, analysis: Dict[str, Any]) -> ProjectType:
        """プロジェクトタイプ推定"""
        intent = analysis.get('intent', '').lower()
        keywords = analysis.get('keywords', [])
        context = analysis.get('context', {})
        
        # キーワードベースの推定
        if any(keyword in intent for keyword in ['mcp', 'server', 'tool']):
            return ProjectType.MCP_SERVER
        
        if any(keyword in intent for keyword in ['claude', 'integration', 'slash', 'hook']):
            return ProjectType.CLAUDE_INTEGRATION
        
        if any(keyword in intent for keyword in ['document', 'docs', 'guide', 'manual']):
            return ProjectType.DOCUMENTATION
        
        if any(keyword in intent for keyword in ['performance', 'optimize', 'speed', 'cache']):
            return ProjectType.PERFORMANCE_OPTIMIZATION
        
        if any(keyword in intent for keyword in ['quality', 'analyze', 'test', 'validate']):
            return ProjectType.QUALITY_ANALYSIS
        
        if any(keyword in intent for keyword in ['workflow', 'automation', 'github']):
            return ProjectType.WORKFLOW_AUTOMATION
        
        # デフォルト
        return ProjectType.UNIFIED_PLATFORM
    
    async def _generate_project_spec(self, analysis: Dict[str, Any], project_type: ProjectType) -> ProjectSpec:
        """プロジェクト仕様生成"""
        intent = analysis.get('intent', 'Unknown project')
        requirements = analysis.get('requirements', [])
        constraints = analysis.get('constraints', {})
        
        # プロジェクト名生成
        project_name = analysis.get('suggested_name', f"{project_type.value}_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # 基本仕様
        spec = ProjectSpec(
            name=project_name,
            description=intent,
            project_type=project_type,
            requirements=requirements,
            constraints=constraints,
            quality_criteria={
                'completeness': 0.9,
                'consistency': 0.85,
                'accuracy': 0.9,
                'usability': 0.8
            }
        )
        
        # テンプレートベースの拡張
        if project_type.value in self.templates:
            template = self.templates[project_type.value]
            spec.deliverables = list(template.required_files)
            spec.resources = template.agent_requirements
        
        # Claude による詳細化
        if self.claude_bridge:
            enhanced_spec = await self.claude_bridge.enhance_project_spec(spec.__dict__)
            if enhanced_spec:
                spec.deliverables.extend(enhanced_spec.get('additional_deliverables', []))
                spec.requirements.extend(enhanced_spec.get('additional_requirements', []))
        
        return spec
    
    async def _decompose_into_tasks(self, project_spec: ProjectSpec) -> List[TaskSpec]:
        """プロジェクト仕様からタスク分解"""
        tasks = []
        task_counter = 0
        
        # テンプレートベースのタスク生成
        if project_spec.project_type.value in self.templates:
            template = self.templates[project_spec.project_type.value]
            
            for task_template in template.task_templates:
                task_counter += 1
                task = TaskSpec(
                    id=f"{project_spec.name}_task_{task_counter:03d}",
                    name=task_template['name'],
                    description=f"{task_template['name']} for {project_spec.name}",
                    task_type=TaskType(task_template['type']),
                    project_id=project_spec.name,
                    priority=task_template.get('priority', 5),
                    required_agents=template.agent_requirements.get(task_template['type'], [])
                )
                tasks.append(task)
        
        # 要件ベースの追加タスク
        for requirement in project_spec.requirements:
            if 'test' in requirement.lower():
                task_counter += 1
                task = TaskSpec(
                    id=f"{project_spec.name}_task_{task_counter:03d}",
                    name=f"Implement {requirement}",
                    description=f"Implementation task for requirement: {requirement}",
                    task_type=TaskType.TESTING,
                    project_id=project_spec.name,
                    priority=6
                )
                tasks.append(task)
            
            elif 'document' in requirement.lower():
                task_counter += 1
                task = TaskSpec(
                    id=f"{project_spec.name}_task_{task_counter:03d}",
                    name=f"Document {requirement}",
                    description=f"Documentation task for requirement: {requirement}",
                    task_type=TaskType.DOCUMENTATION,
                    project_id=project_spec.name,
                    priority=4
                )
                tasks.append(task)
        
        # 成果物ベースのタスク
        for deliverable in project_spec.deliverables:
            if deliverable not in [task.name.lower() for task in tasks]:
                task_counter += 1
                task = TaskSpec(
                    id=f"{project_spec.name}_task_{task_counter:03d}",
                    name=f"Create {deliverable}",
                    description=f"Create deliverable: {deliverable}",
                    task_type=TaskType.DEVELOPMENT,
                    project_id=project_spec.name,
                    priority=7
                )
                tasks.append(task)
        
        self.logger.debug(f"Generated {len(tasks)} tasks from project spec")
        return tasks
    
    async def _elaborate_tasks(self, tasks: List[TaskSpec], project_spec: ProjectSpec) -> List[Dict[str, Any]]:
        """タスク詳細化"""
        detailed_tasks = []
        
        for task in tasks:
            # 成功基準の設定
            success_criteria = []
            if task.task_type == TaskType.DEVELOPMENT:
                success_criteria = [
                    "Code implementation completed",
                    "Unit tests passing",
                    "Code review approved"
                ]
            elif task.task_type == TaskType.TESTING:
                success_criteria = [
                    "Test cases implemented",
                    "All tests passing",
                    "Coverage threshold met"
                ]
            elif task.task_type == TaskType.DOCUMENTATION:
                success_criteria = [
                    "Documentation written",
                    "Examples provided",
                    "Review completed"
                ]
            
            task.success_criteria = success_criteria
            
            # エージェント要件の詳細化
            agent_requirements = {}
            if task.required_agents:
                agent_requirements = {
                    'required': task.required_agents,
                    'preferred_count': min(len(task.required_agents), 3),
                    'specializations': [task.task_type.value]
                }
            
            # タスク辞書作成
            task_dict = {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'type': task.task_type.value,
                'priority': self._priority_to_string(task.priority),
                'estimated_hours': task.estimated_hours,
                'dependencies': task.dependencies,
                'success_criteria': task.success_criteria,
                'agent_requirements': agent_requirements,
                'metadata': {
                    'project_id': task.project_id,
                    'project_type': project_spec.project_type.value,
                    'created_at': task.created_at.isoformat(),
                    'quality_criteria': project_spec.quality_criteria
                }
            }
            
            detailed_tasks.append(task_dict)
            
            # タスクレジストリに登録
            self.task_registry[task.id] = task
        
        return detailed_tasks
    
    def _priority_to_string(self, priority: int) -> str:
        """優先度数値を文字列に変換"""
        if priority >= 9:
            return "critical"
        elif priority >= 7:
            return "high"
        elif priority >= 5:
            return "medium"
        else:
            return "low"
    
    async def create_github_issues(self, tasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """GitHub Issues 作成"""
        if not self.github_enabled or not self.repo_path:
            self.logger.warning("GitHub integration not enabled")
            return {}
        
        issue_map = {}
        
        for task in tasks:
            try:
                # Issue body 作成
                body = f"""
## Task Description
{task['description']}

## Success Criteria
{chr(10).join(f"- [ ] {criteria}" for criteria in task.get('success_criteria', []))}

## Priority
{task.get('priority', 'medium')}

## Agent Requirements
{', '.join(task.get('agent_requirements', {}).get('required', []))}

## Metadata
- Project: {task['metadata'].get('project_id', 'Unknown')}
- Type: {task.get('type', 'Unknown')}
- Created: {task['metadata'].get('created_at', 'Unknown')}

---
*Generated by Ultimate ShunsukeModel Ecosystem - Project Orchestrator*
"""
                
                # GitHub CLI を使用してIssue作成
                cmd = [
                    'gh', 'issue', 'create',
                    '--title', task['name'],
                    '--body', body,
                    '--label', task.get('type', 'task'),
                    '--label', task.get('priority', 'medium')
                ]
                
                result = subprocess.run(
                    cmd,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    issue_url = result.stdout.strip()
                    issue_map[task['id']] = issue_url
                    self.logger.info(f"Created GitHub Issue for task {task['id']}: {issue_url}")
                else:
                    self.logger.error(f"Failed to create GitHub Issue for task {task['id']}: {result.stderr}")
                    
            except Exception as e:
                self.logger.error(f"Error creating GitHub Issue for task {task['id']}: {e}")
        
        return issue_map
    
    async def update_task_status(self, task_id: str, status: str, details: Dict[str, Any] = None):
        """タスクステータス更新"""
        if task_id not in self.task_registry:
            self.logger.warning(f"Task not found in registry: {task_id}")
            return
        
        task = self.task_registry[task_id]
        old_status = task.metadata.get('status', 'unknown')
        
        # メタデータ更新
        task.metadata['status'] = status
        task.metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        if details:
            task.metadata.update(details)
        
        self.logger.info(f"Task {task_id} status updated: {old_status} -> {status}")
        
        # GitHub Issue 更新（実装予定）
        if self.github_enabled:
            await self._update_github_issue(task_id, status, details)
    
    async def _update_github_issue(self, task_id: str, status: str, details: Dict[str, Any] = None):
        """GitHub Issue ステータス更新"""
        # 実装予定: GitHub Issue のラベルやコメントを更新
        pass
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """プロジェクト状況取得"""
        project_tasks = [
            task for task in self.task_registry.values()
            if task.project_id == project_id
        ]
        
        if not project_tasks:
            return {"error": f"No tasks found for project: {project_id}"}
        
        status_counts = {}
        for task in project_tasks:
            task_status = task.metadata.get('status', 'pending')
            status_counts[task_status] = status_counts.get(task_status, 0) + 1
        
        total_tasks = len(project_tasks)
        completed_tasks = status_counts.get('completed', 0)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            "project_id": project_id,
            "total_tasks": total_tasks,
            "status_breakdown": status_counts,
            "completion_rate": completion_rate,
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.metadata.get('status', 'pending'),
                    "priority": task.priority
                }
                for task in project_tasks
            ]
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """オーケストレーター状態取得"""
        return {
            "initialized": self.is_initialized,
            "active_projects": len(self.active_projects),
            "total_tasks": len(self.task_registry),
            "templates_loaded": len(self.templates),
            "github_enabled": self.github_enabled,
            "claude_bridge_active": self.claude_bridge is not None
        }
    
    async def shutdown(self):
        """オーケストレーターシャットダウン"""
        self.logger.info("Project Orchestrator shutdown initiated")
        
        if self.claude_bridge:
            await self.claude_bridge.shutdown()
        
        self.is_initialized = False
        self.logger.info("Project Orchestrator shutdown completed")


if __name__ == "__main__":
    # テスト実行
    async def test_orchestrator():
        config = {
            'github_integration': {
                'enabled': False,
                'repo_path': None
            },
            'claude_integration': {
                'enabled': True
            }
        }
        
        orchestrator = ProjectOrchestrator(config)
        await orchestrator.initialize()
        
        # テスト解析結果
        analysis = {
            'intent': 'Create a comprehensive MCP server with quality analysis',
            'keywords': ['mcp', 'server', 'quality', 'analysis'],
            'requirements': ['implement tools', 'write tests', 'create documentation'],
            'context': {}
        }
        
        tasks = await orchestrator.create_task_breakdown(analysis)
        print(json.dumps(tasks, indent=2, default=str))
        
        await orchestrator.shutdown()
    
    asyncio.run(test_orchestrator())