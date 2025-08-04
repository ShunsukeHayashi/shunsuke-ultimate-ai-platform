#!/usr/bin/env python3
"""
シュンスケ式多言語テンプレートシステム - Ultimate ShunsukeModel Ecosystem

言語固有のドキュメントテンプレートとフォーマッティングルールを管理。
各言語の文化的慣習と表現スタイルに対応したテンプレート生成。
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
from jinja2 import Environment, FileSystemLoader, Template

from .multilingual_manager import LanguageCode, DocumentStyle


class TemplateType(str, Enum):
    """テンプレートタイプ"""
    README = "readme"
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    TUTORIAL = "tutorial"
    CHANGELOG = "changelog"
    CONTRIBUTING = "contributing"
    LICENSE = "license"
    ARCHITECTURE = "architecture"
    TROUBLESHOOTING = "troubleshooting"
    FAQ = "faq"


@dataclass
class TemplateMetadata:
    """テンプレートメタデータ"""
    template_id: str
    template_type: TemplateType
    language: LanguageCode
    style: DocumentStyle
    version: str = "1.0"
    author: str = "ShunsukeModel Team"
    description: str = ""
    last_updated: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class LocalizationSettings:
    """ローカライゼーション設定"""
    language: LanguageCode
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    number_format: str = "en_US"
    title_case: bool = True
    heading_style: str = "hash"  # hash, underline, numbered
    list_style: str = "dash"     # dash, number, bullet
    code_fence: str = "```"
    quote_style: str = ">"
    emphasis_style: Dict[str, str] = field(default_factory=lambda: {
        "bold": "**",
        "italic": "*",
        "code": "`"
    })
    section_separator: str = "\n\n"
    line_length: int = 80


class LanguageTemplateEngine(ABC):
    """言語固有テンプレートエンジンの基底クラス"""
    
    def __init__(self, language: LanguageCode, localization_settings: LocalizationSettings):
        self.language = language
        self.settings = localization_settings
        self.logger = logging.getLogger(f"{__name__}.{language.value}")
    
    @abstractmethod
    async def generate_readme(self, project_data: Dict[str, Any]) -> str:
        """README生成"""
        pass
    
    @abstractmethod
    async def generate_api_reference(self, api_data: Dict[str, Any]) -> str:
        """API リファレンス生成"""
        pass
    
    @abstractmethod
    async def generate_user_guide(self, guide_data: Dict[str, Any]) -> str:
        """ユーザーガイド生成"""
        pass
    
    @abstractmethod
    async def format_heading(self, text: str, level: int) -> str:
        """見出しフォーマット"""
        pass
    
    @abstractmethod
    async def format_list(self, items: List[str], ordered: bool = False) -> str:
        """リストフォーマット"""
        pass
    
    @abstractmethod
    async def format_code_block(self, code: str, language: str = "") -> str:
        """コードブロックフォーマット"""
        pass


class JapaneseTemplateEngine(LanguageTemplateEngine):
    """日本語テンプレートエンジン"""
    
    async def generate_readme(self, project_data: Dict[str, Any]) -> str:
        """日本語README生成"""
        template_content = """# {project_name}

{description}

## 📋 目次

