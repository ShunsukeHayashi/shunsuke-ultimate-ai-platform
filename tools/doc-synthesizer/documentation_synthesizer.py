"""
Ultimate ShunsukeModel Ecosystem - Documentation Synthesizer
自動ドキュメント生成システム

コードベース、API、アーキテクチャから包括的なドキュメントを自動生成
多言語対応、テンプレート管理、品質保証機能を統合
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
import re
import ast
from datetime import datetime, timezone
import hashlib
import shutil
import subprocess

from ...orchestration.communication.communication_protocol import CommunicationProtocol, MessageType
from ...tools.quality_analyzer.quality_guardian import QualityReport

# 多言語対応システムのインポート
from .multilingual_manager import (
    MultilingualManager, LanguageCode, DocumentStyle, 
    TranslationRequest, create_multilingual_manager
)
from .multilingual_templates import (
    MultilingualTemplateManager, TemplateType,
    create_multilingual_template_manager
)


class DocumentType(Enum):
    """ドキュメントタイプ"""
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    ARCHITECTURE = "architecture"
    TUTORIAL = "tutorial"
    README = "readme"
    CHANGELOG = "changelog"
    CONTRIBUTING = "contributing"
    DEPLOYMENT = "deployment"
    TROUBLESHOOTING = "troubleshooting"


class DocumentFormat(Enum):
    """ドキュメント形式"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    RST = "rst"
    ASCIIDOC = "asciidoc"
    CONFLUENCE = "confluence"
    NOTION = "notion"


class Language(Enum):
    """対応言語"""
    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ITALIAN = "it"


class DocumentationQuality(Enum):
    """ドキュメント品質レベル"""
    MINIMAL = "minimal"      # 最小限の情報
    STANDARD = "standard"    # 標準的な詳細度
    COMPREHENSIVE = "comprehensive"  # 包括的で詳細
    EXPERT = "expert"        # 専門家レベルの詳細


@dataclass
class DocumentSection:
    """ドキュメントセクション"""
    id: str
    title: str
    content: str
    level: int = 1  # ヘッダーレベル
    order: int = 0
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    language: Language = Language.ENGLISH
    
    def to_markdown(self, base_level: int = 1) -> str:
        """Markdown形式に変換"""
        header_level = "#" * min(base_level + self.level - 1, 6)
        md_content = f"{header_level} {self.title}\n\n{self.content}\n\n"
        
        # サブセクション追加
        for subsection in sorted(self.subsections, key=lambda s: s.order):
            md_content += subsection.to_markdown(base_level + self.level)
        
        return md_content


