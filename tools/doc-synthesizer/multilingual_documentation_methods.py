#!/usr/bin/env python3
"""
シュンスケ式多言語ドキュメント生成メソッド - Ultimate ShunsukeModel Ecosystem

DocumentationSynthesizerクラスの多言語対応拡張メソッド群
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
from datetime import datetime

from .multilingual_manager import LanguageCode, DocumentStyle, TranslationRequest
from .multilingual_templates import TemplateType


async def _generate_multilingual_documentation(
    self,
    generated_docs: Dict[Any, Dict[Any, Any]],
    project_structure: Dict[str, Any]
) -> Dict[str, Any]:
    """
    多言語ドキュメント生成メソッド
    
    既存のドキュメントを多言語に翻訳し、
    言語固有のテンプレートを適用
    """
    multilingual_docs = {}
    
    try:
        if not self.multilingual_manager or not self.template_manager:
            self.logger.warning("Multilingual systems not initialized, skipping multilingual generation")
            return {'original_docs': generated_docs}
        
        # サポート言語の取得
        supported_languages = await self.multilingual_manager.get_supported_languages()
        target_languages = [LanguageCode(lang['code']) for lang in supported_languages]
        
        self.logger.info(f"Generating multilingual docs for languages: {[lang.value for lang in target_languages]}")
        
        for doc_type, language_docs in generated_docs.items():
            multilingual_docs[doc_type.value] = {}
            
            for source_language, doc_section in language_docs.items():
                # 原文ドキュメントの処理
                doc_content = self._extract_document_content(doc_section)
                
                # 言語検出
                detected_lang, confidence = await self.multilingual_manager.detect_language(doc_content)
                self.logger.debug(f"Detected language: {detected_lang} (confidence: {confidence:.2f})")
                
                # 各ターゲット言語への翻訳・生成
                for target_lang in target_languages:
                    try:
                        if target_lang == detected_lang:
                            # 同じ言語の場合は原文をそのまま使用
                            multilingual_docs[doc_type.value][target_lang.value] = {
                                'content': doc_content,
                                'template_applied': False,
                                'translated': False,
                                'source_language': detected_lang.value
                            }
                        else:
                            # 翻訳＋テンプレート適用
                            localized_doc = await self._generate_localized_document(
                                doc_type, doc_content, detected_lang, target_lang, project_structure
                            )
                            multilingual_docs[doc_type.value][target_lang.value] = localized_doc
                    
                    except Exception as e:
                        self.logger.error(f"Failed to generate {target_lang.value} version of {doc_type.value}: {e}")
                        multilingual_docs[doc_type.value][target_lang.value] = {
                            'content': doc_content,
                            'error': str(e),
                            'fallback': True
                        }
        
        # 統計更新
        total_translations = sum(
            1 for doc_langs in multilingual_docs.values()
            for lang_data in doc_langs.values()
            if lang_data.get('translated', False)
        )
        
        self.generation_stats['translations_performed'] = total_translations
        
        self.logger.info(f"Multilingual documentation generation completed: {total_translations} translations")
        
        return multilingual_docs
        
    except Exception as e:
        self.logger.error(f"Multilingual documentation generation failed: {e}")
        return {'original_docs': generated_docs, 'error': str(e)}


async def _generate_localized_document(
    self,
    doc_type: Any,
    source_content: str,
    source_language: LanguageCode,
    target_language: LanguageCode,
    project_structure: Dict[str, Any]
) -> Dict[str, Any]:
    """
    ローカライズされたドキュメント生成
    
    翻訳 + 言語固有テンプレート適用 + 文化的適応
    """
    try:
        # 1. コンテンツ翻訳
        translation_request = TranslationRequest(
            source_language=source_language,
            target_language=target_language,
            text=source_content,
            style=DocumentStyle.TECHNICAL,
            preserve_formatting=True,
            use_terminology=True
        )
        
        translation_result = await self.multilingual_manager.translate_text(translation_request)
        
        # 2. テンプレートタイプマッピング
        template_type_mapping = {
            'README': TemplateType.README,
            'API_REFERENCE': TemplateType.API_REFERENCE,
            'USER_GUIDE': TemplateType.USER_GUIDE,
            'DEVELOPER_GUIDE': TemplateType.USER_GUIDE,  # Fallback
            'ARCHITECTURE': TemplateType.ARCHITECTURE,
            'TUTORIAL': TemplateType.TUTORIAL
        }
        
        template_type = template_type_mapping.get(
            doc_type.value if hasattr(doc_type, 'value') else str(doc_type),
            TemplateType.README
        )
        
        # 3. プロジェクトデータの準備
        template_data = self._prepare_template_data(project_structure, translation_result)
        
        # 4. 言語固有テンプレート適用
        templated_content = await self.template_manager.generate_document(
            template_type=template_type,
            language=target_language,
            data=template_data,
            style=DocumentStyle.TECHNICAL
        )
        
        return {
            'content': templated_content,
            'translated': True,
            'template_applied': True,
            'source_language': source_language.value,
            'target_language': target_language.value,
            'translation_confidence': translation_result.confidence_score,
            'cultural_adaptations': translation_result.cultural_adaptations,
            'terminology_used': translation_result.terminology_used,
            'template_type': template_type.value
        }
        
    except Exception as e:
        self.logger.error(f"Localized document generation failed: {e}")
        return {
            'content': source_content,
            'error': str(e),
            'fallback': True,
            'source_language': source_language.value,
            'target_language': target_language.value
        }


def _extract_document_content(self, doc_section: Any) -> str:
    """ドキュメントセクションからコンテンツ抽出"""
    try:
        if hasattr(doc_section, 'content'):
            return doc_section.content
        elif hasattr(doc_section, 'sections'):
            # 複数セクションを結合
            content_parts = []
            for section in doc_section.sections:
                if hasattr(section, 'content'):
                    content_parts.append(section.content)
                elif isinstance(section, str):
                    content_parts.append(section)
            return '\n\n'.join(content_parts)
        elif isinstance(doc_section, str):
            return doc_section
        elif isinstance(doc_section, dict):
            return doc_section.get('content', str(doc_section))
        else:
            return str(doc_section)
    except Exception as e:
        self.logger.error(f"Content extraction failed: {e}")
        return str(doc_section)


def _prepare_template_data(self, project_structure: Dict[str, Any], translation_result: Any) -> Dict[str, Any]:
    """テンプレート用データ準備"""
    try:
        # 基本プロジェクト情報
        template_data = {
            'project_name': project_structure.get('project_name', 'Ultimate ShunsukeModel Ecosystem'),
            'description': 'Next-generation AI development platform with multi-agent orchestration',
            'detailed_description': 'A comprehensive AI development ecosystem featuring advanced agent coordination, real-time quality monitoring, and automated documentation generation.',
            'python_version': '3.9',
            'package_name': 'ultimate-shunsuke-ecosystem',
            'repository_url': 'https://github.com/shunsuke-dev/ultimate-shunsuke-ecosystem',
            'issues_url': 'https://github.com/shunsuke-dev/ultimate-shunsuke-ecosystem/issues',
            'license': 'MIT',
            'author': 'ShunsukeModel Team',
            'year': str(datetime.now().year),
            'contact_email': 'team@shunsuke-ecosystem.dev',
            'discord_url': 'https://discord.gg/shunsuke-ecosystem'
        }
        
        # 機能リスト
        template_data['features'] = [
            'Multi-agent orchestration system',
            'Real-time quality monitoring',
            'Automated documentation generation',
            'Performance optimization toolkit',
            'Integrated development environment support',
            'Cloud deployment automation'
        ]
        
        # 必要環境
        template_data['requirements'] = [
            'Docker (for containerized development)',
            'Git (version control)',
            'Node.js 18+ (for some integrations)'
        ]
        
        # 基本使用例
        template_data['basic_usage'] = '''from core.command_tower import CommandTower
from orchestration.coordinator import AgentCoordinator

# Initialize the system
tower = CommandTower()
coordinator = AgentCoordinator()

# Execute a complex task
result = await tower.execute_command_sequence(
    "analyze_and_improve_codebase",
    context={"target_directory": "./src"}
)

print(f"Task completed: {result['status']}")'''
        
        # 高度な設定
        template_data['advanced_config'] = {
            'agent_coordination': 'Configure multi-agent workflows',
            'quality_monitoring': 'Set up real-time quality checks',
            'performance_optimization': 'Enable automatic performance tuning',
            'multilingual_support': 'Configure international documentation'
        }
        
        # API情報（API参考用）
        template_data['api_name'] = 'Ultimate ShunsukeModel Ecosystem API'
        template_data['endpoints'] = [
            {
                'method': 'POST',
                'path': '/api/v1/analyze',
                'description': 'Analyze project structure and generate insights',
                'parameters': [
                    {'name': 'project_path', 'type': 'string', 'description': 'Path to project directory'},
                    {'name': 'analysis_type', 'type': 'string', 'description': 'Type of analysis to perform'}
                ],
                'response_example': '{"status": "completed", "insights": {...}}'
            },
            {
                'method': 'GET',
                'path': '/api/v1/agents',
                'description': 'List available AI agents',
                'parameters': [],
                'response_example': '{"agents": [{"id": "scout", "capabilities": [...]}]}'
            }
        ]
        
        # 認証情報
        template_data['authentication'] = {
            'type': 'api_key',
            'description': 'API key required for all requests'
        }
        
        # よくある質問
        template_data['faq'] = [
            {
                'question': 'How do I get started with the platform?',
                'answer': 'Follow the installation guide and run the initial setup command.'
            },
            {
                'question': 'Can I customize the AI agents?',
                'answer': 'Yes, the system provides extensive customization options for agent behavior.'
            }
        ]
        
        # トラブルシューティング
        template_data['troubleshooting'] = [
            {
                'problem': 'Installation fails with dependency errors',
                'solution': 'Ensure you have Python 3.9+ and try installing in a clean virtual environment.'
            },
            {
                'problem': 'Agents not responding',
                'solution': 'Check the agent coordinator status and restart if necessary.'
            }
        ]
        
        # チュートリアル
        template_data['tutorials'] = [
            {
                'title': 'Quick Start Tutorial',
                'content': 'Step-by-step guide to setting up your first project with the ecosystem.'
            },
            {
                'title': 'Advanced Agent Configuration',
                'content': 'Learn how to configure and customize AI agents for specific tasks.'
            }
        ]
        
        # 統計情報をテンプレートデータに追加
        if project_structure.get('statistics'):
            stats = project_structure['statistics']
            template_data.update({
                'total_files': stats.get('total_files', 0),
                'total_lines': stats.get('total_lines', 0),
                'languages_used': stats.get('languages', [])
            })
        
        return template_data
        
    except Exception as e:
        self.logger.error(f"Template data preparation failed: {e}")
        return {
            'project_name': 'Project',
            'description': 'Project description',
            'author': 'Developer',
            'year': str(datetime.now().year)
        }


async def _write_multilingual_documentation_files(self, multilingual_docs: Dict[str, Any]) -> List[str]:
    """多言語ドキュメントファイル書き込み"""
    output_files = []
    
    try:
        for doc_type, language_docs in multilingual_docs.items():
            if doc_type == 'error':
                continue
                
            for language_code, doc_data in language_docs.items():
                try:
                    # ファイル名生成
                    filename = self._generate_multilingual_filename(doc_type, language_code)
                    file_path = self.config.output_path / filename
                    
                    # コンテンツ取得
                    content = doc_data.get('content', '')
                    
                    # メタデータヘッダー追加
                    metadata_header = self._generate_metadata_header(doc_data, doc_type, language_code)
                    full_content = f"{metadata_header}\n\n{content}"
                    
                    # ファイル書き込み
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(full_content)
                    
                    output_files.append(str(file_path))
                    
                    # ログ出力
                    status = "translated" if doc_data.get('translated', False) else "original"
                    self.logger.info(f"Generated multilingual doc: {filename} ({status})")
                    
                except Exception as e:
                    self.logger.error(f"Failed to write {doc_type}_{language_code}: {e}")
        
        self.logger.info(f"Multilingual documentation written: {len(output_files)} files")
        return output_files
        
    except Exception as e:
        self.logger.error(f"Multilingual file writing failed: {e}")
        return []


def _generate_multilingual_filename(self, doc_type: str, language_code: str) -> str:
    """多言語ファイル名生成"""
    try:
        # ドキュメントタイプのクリーンアップ
        clean_doc_type = doc_type.replace('_', '-').lower()
        
        # 言語固有のファイル名
        if language_code == 'en':
            return f"{clean_doc_type}.md"
        else:
            return f"{clean_doc_type}_{language_code}.md"
            
    except Exception as e:
        self.logger.error(f"Filename generation failed: {e}")
        return f"document_{language_code}.md"


def _generate_metadata_header(self, doc_data: Dict[str, Any], doc_type: str, language_code: str) -> str:
    """メタデータヘッダー生成"""
    try:
        timestamp = datetime.now().isoformat()
        
        metadata = f"""---