- [概要](#概要)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [機能](#機能)
- [ライセンス](#ライセンス)

## 📖 概要

{detailed_description}

## 🚀 インストール

### 必要な環境

- Python {python_version} 以上
- {additional_requirements}

### インストール手順

```bash
# リポジトリのクローン
git clone {repository_url}
cd {project_name}

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 依存関係のインストール
pip install -r requirements.txt
```

## 📚 使用方法

### 基本的な使用方法

```python
{basic_usage_example}
```

### 高度な設定

{advanced_configuration}

## ✨ 機能

{features_list}

## 📄 ライセンス

このプロジェクトは {license} ライセンスの下で公開されています。
詳細については [LICENSE](LICENSE) ファイルをご覧ください。

## 🤝 貢献

プロジェクトへの貢献を歓迎します！詳細については [CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。

## 📞 サポート

- GitHub Issues: [問題の報告]({issues_url})
- Email: {contact_email}
- Discord: {discord_url}

---

© {year} {author}. All rights reserved.
"""
        
        # テンプレート変数の設定
        template_vars = {
            "project_name": project_data.get("name", "プロジェクト名"),
            "description": project_data.get("description", "プロジェクトの説明"),
            "detailed_description": project_data.get("detailed_description", "詳細な説明がここに入ります。"),
            "python_version": project_data.get("python_version", "3.9"),
            "additional_requirements": self._format_requirements_ja(project_data.get("requirements", [])),
            "repository_url": project_data.get("repository_url", "https://github.com/user/repo"),
            "basic_usage_example": project_data.get("basic_usage", "# 基本的な使用例\nprint('Hello, World!')"),
            "advanced_configuration": self._format_advanced_config_ja(project_data.get("advanced_config", {})),
            "features_list": self._format_features_ja(project_data.get("features", [])),
            "license": project_data.get("license", "MIT"),
            "issues_url": project_data.get("issues_url", "https://github.com/user/repo/issues"),
            "contact_email": project_data.get("contact_email", "contact@example.com"),
            "discord_url": project_data.get("discord_url", "#"),
            "year": project_data.get("year", "2025"),
            "author": project_data.get("author", "開発者")
        }
        
        return template_content.format(**template_vars)
    
    def _format_requirements_ja(self, requirements: List[str]) -> str:
        """必要環境の日本語フォーマット"""
        if not requirements:
            return "特になし"
        return "\n- ".join([""] + requirements)
    
    def _format_advanced_config_ja(self, config: Dict[str, Any]) -> str:
        """高度な設定の日本語フォーマット"""
        if not config:
            return "設定オプションについては、ドキュメントをご参照ください。"
        
        formatted_config = "以下の設定オプションが利用可能です：\n\n"
        for key, value in config.items():
            formatted_config += f"- **{key}**: {value}\n"
        
        return formatted_config
    
    def _format_features_ja(self, features: List[str]) -> str:
        """機能リストの日本語フォーマット"""
        if not features:
            return "- 基本機能\n- 高度な機能\n- 拡張可能なアーキテクチャ"
        
        return "\n".join([f"- {feature}" for feature in features])
    
    async def generate_api_reference(self, api_data: Dict[str, Any]) -> str:
        """日本語API リファレンス生成"""
        template_content = """# API リファレンス

{api_description}

## 概要

このドキュメントでは、{api_name} の全てのAPIエンドポイントについて説明します。

## 認証

{authentication_info}

## エンドポイント

{endpoints_section}

## エラーハンドリング

{error_handling_section}

## レート制限

{rate_limiting_info}

## 例

{examples_section}
"""
        
        return template_content.format(
            api_description=api_data.get("description", "API の説明"),
            api_name=api_data.get("name", "API"),
            authentication_info=self._format_auth_info_ja(api_data.get("authentication", {})),
            endpoints_section=self._format_endpoints_ja(api_data.get("endpoints", [])),
            error_handling_section=self._format_error_handling_ja(api_data.get("error_handling", {})),
            rate_limiting_info=api_data.get("rate_limiting", "レート制限については、利用規約をご確認ください。"),
            examples_section=self._format_examples_ja(api_data.get("examples", []))
        )
    
    def _format_auth_info_ja(self, auth_info: Dict[str, Any]) -> str:
        """認証情報の日本語フォーマット"""
        if not auth_info:
            return "認証は必要ありません。"
        
        auth_type = auth_info.get("type", "unknown")
        if auth_type == "bearer":
            return "Bearer トークンを使用した認証が必要です。"
        elif auth_type == "api_key":
            return "API キーを使用した認証が必要です。"
        else:
            return f"{auth_type} 認証が必要です。"
    
    def _format_endpoints_ja(self, endpoints: List[Dict[str, Any]]) -> str:
        """エンドポイントの日本語フォーマット"""
        if not endpoints:
            return "エンドポイント情報がありません。"
        
        formatted = ""
        for endpoint in endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "/")
            description = endpoint.get("description", "説明なし")
            
            formatted += f"### {method} {path}\n\n{description}\n\n"
        
        return formatted
    
    def _format_error_handling_ja(self, error_info: Dict[str, Any]) -> str:
        """エラーハンドリングの日本語フォーマット"""
        if not error_info:
            return "標準的なHTTPステータスコードを使用します。"
        
        return "エラー時は適切なHTTPステータスコードとエラーメッセージが返されます。"
    
    def _format_examples_ja(self, examples: List[Dict[str, Any]]) -> str:
        """例の日本語フォーマット"""
        if not examples:
            return "使用例については、個別のエンドポイント説明をご参照ください。"
        
        formatted = ""
        for i, example in enumerate(examples, 1):
            title = example.get("title", f"例 {i}")
            code = example.get("code", "# コード例")
            
            formatted += f"### {title}\n\n```python\n{code}\n```\n\n"
        
        return formatted
    
    async def generate_user_guide(self, guide_data: Dict[str, Any]) -> str:
        """日本語ユーザーガイド生成"""
        template_content = """# ユーザーガイド

{guide_introduction}

## はじめに

{getting_started_section}

## チュートリアル

{tutorial_section}

## よくある質問

{faq_section}

## トラブルシューティング

{troubleshooting_section}

## サポート

ご不明な点がございましたら、以下までお問い合わせください：

- GitHub Issues: {issues_url}
- Email: {support_email}
- Discord: {discord_url}
"""
        
        return template_content.format(
            guide_introduction=guide_data.get("introduction", "このガイドでは、システムの使用方法について説明します。"),
            getting_started_section=self._format_getting_started_ja(guide_data.get("getting_started", {})),
            tutorial_section=self._format_tutorial_ja(guide_data.get("tutorials", [])),
            faq_section=self._format_faq_ja(guide_data.get("faq", [])),
            troubleshooting_section=self._format_troubleshooting_ja(guide_data.get("troubleshooting", [])),
            issues_url=guide_data.get("issues_url", "#"),
            support_email=guide_data.get("support_email", "support@example.com"),
            discord_url=guide_data.get("discord_url", "#")
        )
    
    def _format_getting_started_ja(self, getting_started: Dict[str, Any]) -> str:
        """はじめにセクションの日本語フォーマット"""
        if not getting_started:
            return "システムのセットアップから基本的な使用方法まで、ステップバイステップで説明します。"
        
        return getting_started.get("content", "はじめに関する情報がここに表示されます。")
    
    def _format_tutorial_ja(self, tutorials: List[Dict[str, Any]]) -> str:
        """チュートリアルの日本語フォーマット"""
        if not tutorials:
            return "チュートリアルは準備中です。"
        
        formatted = ""
        for tutorial in tutorials:
            title = tutorial.get("title", "チュートリアル")
            content = tutorial.get("content", "内容")
            
            formatted += f"### {title}\n\n{content}\n\n"
        
        return formatted
    
    def _format_faq_ja(self, faq_items: List[Dict[str, Any]]) -> str:
        """FAQの日本語フォーマット"""
        if not faq_items:
            return "FAQ項目は準備中です。"
        
        formatted = ""
        for item in faq_items:
            question = item.get("question", "質問")
            answer = item.get("answer", "回答")
            
            formatted += f"### Q: {question}\n\n**A:** {answer}\n\n"
        
        return formatted
    
    def _format_troubleshooting_ja(self, troubleshooting_items: List[Dict[str, Any]]) -> str:
        """トラブルシューティングの日本語フォーマット"""
        if not troubleshooting_items:
            return "トラブルシューティング情報は準備中です。"
        
        formatted = ""
        for item in troubleshooting_items:
            problem = item.get("problem", "問題")
            solution = item.get("solution", "解決方法")
            
            formatted += f"### {problem}\n\n{solution}\n\n"
        
        return formatted
    
    async def format_heading(self, text: str, level: int) -> str:
        """日本語見出しフォーマット"""
        if self.settings.heading_style == "hash":
            return "#" * level + " " + text
        elif self.settings.heading_style == "underline":
            if level == 1:
                return f"{text}\n{'=' * len(text)}"
            elif level == 2:
                return f"{text}\n{'-' * len(text)}"
            else:
                return "#" * level + " " + text
        else:
            return "#" * level + " " + text
    
    async def format_list(self, items: List[str], ordered: bool = False) -> str:
        """日本語リストフォーマット"""
        if not items:
            return ""
        
        if ordered:
            return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
        else:
            marker = self.settings.list_style if hasattr(self.settings, 'list_style') else "-"
            return "\n".join([f"{marker} {item}" for item in items])
    
    async def format_code_block(self, code: str, language: str = "") -> str:
        """日本語コードブロックフォーマット"""
        fence = self.settings.code_fence
        return f"{fence}{language}\n{code}\n{fence}"


class EnglishTemplateEngine(LanguageTemplateEngine):
    """英語テンプレートエンジン"""
    
    async def generate_readme(self, project_data: Dict[str, Any]) -> str:
        """英語README生成"""
        template_content = """# {project_name}

{description}

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [License](#license)

## 📖 Overview

{detailed_description}

## 🚀 Installation

### Prerequisites

- Python {python_version} or higher
{additional_requirements}

### Installation Steps

```bash
# Clone the repository
git clone {repository_url}
cd {project_name}

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## 📚 Usage

### Basic Usage

```python
{basic_usage_example}
```

### Advanced Configuration

{advanced_configuration}

## ✨ Features

{features_list}

## 📄 License

This project is licensed under the {license} License.
See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📞 Support

- GitHub Issues: [Report a bug]({issues_url})
- Email: {contact_email}
- Discord: {discord_url}

---

© {year} {author}. All rights reserved.
"""
        
        # テンプレート変数の設定（英語版）
        template_vars = {
            "project_name": project_data.get("name", "Project Name"),
            "description": project_data.get("description", "Project description"),
            "detailed_description": project_data.get("detailed_description", "Detailed description goes here."),
            "python_version": project_data.get("python_version", "3.9"),
            "additional_requirements": self._format_requirements_en(project_data.get("requirements", [])),
            "repository_url": project_data.get("repository_url", "https://github.com/user/repo"),
            "basic_usage_example": project_data.get("basic_usage", "# Basic usage example\nprint('Hello, World!')"),
            "advanced_configuration": self._format_advanced_config_en(project_data.get("advanced_config", {})),
            "features_list": self._format_features_en(project_data.get("features", [])),
            "license": project_data.get("license", "MIT"),
            "issues_url": project_data.get("issues_url", "https://github.com/user/repo/issues"),
            "contact_email": project_data.get("contact_email", "contact@example.com"),
            "discord_url": project_data.get("discord_url", "#"),
            "year": project_data.get("year", "2025"),
            "author": project_data.get("author", "Developer")
        }
        
        return template_content.format(**template_vars)
    
    def _format_requirements_en(self, requirements: List[str]) -> str:
        """英語必要環境フォーマット"""
        if not requirements:
            return ""
        return "\n- ".join([""] + requirements)
    
    def _format_advanced_config_en(self, config: Dict[str, Any]) -> str:
        """英語高度な設定フォーマット"""
        if not config:
            return "See documentation for configuration options."
        
        formatted_config = "The following configuration options are available:\n\n"
        for key, value in config.items():
            formatted_config += f"- **{key}**: {value}\n"
        
        return formatted_config
    
    def _format_features_en(self, features: List[str]) -> str:
        """英語機能リストフォーマット"""
        if not features:
            return "- Core functionality\n- Advanced features\n- Extensible architecture"
        
        return "\n".join([f"- {feature}" for feature in features])
    
    async def generate_api_reference(self, api_data: Dict[str, Any]) -> str:
        """英語API リファレンス生成"""
        # 英語版の実装（省略、構造は日本語版と同様）
        return "# API Reference\n\nAPI documentation content here..."
    
    async def generate_user_guide(self, guide_data: Dict[str, Any]) -> str:
        """英語ユーザーガイド生成"""
        # 英語版の実装（省略、構造は日本語版と同様）
        return "# User Guide\n\nUser guide content here..."
    
    async def format_heading(self, text: str, level: int) -> str:
        """英語見出しフォーマット"""
        return "#" * level + " " + text
    
    async def format_list(self, items: List[str], ordered: bool = False) -> str:
        """英語リストフォーマット"""
        if not items:
            return ""
        
        if ordered:
            return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
        else:
            return "\n".join([f"- {item}" for item in items])
    
    async def format_code_block(self, code: str, language: str = "") -> str:
        """英語コードブロックフォーマット"""
        return f"```{language}\n{code}\n```"


class MultilingualTemplateManager:
    """
    シュンスケ式多言語テンプレート管理システム
    
    各言語に対応したテンプレートエンジンを管理し、
    言語固有のドキュメント生成を統合的に処理。
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        
        # 言語エンジンの初期化
        self.engines: Dict[LanguageCode, LanguageTemplateEngine] = {}
        self._initialize_engines()
        
        # テンプレートメタデータ管理
        self.template_metadata: Dict[str, TemplateMetadata] = {}
        
        # Jinja2環境の設定
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
    
    def _initialize_engines(self) -> None:
        """言語エンジンの初期化"""
        # 日本語設定
        ja_settings = LocalizationSettings(
            language=LanguageCode.JAPANESE,
            date_format="%Y年%m月%d日",
            heading_style="hash",
            list_style="-",
            line_length=80
        )
        
        # 英語設定
        en_settings = LocalizationSettings(
            language=LanguageCode.ENGLISH,
            date_format="%B %d, %Y",
            heading_style="hash",
            list_style="-",
            line_length=80
        )
        
        # エンジンの登録
        self.engines[LanguageCode.JAPANESE] = JapaneseTemplateEngine(
            LanguageCode.JAPANESE, ja_settings
        )
        self.engines[LanguageCode.ENGLISH] = EnglishTemplateEngine(
            LanguageCode.ENGLISH, en_settings
        )
    
    async def generate_document(self, 
                              template_type: TemplateType,
                              language: LanguageCode,
                              data: Dict[str, Any],
                              style: DocumentStyle = DocumentStyle.TECHNICAL) -> str:
        """
        多言語ドキュメントの生成
        
        Args:
            template_type: テンプレートタイプ
            language: ターゲット言語
            data: テンプレートに渡すデータ
            style: ドキュメントスタイル
            
        Returns:
            生成されたドキュメント
        """
        try:
            if language not in self.engines:
                raise ValueError(f"Unsupported language: {language}")
            
            engine = self.engines[language]
            
            # テンプレートタイプに応じた生成
            if template_type == TemplateType.README:
                document = await engine.generate_readme(data)
            elif template_type == TemplateType.API_REFERENCE:
                document = await engine.generate_api_reference(data)
            elif template_type == TemplateType.USER_GUIDE:
                document = await engine.generate_user_guide(data)
            else:
                # カスタムテンプレートの使用
                document = await self._generate_custom_template(
                    template_type, language, data, style
                )
            
            self.logger.info(f"ドキュメント生成完了: {template_type.value} ({language.value})")
            return document
            
        except Exception as e:
            self.logger.error(f"ドキュメント生成エラー: {e}")
            return f"# Error\n\nFailed to generate document: {e}"
    
    async def _generate_custom_template(self,
                                      template_type: TemplateType,
                                      language: LanguageCode,
                                      data: Dict[str, Any],
                                      style: DocumentStyle) -> str:
        """カスタムテンプレートの生成"""
        try:
            template_name = f"{template_type.value}_{language.value}_{style.value}.md"
            
            # テンプレートファイルの存在確認
            if not (self.templates_dir / template_name).exists():
                template_name = f"{template_type.value}_{language.value}.md"
            
            if not (self.templates_dir / template_name).exists():
                template_name = f"{template_type.value}_default.md"
            
            if not (self.templates_dir / template_name).exists():
                return f"# {template_type.value.title()}\n\nTemplate not found: {template_name}"
            
            # Jinja2テンプレートの読み込みと生成
            template = self.jinja_env.get_template(template_name)
            document = template.render(**data)
            
            return document
            
        except Exception as e:
            self.logger.error(f"カスタムテンプレート生成エラー: {e}")
            return f"# Error\n\nCustom template generation failed: {e}"
    
    async def generate_multilingual_docs(self,
                                       template_type: TemplateType,
                                       data: Dict[str, Any],
                                       target_languages: List[LanguageCode],
                                       style: DocumentStyle = DocumentStyle.TECHNICAL) -> Dict[str, str]:
        """
        多言語ドキュメントの一括生成
        
        Args:
            template_type: テンプレートタイプ
            data: テンプレートデータ
            target_languages: ターゲット言語リスト
            style: ドキュメントスタイル
            
        Returns:
            言語コードをキーとする生成ドキュメント辞書
        """
        results = {}
        
        for language in target_languages:
            try:
                document = await self.generate_document(
                    template_type, language, data, style
                )
                results[language.value] = document
                
            except Exception as e:
                self.logger.error(f"多言語生成エラー ({language.value}): {e}")
                results[language.value] = f"# Error\n\nGeneration failed: {e}"
        
        self.logger.info(f"多言語ドキュメント一括生成完了: {len(results)}言語")
        return results
    
    async def create_template_directory_structure(self) -> None:
        """テンプレートディレクトリ構造の作成"""
        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            
            # 基本テンプレートファイルの作成
            template_files = {
                "readme_ja.md": self._get_default_readme_template_ja(),
                "readme_en.md": self._get_default_readme_template_en(),
                "api_reference_ja.md": self._get_default_api_template_ja(),
                "api_reference_en.md": self._get_default_api_template_en(),
            }
            
            for filename, content in template_files.items():
                template_path = self.templates_dir / filename
                if not template_path.exists():
                    async with aiofiles.open(template_path, 'w', encoding='utf-8') as f:
                        await f.write(content)
            
            self.logger.info(f"テンプレートディレクトリ構造を作成: {self.templates_dir}")
            
        except Exception as e:
            self.logger.error(f"テンプレートディレクトリ作成エラー: {e}")
    
    def _get_default_readme_template_ja(self) -> str:
        """デフォルト日本語READMEテンプレート"""
        return """# {{ project_name }}

{{ description }}

## 📋 目次

- [概要](#概要)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [機能](#機能)
- [ライセンス](#ライセンス)

## 📖 概要

{{ detailed_description }}

## 🚀 インストール

```bash
pip install {{ package_name }}
```

## 📚 使用方法

```python
{{ basic_usage }}
```

## ✨ 機能

{% for feature in features %}
- {{ feature }}
{% endfor %}

## 📄 ライセンス

このプロジェクトは {{ license }} ライセンスの下で公開されています。

---

© {{ year }} {{ author }}
"""
    
    def _get_default_readme_template_en(self) -> str:
        """デフォルト英語READMEテンプレート"""
        return """# {{ project_name }}

{{ description }}

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [License](#license)

## 📖 Overview

{{ detailed_description }}

## 🚀 Installation

```bash
pip install {{ package_name }}
```

## 📚 Usage

```python
{{ basic_usage }}
```

## ✨ Features

{% for feature in features %}
- {{ feature }}
{% endfor %}

## 📄 License

This project is licensed under the {{ license }} License.

---

© {{ year }} {{ author }}
"""
    
    def _get_default_api_template_ja(self) -> str:
        """デフォルト日本語APIテンプレート"""
        return """# API リファレンス

{{ api_description }}

## エンドポイント

{% for endpoint in endpoints %}
### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
#### パラメータ

{% for param in endpoint.parameters %}
- **{{ param.name }}** ({{ param.type }}): {{ param.description }}
{% endfor %}
{% endif %}

#### レスポンス例

```json
{{ endpoint.response_example }}
```

{% endfor %}
"""
    
    def _get_default_api_template_en(self) -> str:
        """デフォルト英語APIテンプレート"""
        return """# API Reference

{{ api_description }}

## Endpoints

{% for endpoint in endpoints %}
### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
#### Parameters

{% for param in endpoint.parameters %}
- **{{ param.name }}** ({{ param.type }}): {{ param.description }}
{% endfor %}
{% endif %}

#### Response Example

```json
{{ endpoint.response_example }}
```

{% endfor %}
"""
    
    async def get_supported_template_types(self) -> List[Dict[str, Any]]:
        """サポートテンプレートタイプの取得"""
        return [
            {
                "type": template_type.value,
                "name": template_type.value.replace("_", " ").title(),
                "supported_languages": [lang.value for lang in self.engines.keys()]
            }
            for template_type in TemplateType
        ]
    
    async def get_template_metadata(self, template_id: str) -> Optional[TemplateMetadata]:
        """テンプレートメタデータの取得"""
        return self.template_metadata.get(template_id)


# ファクトリー関数
async def create_multilingual_template_manager(templates_dir: Optional[Path] = None) -> MultilingualTemplateManager:
    """多言語テンプレート管理システムのインスタンス作成"""
    manager = MultilingualTemplateManager(templates_dir)
    await manager.create_template_directory_structure()
    return manager


if __name__ == "__main__":
    # テスト実行
    async def test_multilingual_templates():
        manager = await create_multilingual_template_manager()
        
        # テストデータ
        project_data = {
            "name": "Ultimate ShunsukeModel Ecosystem",
            "description": "次世代AI開発プラットフォーム",
            "detailed_description": "マルチエージェント協調システムを備えた統合AI開発環境",
            "python_version": "3.9",
            "requirements": ["Docker", "Git"],
            "repository_url": "https://github.com/shunsuke-dev/ultimate-shunsuke-ecosystem",
            "basic_usage": "from core.command_tower import CommandTower\ntower = CommandTower()\nresult = await tower.execute_command('analyze_project')",
            "features": ["マルチエージェント協調", "リアルタイム品質監視", "自動ドキュメント生成"],
            "license": "MIT",
            "author": "ShunsukeModel Team",
            "year": "2025"
        }
        
        # 日本語README生成
        ja_readme = await manager.generate_document(
            TemplateType.README, 
            LanguageCode.JAPANESE, 
            project_data
        )
        print("日本語README:")
        print(ja_readme[:300] + "...")
        
        # 英語README生成
        en_readme = await manager.generate_document(
            TemplateType.README,
            LanguageCode.ENGLISH,
            project_data
        )
        print("\n英語README:")
        print(en_readme[:300] + "...")
        
        # 多言語一括生成
        multilingual_docs = await manager.generate_multilingual_docs(
            TemplateType.README,
            project_data,
            [LanguageCode.JAPANESE, LanguageCode.ENGLISH]
        )
        print(f"\n多言語生成完了: {len(multilingual_docs)}言語")
    
    asyncio.run(test_multilingual_templates())