@dataclass
class DocumentTemplate:
    """ドキュメントテンプレート"""
    name: str
    document_type: DocumentType
    sections: List[str] = field(default_factory=list)  # セクション順序
    required_sections: Set[str] = field(default_factory=set)
    optional_sections: Set[str] = field(default_factory=set)
    frontmatter_template: Dict[str, Any] = field(default_factory=dict)
    style_config: Dict[str, Any] = field(default_factory=dict)
    language_specific: Dict[Language, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class DocumentationConfig:
    """ドキュメント生成設定"""
    project_path: Path
    output_path: Path
    languages: List[Language] = field(default_factory=lambda: [Language.ENGLISH])
    formats: List[DocumentFormat] = field(default_factory=lambda: [DocumentFormat.MARKDOWN])
    quality_level: DocumentationQuality = DocumentationQuality.STANDARD
    include_code_examples: bool = True
    include_diagrams: bool = True
    auto_generate_toc: bool = True
    update_existing: bool = True
    custom_templates: Dict[str, str] = field(default_factory=dict)
    style_preferences: Dict[str, Any] = field(default_factory=dict)


class CodeAnalyzer:
    """コード解析エンジン"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def analyze_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """プロジェクト構造解析"""
        structure = {
            'project_name': project_path.name,
            'root_path': str(project_path),
            'modules': [],
            'classes': [],
            'functions': [],
            'apis': [],
            'dependencies': [],
            'file_structure': {},
            'statistics': {}
        }
        
        try:
            # ファイル構造解析
            structure['file_structure'] = await self._analyze_file_structure(project_path)
            
            # Python モジュール解析
            if await self._is_python_project(project_path):
                structure.update(await self._analyze_python_project(project_path))
            
            # JavaScript/TypeScript プロジェクト解析
            if await self._is_js_project(project_path):
                structure.update(await self._analyze_js_project(project_path))
            
            # 依存関係解析
            structure['dependencies'] = await self._analyze_dependencies(project_path)
            
            # 統計情報計算
            structure['statistics'] = await self._calculate_statistics(project_path)
            
        except Exception as e:
            self.logger.error(f"Project structure analysis failed: {e}")
        
        return structure
    
    async def _analyze_file_structure(self, project_path: Path) -> Dict[str, Any]:
        """ファイル構造解析"""
        structure = {}
        
        try:
            for item in project_path.rglob("*"):
                if item.is_file() and not self._should_ignore_file(item):
                    rel_path = item.relative_to(project_path)
                    parts = rel_path.parts
                    
                    current = structure
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    
                    # ファイル情報
                    current[parts[-1]] = {
                        'type': 'file',
                        'size': item.stat().st_size,
                        'extension': item.suffix,
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    }
        
        except Exception as e:
            self.logger.error(f"File structure analysis failed: {e}")
        
        return structure
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """ファイルを無視すべきかチェック"""
        ignore_patterns = [
            '.git', '__pycache__', '*.pyc', '.DS_Store',
            'node_modules', '.env', '*.log', 'venv', '.venv'
        ]
        
        for pattern in ignore_patterns:
            if pattern.startswith('*.'):
                if file_path.name.endswith(pattern[1:]):
                    return True
            else:
                if pattern in str(file_path):
                    return True
        
        return False
    
    async def _is_python_project(self, project_path: Path) -> bool:
        """Pythonプロジェクトかチェック"""
        python_indicators = ['setup.py', 'pyproject.toml', 'requirements.txt', 'Pipfile']
        return any((project_path / indicator).exists() for indicator in python_indicators)
    
    async def _is_js_project(self, project_path: Path) -> bool:
        """JavaScript/TypeScriptプロジェクトかチェック"""
        js_indicators = ['package.json', 'tsconfig.json', 'webpack.config.js']
        return any((project_path / indicator).exists() for indicator in js_indicators)
    
    async def _analyze_python_project(self, project_path: Path) -> Dict[str, Any]:
        """Pythonプロジェクト詳細解析"""
        analysis = {
            'modules': [],
            'classes': [],
            'functions': [],
            'apis': []
        }
        
        python_files = list(project_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                file_analysis = await self._analyze_python_file(py_file, tree)
                
                analysis['modules'].append({
                    'name': py_file.stem,
                    'path': str(py_file.relative_to(project_path)),
                    **file_analysis
                })
                
                analysis['classes'].extend(file_analysis['classes'])
                analysis['functions'].extend(file_analysis['functions'])
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze Python file {py_file}: {e}")
        
        return analysis
    
    async def _analyze_python_file(self, file_path: Path, tree: ast.AST) -> Dict[str, Any]:
        """個別Pythonファイル解析"""
        analysis = {
            'classes': [],
            'functions': [],
            'imports': [],
            'constants': [],
            'docstring': ast.get_docstring(tree) or ""
        }
        
        class PythonAnalyzer(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node) or "",
                    'methods': [],
                    'base_classes': [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else [],
                    'decorators': [ast.unparse(dec) for dec in node.decorator_list] if hasattr(ast, 'unparse') else []
                }
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info['methods'].append({
                            'name': item.name,
                            'line': item.lineno,
                            'docstring': ast.get_docstring(item) or "",
                            'args': [arg.arg for arg in item.args.args],
                            'is_property': any(
                                hasattr(dec, 'id') and dec.id == 'property' 
                                for dec in item.decorator_list
                            )
                        })
                
                analysis['classes'].append(class_info)
                self.generic_visit(node)
            
            def visit_FunctionDef(self, node):
                # クラス外の関数のみ
                if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                    function_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node) or "",
                        'args': [arg.arg for arg in node.args.args],
                        'returns': ast.unparse(node.returns) if node.returns and hasattr(ast, 'unparse') else None,
                        'is_async': isinstance(node, ast.AsyncFunctionDef),
                        'decorators': [ast.unparse(dec) for dec in node.decorator_list] if hasattr(ast, 'unparse') else []
                    }
                    analysis['functions'].append(function_info)
                
                self.generic_visit(node)
            
            def visit_Import(self, node):
                for alias in node.names:
                    analysis['imports'].append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            
            def visit_ImportFrom(self, node):
                for alias in node.names:
                    analysis['imports'].append({
                        'from': node.module,
                        'import': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
        
        analyzer = PythonAnalyzer()
        analyzer.visit(tree)
        
        return analysis
    
    async def _analyze_js_project(self, project_path: Path) -> Dict[str, Any]:
        """JavaScript/TypeScriptプロジェクト解析"""
        # 簡易実装 - 実際はより詳細な解析が必要
        analysis = {'js_analysis': 'pending_implementation'}
        return analysis
    
    async def _analyze_dependencies(self, project_path: Path) -> List[Dict[str, Any]]:
        """依存関係解析"""
        dependencies = []
        
        # Python dependencies
        requirements_files = ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile']
        for req_file in requirements_files:
            req_path = project_path / req_file
            if req_path.exists():
                deps = await self._parse_python_dependencies(req_path)
                dependencies.extend(deps)
        
        # JavaScript dependencies
        package_json = project_path / 'package.json'
        if package_json.exists():
            deps = await self._parse_js_dependencies(package_json)
            dependencies.extend(deps)
        
        return dependencies
    
    async def _parse_python_dependencies(self, req_file: Path) -> List[Dict[str, Any]]:
        """Python依存関係解析"""
        dependencies = []
        
        try:
            if req_file.name == 'requirements.txt':
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dep_match = re.match(r'^([a-zA-Z0-9_-]+)([>=<~!]*.*)?', line)
                            if dep_match:
                                dependencies.append({
                                    'name': dep_match.group(1),
                                    'version': dep_match.group(2) or '',
                                    'type': 'python',
                                    'file': req_file.name
                                })
            
            elif req_file.name == 'pyproject.toml':
                import toml
                with open(req_file, 'r') as f:
                    data = toml.load(f)
                    
                project_deps = data.get('project', {}).get('dependencies', [])
                for dep in project_deps:
                    dep_match = re.match(r'^([a-zA-Z0-9_-]+)([>=<~!]*.*)?', dep)
                    if dep_match:
                        dependencies.append({
                            'name': dep_match.group(1),
                            'version': dep_match.group(2) or '',
                            'type': 'python',
                            'file': req_file.name
                        })
        
        except Exception as e:
            self.logger.warning(f"Failed to parse Python dependencies from {req_file}: {e}")
        
        return dependencies
    
    async def _parse_js_dependencies(self, package_json: Path) -> List[Dict[str, Any]]:
        """JavaScript依存関係解析"""
        dependencies = []
        
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
            
            for dep_type in ['dependencies', 'devDependencies']:
                deps = data.get(dep_type, {})
                for name, version in deps.items():
                    dependencies.append({
                        'name': name,
                        'version': version,
                        'type': 'javascript',
                        'category': dep_type,
                        'file': package_json.name
                    })
        
        except Exception as e:
            self.logger.warning(f"Failed to parse JavaScript dependencies: {e}")
        
        return dependencies
    
    async def _calculate_statistics(self, project_path: Path) -> Dict[str, Any]:
        """統計情報計算"""
        stats = {
            'total_files': 0,
            'total_lines': 0,
            'file_types': {},
            'largest_files': [],
            'language_distribution': {}
        }
        
        try:
            file_sizes = []
            
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    stats['total_files'] += 1
                    
                    # ファイルサイズ
                    size = file_path.stat().st_size
                    file_sizes.append((str(file_path.relative_to(project_path)), size))
                    
                    # 拡張子別統計
                    ext = file_path.suffix or 'no_extension'
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                    
                    # 行数カウント（テキストファイルのみ）
                    if self._is_text_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                                stats['total_lines'] += lines
                        except:
                            pass
            
            # 最大ファイル
            stats['largest_files'] = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]
            
        except Exception as e:
            self.logger.error(f"Statistics calculation failed: {e}")
        
        return stats
    
    def _is_text_file(self, file_path: Path) -> bool:
        """テキストファイルかチェック"""
        text_extensions = {'.py', '.js', '.ts', '.md', '.txt', '.yml', '.yaml', '.json', '.xml', '.html', '.css', '.sql'}
        return file_path.suffix.lower() in text_extensions


class DocumentGenerator:
    """ドキュメント生成エンジン"""
    
    def __init__(self, config: DocumentationConfig):
        self.config = config
        self.templates: Dict[DocumentType, DocumentTemplate] = {}
        self.logger = logging.getLogger(__name__)
        self._load_templates()
    
    def _load_templates(self):
        """テンプレート読み込み"""
        # API Reference テンプレート
        api_template = DocumentTemplate(
            name="API Reference",
            document_type=DocumentType.API_REFERENCE,
            sections=["overview", "authentication", "endpoints", "examples", "errors"],
            required_sections={"overview", "endpoints"},
            optional_sections={"authentication", "examples", "errors"},
            frontmatter_template={
                "title": "API Reference",
                "description": "Complete API documentation",
                "version": "1.0.0"
            }
        )
        
        # User Guide テンプレート
        user_guide_template = DocumentTemplate(
            name="User Guide",
            document_type=DocumentType.USER_GUIDE,
            sections=["introduction", "installation", "quick_start", "features", "faq"],
            required_sections={"introduction", "installation"},
            optional_sections={"quick_start", "features", "faq"},
            frontmatter_template={
                "title": "User Guide",
                "description": "Complete user documentation"
            }
        )
        
        # README テンプレート
        readme_template = DocumentTemplate(
            name="README",
            document_type=DocumentType.README,
            sections=["title", "description", "installation", "usage", "contributing", "license"],
            required_sections={"title", "description", "installation"},
            optional_sections={"usage", "contributing", "license"},
            frontmatter_template={}
        )
        
        self.templates = {
            DocumentType.API_REFERENCE: api_template,
            DocumentType.USER_GUIDE: user_guide_template,
            DocumentType.README: readme_template
        }
    
    async def generate_documentation(
        self,
        project_structure: Dict[str, Any],
        document_types: List[DocumentType] = None
    ) -> Dict[DocumentType, Dict[Language, DocumentSection]]:
        """ドキュメント生成"""
        if document_types is None:
            document_types = [DocumentType.API_REFERENCE, DocumentType.USER_GUIDE]
        
        generated_docs = {}
        
        for doc_type in document_types:
            if doc_type in self.templates:
                template = self.templates[doc_type]
                
                # 各言語でドキュメント生成
                language_docs = {}
                for language in self.config.languages:
                    doc_section = await self._generate_document_for_language(
                        doc_type, template, project_structure, language
                    )
                    language_docs[language] = doc_section
                
                generated_docs[doc_type] = language_docs
        
        return generated_docs
    
    async def _generate_document_for_language(
        self,
        doc_type: DocumentType,
        template: DocumentTemplate,
        project_structure: Dict[str, Any],
        language: Language
    ) -> DocumentSection:
        """特定言語でのドキュメント生成"""
        
        # メインセクション作成
        main_section = DocumentSection(
            id=f"{doc_type.value}_{language.value}",
            title=await self._get_localized_title(doc_type, language),
            content="",
            language=language
        )
        
        # セクション別コンテンツ生成
        for i, section_name in enumerate(template.sections):
            section_content = await self._generate_section_content(
                section_name, doc_type, project_structure, language
            )
            
            if section_content:
                subsection = DocumentSection(
                    id=f"{section_name}_{language.value}",
                    title=await self._get_localized_section_title(section_name, language),
                    content=section_content,
                    level=2,
                    order=i,
                    language=language
                )
                main_section.subsections.append(subsection)
        
        return main_section
    
    async def _get_localized_title(self, doc_type: DocumentType, language: Language) -> str:
        """ローカライズされたタイトル取得"""
        titles = {
            DocumentType.API_REFERENCE: {
                Language.ENGLISH: "API Reference",
                Language.JAPANESE: "API リファレンス",
                Language.CHINESE: "API 参考",
                Language.KOREAN: "API 참조"
            },
            DocumentType.USER_GUIDE: {
                Language.ENGLISH: "User Guide",
                Language.JAPANESE: "ユーザーガイド",
                Language.CHINESE: "用户指南",
                Language.KOREAN: "사용 가이드"
            },
            DocumentType.README: {
                Language.ENGLISH: "README",
                Language.JAPANESE: "README",
                Language.CHINESE: "自述文件",
                Language.KOREAN: "리드미"
            }
        }
        
        return titles.get(doc_type, {}).get(language, doc_type.value.replace('_', ' ').title())
    
    async def _get_localized_section_title(self, section_name: str, language: Language) -> str:
        """ローカライズされたセクションタイトル取得"""
        section_titles = {
            "overview": {
                Language.ENGLISH: "Overview",
                Language.JAPANESE: "概要",
                Language.CHINESE: "概述",
                Language.KOREAN: "개요"
            },
            "installation": {
                Language.ENGLISH: "Installation",
                Language.JAPANESE: "インストール",
                Language.CHINESE: "安装",
                Language.KOREAN: "설치"
            },
            "usage": {
                Language.ENGLISH: "Usage",
                Language.JAPANESE: "使用方法",
                Language.CHINESE: "使用方法",
                Language.KOREAN: "사용법"
            },
            "examples": {
                Language.ENGLISH: "Examples",
                Language.JAPANESE: "例",
                Language.CHINESE: "示例",
                Language.KOREAN: "예제"
            },
            "authentication": {
                Language.ENGLISH: "Authentication",
                Language.JAPANESE: "認証",
                Language.CHINESE: "认证",
                Language.KOREAN: "인증"
            },
            "endpoints": {
                Language.ENGLISH: "API Endpoints",
                Language.JAPANESE: "API エンドポイント",
                Language.CHINESE: "API 端点",
                Language.KOREAN: "API 엔드포인트"
            }
        }
        
        return section_titles.get(section_name, {}).get(
            language, 
            section_name.replace('_', ' ').title()
        )
    
    async def _generate_section_content(
        self,
        section_name: str,
        doc_type: DocumentType,
        project_structure: Dict[str, Any],
        language: Language
    ) -> str:
        """セクションコンテンツ生成"""
        
        if section_name == "overview":
            return await self._generate_overview_content(project_structure, language)
        
        elif section_name == "installation":
            return await self._generate_installation_content(project_structure, language)
        
        elif section_name == "endpoints" and doc_type == DocumentType.API_REFERENCE:
            return await self._generate_api_endpoints_content(project_structure, language)
        
        elif section_name == "examples":
            return await self._generate_examples_content(project_structure, language)
        
        elif section_name == "usage":
            return await self._generate_usage_content(project_structure, language)
        
        elif section_name == "authentication":
            return await self._generate_authentication_content(project_structure, language)
        
        else:
            # デフォルトコンテンツ
            return await self._generate_default_section_content(section_name, language)
    
    async def _generate_overview_content(self, project_structure: Dict[str, Any], language: Language) -> str:
        """概要セクション生成"""
        project_name = project_structure.get('project_name', 'Project')
        
        if language == Language.JAPANESE:
            return f"""
{project_name} は、高品質なソフトウェア開発を支援するための包括的なツールセットです。

## 主な機能

- **自動化された品質管理**: コード品質の継続的な監視と改善提案
- **マルチエージェント協調**: 複数のAIエージェントによる効率的なタスク実行
- **リアルタイム監視**: システムパフォーマンスとセキュリティの常時監視
- **統合開発環境**: 主要な開発ツールとの完全統合

## アーキテクチャ

{project_name} は、モジュラー設計により高い拡張性とメンテナンス性を実現しています。
各コンポーネントは独立して動作し、必要に応じて組み合わせて使用できます。

## システム要件

- Python 3.9 以上
- 最小メモリ: 4GB RAM
- 推奨メモリ: 8GB RAM 以上
"""
        
        else:  # English
            return f"""
{project_name} is a comprehensive toolkit designed to support high-quality software development.

## Key Features

- **Automated Quality Management**: Continuous code quality monitoring and improvement suggestions
- **Multi-Agent Orchestration**: Efficient task execution through multiple AI agents
- **Real-time Monitoring**: Constant monitoring of system performance and security
- **Integrated Development Environment**: Complete integration with major development tools

## Architecture

{project_name} achieves high extensibility and maintainability through modular design.
Each component operates independently and can be combined as needed.

## System Requirements

- Python 3.9 or higher
- Minimum Memory: 4GB RAM  
- Recommended Memory: 8GB RAM or more
"""
    
    async def _generate_installation_content(self, project_structure: Dict[str, Any], language: Language) -> str:
        """インストールセクション生成"""
        project_name = project_structure.get('project_name', 'project')
        
        # Python プロジェクトかチェック
        has_requirements = any(
            'requirements.txt' in str(dep.get('file', ''))
            for dep in project_structure.get('dependencies', [])
        )
        has_setup_py = 'setup.py' in str(project_structure.get('file_structure', {}))
        
        if language == Language.JAPANESE:
            content = f"""
## 前提条件

- Python 3.9 以上
- pip パッケージマネージャー
- Git (開発版を使用する場合)

## インストール方法

### PyPI からのインストール (推奨)

```bash
pip install {project_name}
```

### ソースからのインストール

```bash
# リポジトリのクローン
git clone https://github.com/your-org/{project_name}.git
cd {project_name}

# 仮想環境の作成 (推奨)
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
"""
            
            if has_requirements:
                content += """
# 依存関係のインストール
pip install -r requirements.txt
"""
            
            if has_setup_py:
                content += """
# パッケージのインストール
pip install -e .
```
"""
            
            content += """
## インストール確認

```bash
python -c "import {project_name}; print('{project_name} successfully installed!')"
```
""".format(project_name=project_name)
        
        else:  # English
            content = f"""
## Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (if using development version)

## Installation

### Install from PyPI (Recommended)

```bash
pip install {project_name}
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/{project_name}.git
cd {project_name}

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
"""
            
            if has_requirements:
                content += """
# Install dependencies
pip install -r requirements.txt
"""
            
            if has_setup_py:
                content += """
# Install package
pip install -e .
```
"""
            
            content += """
## Verify Installation

```bash
python -c "import {project_name}; print('{project_name} successfully installed!')"
```
""".format(project_name=project_name)
        
        return content
    
    async def _generate_api_endpoints_content(self, project_structure: Dict[str, Any], language: Language) -> str:
        """API エンドポイント生成"""
        functions = project_structure.get('functions', [])
        classes = project_structure.get('classes', [])
        
        if language == Language.JAPANESE:
            content = "## 利用可能な API\n\n"
            
            # 関数 API
            if functions:
                content += "### 関数 API\n\n"
                for func in functions[:10]:  # 最初の10個
                    content += f"#### `{func['name']}()`\n\n"
                    if func.get('docstring'):
                        content += f"{func['docstring']}\n\n"
                    
                    if func.get('args'):
                        content += "**パラメータ:**\n"
                        for arg in func['args']:
                            content += f"- `{arg}`: パラメータの説明\n"
                        content += "\n"
                    
                    content += "**例:**\n```python\n"
                    content += f"result = {func['name']}()\n"
                    content += "```\n\n"
            
            # クラス API
            if classes:
                content += "### クラス API\n\n"
                for cls in classes[:5]:  # 最初の5個
                    content += f"#### `{cls['name']}`\n\n"
                    if cls.get('docstring'):
                        content += f"{cls['docstring']}\n\n"
                    
                    if cls.get('methods'):
                        content += "**メソッド:**\n"
                        for method in cls['methods'][:5]:
                            content += f"- `{method['name']}()`: "
                            if method.get('docstring'):
                                content += method['docstring'].split('.')[0]
                            content += "\n"
                        content += "\n"
        
        else:  # English
            content = "## Available APIs\n\n"
            
            # Function APIs
            if functions:
                content += "### Function APIs\n\n"
                for func in functions[:10]:  # First 10
                    content += f"#### `{func['name']}()`\n\n"
                    if func.get('docstring'):
                        content += f"{func['docstring']}\n\n"
                    
                    if func.get('args'):
                        content += "**Parameters:**\n"
                        for arg in func['args']:
                            content += f"- `{arg}`: Parameter description\n"
                        content += "\n"
                    
                    content += "**Example:**\n```python\n"
                    content += f"result = {func['name']}()\n"
                    content += "```\n\n"
            
            # Class APIs
            if classes:
                content += "### Class APIs\n\n"
                for cls in classes[:5]:  # First 5
                    content += f"#### `{cls['name']}`\n\n"
                    if cls.get('docstring'):
                        content += f"{cls['docstring']}\n\n"
                    
                    if cls.get('methods'):
                        content += "**Methods:**\n"
                        for method in cls['methods'][:5]:
                            content += f"- `{method['name']}()`: "
                            if method.get('docstring'):
                                content += method['docstring'].split('.')[0]
                            content += "\n"
                        content += "\n"
        
        return content or "No API endpoints found."
    
    async def _generate_examples_content(self, project_structure: Dict[str, Any], language: Language) -> str:
        """使用例生成"""
        project_name = project_structure.get('project_name', 'project')
        main_classes = project_structure.get('classes', [])[:3]
        main_functions = project_structure.get('functions', [])[:3]
        
        if language == Language.JAPANESE:
            content = f"""
## 基本的な使用例

### インポート

```python
import {project_name}
from {project_name} import main_module
```

### 基本的な初期化

```python
# 基本設定で初期化
config = {project_name}.Config()
system = {project_name}.System(config)
```
"""
            
            if main_classes:
                content += "\n### クラスの使用例\n\n"
                for cls in main_classes:
                    content += f"```python\n# {cls['name']} の使用例\n"
                    content += f"{cls['name'].lower()} = {project_name}.{cls['name']}()\n"
                    if cls.get('methods'):
                        method = cls['methods'][0]
                        content += f"result = {cls['name'].lower()}.{method['name']}()\n"
                    content += "```\n\n"
            
            if main_functions:
                content += "\n### 関数の使用例\n\n"
                for func in main_functions:
                    content += f"```python\n# {func['name']} の使用例\n"
                    args_str = ", ".join(f"'{arg}'" if isinstance(arg, str) else str(arg) for arg in func.get('args', [])[:2])
                    content += f"result = {project_name}.{func['name']}({args_str})\n"
                    content += "print(result)\n```\n\n"
        
        else:  # English
            content = f"""
## Basic Usage Examples

### Import

```python
import {project_name}
from {project_name} import main_module
```

### Basic Initialization

```python
# Initialize with basic configuration
config = {project_name}.Config()
system = {project_name}.System(config)
```
"""
            
            if main_classes:
                content += "\n### Class Usage Examples\n\n"
                for cls in main_classes:
                    content += f"```python\n# {cls['name']} usage example\n"
                    content += f"{cls['name'].lower()} = {project_name}.{cls['name']}()\n"
                    if cls.get('methods'):
                        method = cls['methods'][0]
                        content += f"result = {cls['name'].lower()}.{method['name']}()\n"
                    content += "```\n\n"
            
            if main_functions:
                content += "\n### Function Usage Examples\n\n"
                for func in main_functions:
                    content += f"```python\n# {func['name']} usage example\n"
                    args_str = ", ".join(f"'{arg}'" if isinstance(arg, str) else str(arg) for arg in func.get('args', [])[:2])
                    content += f"result = {project_name}.{func['name']}({args_str})\n"
                    content += "print(result)\n```\n\n"
        
        return content
    
    async def _generate_usage_content(self, project_structure: Dict[str, Any], language: Language) -> str:
        """使用方法生成"""
        if language == Language.JAPANESE:
            return """
## 基本的な使用方法

### ステップ 1: 初期設定

システムを使用する前に、必要な設定を行います。

```python
from ultimate_shunsuke_ecosystem import CommandTower

# Command Tower の初期化
tower = await CommandTower.get_instance()
```

### ステップ 2: タスクの実行

```python
# ユーザーの意図を Command Tower に送信
result = await tower.execute_command_sequence(
    "プロジェクトの品質分析を実行し、改善提案を生成してください"
)

print(f"実行結果: {result}")
```

### ステップ 3: 結果の確認

```python
# 品質レポートの確認
if result['status'] == 'completed':
    quality_score = result['quality_metrics']['overall_score']
    print(f"品質スコア: {quality_score}")
    
    # 改善提案の確認
    suggestions = result.get('suggestions', [])
    print(f"改善提案数: {len(suggestions)}")
```
"""
        
        else:  # English
            return """
## Basic Usage

### Step 1: Initial Setup

Configure the system before use.

```python
from ultimate_shunsuke_ecosystem import CommandTower

# Initialize Command Tower
tower = await CommandTower.get_instance()
```

### Step 2: Execute Tasks

```python
# Send user intent to Command Tower
result = await tower.execute_command_sequence(
    "Please analyze project quality and generate improvement suggestions"
)

print(f"Execution result: {result}")
```

### Step 3: Review Results

```python
# Check quality report
if result['status'] == 'completed':
    quality_score = result['quality_metrics']['overall_score']
    print(f"Quality score: {quality_score}")
    
    # Check improvement suggestions
    suggestions = result.get('suggestions', [])
    print(f"Number of suggestions: {len(suggestions)}")
```
"""
    
    async def _generate_authentication_content(self, project_structure: Dict[str, Any], language: Language) -> str:
        """認証セクション生成"""
        if language == Language.JAPANESE:
            return """
## 認証設定

### API キーの設定

外部サービスとの統合には API キーが必要です。

```bash
# 環境変数として設定
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GITHUB_TOKEN="your-github-token"
```

### 設定ファイル

`.env` ファイルを使用した設定も可能です：

```env
# .env ファイル
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GITHUB_TOKEN=your-github-token
```

### プログラムでの設定

```python
import os
from ultimate_shunsuke_ecosystem import Config

# 設定オブジェクトの作成
config = Config()
config.openai_api_key = os.getenv('OPENAI_API_KEY')
config.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
```
"""
        
        else:  # English
            return """
## Authentication Setup

### API Key Configuration

API keys are required for external service integrations.

```bash
# Set as environment variables
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GITHUB_TOKEN="your-github-token"
```

### Configuration File

You can also use a `.env` file:

```env
# .env file
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GITHUB_TOKEN=your-github-token
```

### Programmatic Configuration

```python
import os
from ultimate_shunsuke_ecosystem import Config

# Create configuration object
config = Config()
config.openai_api_key = os.getenv('OPENAI_API_KEY')
config.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
```
"""
    
    async def _generate_default_section_content(self, section_name: str, language: Language) -> str:
        """デフォルトセクションコンテンツ生成"""
        if language == Language.JAPANESE:
            return f"{section_name.replace('_', ' ').title()} セクションの内容をここに記述します。"
        else:
            return f"Content for {section_name.replace('_', ' ').title()} section goes here."


class DocumentationSynthesizer:
    """
    ドキュメント統合システム
    
    主要機能:
    1. プロジェクト解析からドキュメント自動生成
    2. 多言語対応ドキュメント作成
    3. 品質保証とレビュー機能
    4. テンプレート管理システム
    5. 出力フォーマット変換
    """
    
    def __init__(self, config: DocumentationConfig):
        """初期化"""
        self.config = config
        self.code_analyzer = CodeAnalyzer({})
        self.document_generator = DocumentGenerator(config)
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 通信プロトコル
        self.communication_protocol: Optional[CommunicationProtocol] = None
        
        # 多言語対応システム
        self.multilingual_manager: Optional[MultilingualManager] = None
        self.template_manager: Optional[MultilingualTemplateManager] = None
        
        # 出力統計
        self.generation_stats = {
            'documents_generated': 0,
            'languages_processed': 0,
            'total_sections': 0,
            'generation_time': 0.0,
            'translations_performed': 0,
            'cultural_adaptations': 0
        }
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'documentation-synthesizer.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """ドキュメント統合システム初期化"""
        try:
            self.logger.info("Documentation Synthesizer initialization started")
            
            # 出力ディレクトリ作成
            self.config.output_path.mkdir(parents=True, exist_ok=True)
            
            # 通信プロトコル初期化
            self.communication_protocol = CommunicationProtocol(
                "documentation_synthesizer",
                {}
            )
            await self.communication_protocol.initialize()
            
            # 多言語対応システム初期化
            self.multilingual_manager = await create_multilingual_manager()
            self.template_manager = await create_multilingual_template_manager()
            
            self.logger.info("Documentation Synthesizer initialization completed")
            
        except Exception as e:
            self.logger.error(f"Documentation Synthesizer initialization failed: {e}")
            raise
    
    async def synthesize_complete_documentation(
        self,
        document_types: List[DocumentType] = None
    ) -> Dict[str, Any]:
        """完全なドキュメント統合生成"""
        start_time = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Starting complete documentation synthesis for: {self.config.project_path}")
            
            # Step 1: プロジェクト解析
            self.logger.info("Step 1: Analyzing project structure")
            project_structure = await self.code_analyzer.analyze_project_structure(self.config.project_path)
            
            # Step 2: ドキュメント生成
            self.logger.info("Step 2: Generating documentation")
            if document_types is None:
                document_types = [DocumentType.README, DocumentType.API_REFERENCE, DocumentType.USER_GUIDE]
            
            generated_docs = await self.document_generator.generate_documentation(
                project_structure, document_types
            )
            
            # Step 3: 多言語ドキュメント生成
            self.logger.info("Step 3: Generating multilingual documentation")
            multilingual_docs = await self._generate_multilingual_documentation(generated_docs, project_structure)
            
            # Step 4: ファイル出力
            self.logger.info("Step 4: Writing documentation files")
            output_files = await self._write_multilingual_documentation_files(multilingual_docs)
            
            # Step 5: 統計更新
            end_time = datetime.now(timezone.utc)
            generation_time = (end_time - start_time).total_seconds()
            
            translation_stats = await self.multilingual_manager.get_translation_quality_report() if self.multilingual_manager else {}
            
            self.generation_stats.update({
                'documents_generated': len(output_files),
                'languages_processed': len(self.config.languages),
                'total_sections': sum(
                    len(lang_docs) 
                    for doc_type_docs in generated_docs.values() 
                    for lang_docs in doc_type_docs.values()
                ),
                'generation_time': generation_time,
                'translations_performed': translation_stats.get('total_translations', 0),
                'cultural_adaptations': translation_stats.get('cultural_adaptations', 0)
            })
            
            # Step 6: 品質チェック
            quality_report = await self._perform_quality_check(output_files)
            
            result = {
                'status': 'completed',
                'project_path': str(self.config.project_path),
                'output_path': str(self.config.output_path),
                'generated_files': output_files,
                'project_structure': project_structure,
                'generation_stats': self.generation_stats.copy(),
                'quality_report': quality_report,
                'execution_time': generation_time
            }
            
            self.logger.info(f"Documentation synthesis completed successfully in {generation_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Documentation synthesis failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'project_path': str(self.config.project_path)
            }
    
    async def _write_documentation_files(
        self,
        generated_docs: Dict[DocumentType, Dict[Language, DocumentSection]]
    ) -> List[str]:
        """ドキュメントファイル書き込み"""
        output_files = []
        
        for doc_type, language_docs in generated_docs.items():
            for language, doc_section in language_docs.items():
                
                # ファイル名生成
                filename = await self._generate_filename(doc_type, language)
                file_path = self.config.output_path / filename
                
                # Markdown コンテンツ生成
                markdown_content = await self._generate_markdown_file(doc_section, doc_type, language)
                
                # ファイル書き込み
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                output_files.append(str(file_path))
                self.logger.info(f"Generated documentation: {file_path}")
        
        return output_files
    
    async def _generate_filename(self, doc_type: DocumentType, language: Language) -> str:
        """ファイル名生成"""
        type_names = {
            DocumentType.README: "README",
            DocumentType.API_REFERENCE: "API_Reference",
            DocumentType.USER_GUIDE: "User_Guide",
            DocumentType.DEVELOPER_GUIDE: "Developer_Guide",
            DocumentType.ARCHITECTURE: "Architecture",
            DocumentType.TUTORIAL: "Tutorial"
        }
        
        base_name = type_names.get(doc_type, doc_type.value)
        
        if language == Language.ENGLISH:
            return f"{base_name}.md"
        else:
            return f"{base_name}_{language.value}.md"
    
    async def _generate_markdown_file(
        self,
        doc_section: DocumentSection,
        doc_type: DocumentType,
        language: Language
    ) -> str:
        """Markdown ファイル生成"""
        content = ""
        
        # フロントマター追加（必要に応じて）
        if doc_type != DocumentType.README:
            frontmatter = {
                'title': doc_section.title,
                'language': language.value,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generator': 'Ultimate ShunsukeModel Ecosystem - Documentation Synthesizer'
            }
            
            content += "---\n"
            for key, value in frontmatter.items():
                content += f"{key}: {value}\n"
            content += "---\n\n"
        
        # メインコンテンツ
        content += doc_section.to_markdown()
        
        # フッター追加
        if language == Language.JAPANESE:
            footer = f"\n\n---\n\n*このドキュメントは Ultimate ShunsukeModel Ecosystem によって自動生成されました。*\n\n*生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}*"
        else:
            footer = f"\n\n---\n\n*This documentation was automatically generated by Ultimate ShunsukeModel Ecosystem.*\n\n*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        content += footer
        
        return content
    
    async def _perform_quality_check(self, output_files: List[str]) -> Dict[str, Any]:
        """品質チェック実行"""
        quality_report = {
            'total_files': len(output_files),
            'file_sizes': {},
            'content_analysis': {},
            'issues': [],
            'recommendations': []
        }
        
        for file_path in output_files:
            try:
                file_path_obj = Path(file_path)
                
                # ファイルサイズチェック
                file_size = file_path_obj.stat().st_size
                quality_report['file_sizes'][file_path] = file_size
                
                # コンテンツ解析
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                analysis = {
                    'line_count': len(content.split('\n')),
                    'word_count': len(content.split()),
                    'has_code_examples': '```' in content,
                    'has_links': '[' in content and '](' in content,
                    'header_count': len(re.findall(r'^#+\s', content, re.MULTILINE))
                }
                
                quality_report['content_analysis'][file_path] = analysis
                
                # 品質問題チェック
                if analysis['line_count'] < 10:
                    quality_report['issues'].append(f"Short content in {file_path}")
                
                if not analysis['has_code_examples'] and 'API' in file_path:
                    quality_report['issues'].append(f"Missing code examples in {file_path}")
                
            except Exception as e:
                quality_report['issues'].append(f"Error analyzing {file_path}: {e}")
        
        # 推奨事項生成
        if quality_report['issues']:
            quality_report['recommendations'].append("Review flagged issues and improve content quality")
        
        if len(output_files) > 0:
            avg_size = sum(quality_report['file_sizes'].values()) / len(output_files)
            if avg_size < 1000:  # 1KB未満
                quality_report['recommendations'].append("Consider adding more detailed content")
        
        return quality_report
    
    async def generate_specific_document(
        self,
        doc_type: DocumentType,
        language: Language = Language.ENGLISH
    ) -> Dict[str, Any]:
        """特定ドキュメント生成"""
        try:
            # プロジェクト解析
            project_structure = await self.code_analyzer.analyze_project_structure(self.config.project_path)
            
            # 特定ドキュメント生成
            generated_docs = await self.document_generator.generate_documentation(
                project_structure, [doc_type]
            )
            
            if doc_type in generated_docs and language in generated_docs[doc_type]:
                doc_section = generated_docs[doc_type][language]
                
                # ファイル出力
                filename = await self._generate_filename(doc_type, language)
                file_path = self.config.output_path / filename
                
                markdown_content = await self._generate_markdown_file(doc_section, doc_type, language)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                return {
                    'status': 'completed',
                    'document_type': doc_type.value,
                    'language': language.value,
                    'output_file': str(file_path),
                    'content_preview': markdown_content[:500] + '...' if len(markdown_content) > 500 else markdown_content
                }
            
            else:
                return {
                    'status': 'failed',
                    'error': f"Failed to generate {doc_type.value} document in {language.value}"
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def update_existing_documentation(self, file_path: Path) -> Dict[str, Any]:
        """既存ドキュメント更新"""
        try:
            if not file_path.exists():
                return {'status': 'failed', 'error': 'File does not exist'}
            
            # 既存内容読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # バックアップ作成
            backup_path = file_path.with_suffix(f'.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(file_path, backup_path)
            
            # 新しいコンテンツ生成
            doc_type = self._infer_document_type(file_path.name)
            language = self._infer_language(existing_content)
            
            result = await self.generate_specific_document(doc_type, language)
            
            if result['status'] == 'completed':
                result['backup_created'] = str(backup_path)
                result['original_size'] = len(existing_content)
                
                with open(result['output_file'], 'r', encoding='utf-8') as f:
                    new_content = f.read()
                result['new_size'] = len(new_content)
            
            return result
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def _infer_document_type(self, filename: str) -> DocumentType:
        """ファイル名からドキュメントタイプ推定"""
        filename_lower = filename.lower()
        
        if 'readme' in filename_lower:
            return DocumentType.README
        elif 'api' in filename_lower:
            return DocumentType.API_REFERENCE
        elif 'user' in filename_lower or 'guide' in filename_lower:
            return DocumentType.USER_GUIDE
        elif 'developer' in filename_lower:
            return DocumentType.DEVELOPER_GUIDE
        elif 'architecture' in filename_lower:
            return DocumentType.ARCHITECTURE
        else:
            return DocumentType.README
    
    def _infer_language(self, content: str) -> Language:
        """コンテンツから言語推定"""
        # 簡易的な言語判定
        japanese_chars = len(re.findall(r'[ひらがなカタカナ漢字]', content))
        total_chars = len(content)
        
        if total_chars > 0 and japanese_chars / total_chars > 0.1:
            return Language.JAPANESE
        else:
            return Language.ENGLISH
    
    async def get_generation_statistics(self) -> Dict[str, Any]:
        """生成統計取得"""
        return {
            'current_stats': self.generation_stats.copy(),
            'supported_languages': [lang.value for lang in Language],
            'supported_formats': [fmt.value for fmt in DocumentFormat],
            'supported_document_types': [dt.value for dt in DocumentType],
            'output_directory': str(self.config.output_path),
            'project_path': str(self.config.project_path)
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """ドキュメント統合システム状態取得"""
        return {
            'initialized': self.communication_protocol is not None,
            'project_path': str(self.config.project_path),
            'output_path': str(self.config.output_path),
            'configured_languages': [lang.value for lang in self.config.languages],
            'configured_formats': [fmt.value for fmt in self.config.formats],
            'quality_level': self.config.quality_level.value,
            'generation_stats': self.generation_stats.copy()
        }
    
    async def shutdown(self):
        """ドキュメント統合システムシャットダウン"""
        self.logger.info("Documentation Synthesizer shutdown initiated")
        
        if self.communication_protocol:
            await self.communication_protocol.shutdown()
        
        self.logger.info("Documentation Synthesizer shutdown completed")


if __name__ == "__main__":
    # テスト実行
    async def test_documentation_synthesizer():
        config = DocumentationConfig(
            project_path=Path.cwd(),
            output_path=Path.cwd() / 'generated_docs',
            languages=[Language.ENGLISH, Language.JAPANESE],
            formats=[DocumentFormat.MARKDOWN],
            quality_level=DocumentationQuality.STANDARD
        )
        
        synthesizer = DocumentationSynthesizer(config)
        await synthesizer.initialize()
        
        # 完全ドキュメント生成
        result = await synthesizer.synthesize_complete_documentation()
        print("Documentation synthesis result:")
        print(json.dumps(result, indent=2, default=str))
        
        # 統計確認
        stats = await synthesizer.get_generation_statistics()
        print("Generation statistics:")
        print(json.dumps(stats, indent=2))
        
        await synthesizer.shutdown()
    
    asyncio.run(test_documentation_synthesizer())