document_type: {doc_type}
language: {language_code}
generated_at: {timestamp}
generator: Ultimate ShunsukeModel Ecosystem Documentation Synthesizer
version: 1.0.0"""
        
        # 翻訳情報の追加
        if doc_data.get('translated', False):
            metadata += f"""
translated: true
source_language: {doc_data.get('source_language', 'unknown')}
translation_confidence: {doc_data.get('translation_confidence', 0.0)}
cultural_adaptations: {len(doc_data.get('cultural_adaptations', []))}
terminology_applied: {len(doc_data.get('terminology_used', []))}"""
        
        # テンプレート情報の追加
        if doc_data.get('template_applied', False):
            metadata += f"""
template_applied: true
template_type: {doc_data.get('template_type', 'unknown')}"""
        
        # エラー情報の追加
        if doc_data.get('error'):
            metadata += f"""
generation_error: {doc_data['error']}
fallback_used: {doc_data.get('fallback', False)}"""
        
        metadata += "\n---"
        
        return metadata
        
    except Exception as e:
        self.logger.error(f"Metadata header generation failed: {e}")
        return f"---\ngenerated_at: {datetime.now().isoformat()}\nerror: {str(e)}\n---"


async def generate_multilingual_project_summary(self) -> Dict[str, Any]:
    """
    多言語プロジェクトサマリー生成
    
    プロジェクト全体の概要を複数言語で生成
    """
    try:
        if not self.multilingual_manager or not self.template_manager:
            return {'error': 'Multilingual systems not initialized'}
        
        # プロジェクト解析
        project_structure = await self.code_analyzer.analyze_project_structure(self.config.project_path)
        
        # サポート言語取得
        supported_languages = await self.multilingual_manager.get_supported_languages()
        target_languages = [LanguageCode(lang['code']) for lang in supported_languages]
        
        summaries = {}
        
        for language in target_languages:
            try:
                # 言語固有のプロジェクトサマリー生成
                template_data = self._prepare_template_data(project_structure, None)
                
                summary = await self.template_manager.generate_document(
                    template_type=TemplateType.README,
                    language=language,
                    data=template_data,
                    style=DocumentStyle.TECHNICAL
                )
                
                summaries[language.value] = {
                    'content': summary,
                    'language': language.value,
                    'generated_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Failed to generate summary for {language.value}: {e}")
                summaries[language.value] = {
                    'error': str(e),
                    'language': language.value
                }
        
        return {
            'status': 'completed',
            'summaries': summaries,
            'languages_processed': len(summaries),
            'project_path': str(self.config.project_path)
        }
        
    except Exception as e:
        self.logger.error(f"Multilingual project summary generation failed: {e}")
        return {
            'status': 'failed',
            'error': str(e)
        }


# DocumentationSynthesizerクラスにメソッドを動的に追加するためのヘルパー
def add_multilingual_methods_to_synthesizer():
    """DocumentationSynthesizerクラスに多言語メソッドを追加"""
    from .documentation_synthesizer import DocumentationSynthesizer
    
    # メソッドを動的に追加
    DocumentationSynthesizer._generate_multilingual_documentation = _generate_multilingual_documentation
    DocumentationSynthesizer._generate_localized_document = _generate_localized_document
    DocumentationSynthesizer._extract_document_content = _extract_document_content
    DocumentationSynthesizer._prepare_template_data = _prepare_template_data
    DocumentationSynthesizer._write_multilingual_documentation_files = _write_multilingual_documentation_files
    DocumentationSynthesizer._generate_multilingual_filename = _generate_multilingual_filename
    DocumentationSynthesizer._generate_metadata_header = _generate_metadata_header
    DocumentationSynthesizer.generate_multilingual_project_summary = generate_multilingual_project_summary
    
    return DocumentationSynthesizer