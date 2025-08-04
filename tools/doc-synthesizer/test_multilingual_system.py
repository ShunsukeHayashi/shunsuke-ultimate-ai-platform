#!/usr/bin/env python3
"""
シュンスケ式多言語ドキュメントシステム テスト - Ultimate ShunsukeModel Ecosystem

多言語対応ドキュメント生成システムの包括的テスト
"""

import asyncio
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# テスト対象モジュールのインポート
try:
    from .multilingual_manager import (
        MultilingualManager, LanguageCode, DocumentStyle, 
        TranslationRequest, create_multilingual_manager
    )
    from .multilingual_templates import (
        MultilingualTemplateManager, TemplateType,
        create_multilingual_template_manager
    )
    from .documentation_synthesizer import (
        DocumentationSynthesizer, DocumentationConfig,
        DocumentType, DocumentFormat, DocumentationQuality, Language
    )
    from .multilingual_documentation_methods import add_multilingual_methods_to_synthesizer
except ImportError as e:
    print(f"Import error: {e}")
    print("Running tests from parent directory...")
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    from tools.doc_synthesizer.multilingual_manager import (
        MultilingualManager, LanguageCode, DocumentStyle, 
        TranslationRequest, create_multilingual_manager
    )
    from tools.doc_synthesizer.multilingual_templates import (
        MultilingualTemplateManager, TemplateType,
        create_multilingual_template_manager
    )
    from tools.doc_synthesizer.documentation_synthesizer import (
        DocumentationSynthesizer, DocumentationConfig,
        DocumentType, DocumentFormat, DocumentationQuality, Language
    )
    from tools.doc_synthesizer.multilingual_documentation_methods import add_multilingual_methods_to_synthesizer


class MultilingualSystemTest:
    """多言語システム包括テスト"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # テスト用一時ディレクトリ
        self.test_dir = None
        self.project_dir = None
        self.output_dir = None
        
        # テスト結果
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
    
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # ファイルハンドラー追加
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem' / 'tests'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / 'multilingual_test.log')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
    
    async def setup_test_environment(self):
        """テスト環境セットアップ"""
        try:
            # 一時ディレクトリ作成
            self.test_dir = Path(tempfile.mkdtemp(prefix="multilingual_test_"))
            self.project_dir = self.test_dir / "test_project"
            self.output_dir = self.test_dir / "output"
            
            # テストプロジェクト構造作成
            await self._create_test_project_structure()
            
            self.logger.info(f"Test environment setup completed: {self.test_dir}")
            
        except Exception as e:
            self.logger.error(f"Test environment setup failed: {e}")
            raise
    
    async def _create_test_project_structure(self):
        """テストプロジェクト構造作成"""
        # プロジェクトディレクトリ
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # サンプルPythonファイル
        (self.project_dir / "main.py").write_text('''
"""Sample main module for testing"""

class TestClass:
    """A test class for documentation generation"""
    
    def __init__(self, name: str):
        """Initialize with name"""
        self.name = name
    
    def greet(self) -> str:
        """Return a greeting message"""
        return f"Hello, {self.name}!"

def main():
    """Main function"""
    test = TestClass("World")
    print(test.greet())

if __name__ == "__main__":
    main()
''')
        
        # setup.py
        (self.project_dir / "setup.py").write_text('''
from setuptools import setup, find_packages

setup(
    name="test-project",
    version="1.0.0",
    description="A test project for multilingual documentation",
    packages=find_packages(),
    python_requires=">=3.9",
)
''')
        
        # requirements.txt
        (self.project_dir / "requirements.txt").write_text('''
aiohttp>=3.8.0
pydantic>=2.0.0
''')
        
        # README.md
        (self.project_dir / "README.md").write_text('''
# Test Project

This is a test project for multilingual documentation generation.

## Features

- Test functionality
- Documentation generation
- Quality assurance
''')
    
    async def test_multilingual_manager(self) -> Dict[str, Any]:
        """多言語管理システムテスト"""
        test_name = "MultilingualManager Test"
        self.test_results['tests_run'] += 1
        
        try:
            self.logger.info(f"Starting {test_name}")
            
            # MultilingualManager インスタンス作成
            manager = await create_multilingual_manager()
            
            # 1. 言語検出テスト
            text_en = "This is a test document for language detection."
            lang_en, confidence_en = await manager.detect_language(text_en)
            
            text_ja = "これは言語検出のためのテストドキュメントです。"
            lang_ja, confidence_ja = await manager.detect_language(text_ja)
            
            assert lang_en == LanguageCode.ENGLISH, f"Expected English, got {lang_en}"
            assert lang_ja == LanguageCode.JAPANESE, f"Expected Japanese, got {lang_ja}"
            
            # 2. 翻訳テスト
            translation_request = TranslationRequest(
                source_language=LanguageCode.ENGLISH,
                target_language=LanguageCode.JAPANESE,
                text="Quality Analysis System",
                style=DocumentStyle.TECHNICAL
            )
            
            translation_result = await manager.translate_text(translation_request)
            
            assert translation_result.translated_text, "Translation result should not be empty"
            assert translation_result.source_language == LanguageCode.ENGLISH
            assert translation_result.target_language == LanguageCode.JAPANESE
            
            # 3. サポート言語リスト取得
            supported_languages = await manager.get_supported_languages()
            assert len(supported_languages) > 0, "Should have supported languages"
            
            # 4. 翻訳品質レポート
            quality_report = await manager.get_translation_quality_report()
            assert 'total_translations' in quality_report
            
            self.test_results['tests_passed'] += 1
            self.logger.info(f"{test_name} PASSED")
            
            return {
                'status': 'passed',
                'language_detection': {
                    'english': {'detected': lang_en.value, 'confidence': confidence_en},
                    'japanese': {'detected': lang_ja.value, 'confidence': confidence_ja}
                },
                'translation': {
                    'original': translation_request.text,
                    'translated': translation_result.translated_text,
                    'confidence': translation_result.confidence_score
                },
                'supported_languages_count': len(supported_languages)
            }
            
        except Exception as e:
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {str(e)}")
            self.logger.error(f"{test_name} FAILED: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def test_multilingual_templates(self) -> Dict[str, Any]:
        """多言語テンプレートシステムテスト"""
        test_name = "MultilingualTemplates Test"
        self.test_results['tests_run'] += 1
        
        try:
            self.logger.info(f"Starting {test_name}")
            
            # MultilingualTemplateManager インスタンス作成
            manager = await create_multilingual_template_manager()
            
            # テストデータ準備
            project_data = {
                'name': 'Test Project',
                'description': 'A test project for multilingual templates',
                'python_version': '3.9',
                'author': 'Test Author',
                'year': '2025',
                'features': ['Feature 1', 'Feature 2', 'Feature 3']
            }
            
            # 1. 日本語README生成
            ja_readme = await manager.generate_document(
                TemplateType.README,
                LanguageCode.JAPANESE,
                project_data,
                DocumentStyle.TECHNICAL
            )
            
            assert ja_readme, "Japanese README should not be empty"
            assert 'Test Project' in ja_readme
            assert '概要' in ja_readme or '目次' in ja_readme
            
            # 2. 英語README生成
            en_readme = await manager.generate_document(
                TemplateType.README,
                LanguageCode.ENGLISH,
                project_data,
                DocumentStyle.TECHNICAL
            )
            
            assert en_readme, "English README should not be empty"
            assert 'Test Project' in en_readme
            assert 'Table of Contents' in en_readme or 'Overview' in en_readme
            
            # 3. 多言語一括生成
            multilingual_docs = await manager.generate_multilingual_docs(
                TemplateType.README,
                project_data,
                [LanguageCode.JAPANESE, LanguageCode.ENGLISH],
                DocumentStyle.TECHNICAL
            )
            
            assert len(multilingual_docs) == 2, "Should generate 2 language versions"
            assert 'ja' in multilingual_docs
            assert 'en' in multilingual_docs
            
            # 4. サポートテンプレートタイプ取得
            template_types = await manager.get_supported_template_types()
            assert len(template_types) > 0, "Should have supported template types"
            
            self.test_results['tests_passed'] += 1
            self.logger.info(f"{test_name} PASSED")
            
            return {
                'status': 'passed',
                'japanese_readme_length': len(ja_readme),
                'english_readme_length': len(en_readme),
                'multilingual_docs_count': len(multilingual_docs),
                'supported_template_types': len(template_types)
            }
            
        except Exception as e:
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {str(e)}")
            self.logger.error(f"{test_name} FAILED: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def test_integrated_documentation_synthesizer(self) -> Dict[str, Any]:
        """統合ドキュメント生成システムテスト"""
        test_name = "Integrated DocumentationSynthesizer Test"
        self.test_results['tests_run'] += 1
        
        try:
            self.logger.info(f"Starting {test_name}")
            
            # 多言語メソッドを統合
            add_multilingual_methods_to_synthesizer()
            
            # DocumentationSynthesizer 設定
            config = DocumentationConfig(
                project_path=self.project_dir,
                output_path=self.output_dir,
                languages=[Language.ENGLISH, Language.JAPANESE],
                formats=[DocumentFormat.MARKDOWN],
                quality_level=DocumentationQuality.STANDARD
            )
            
            # システム初期化
            synthesizer = DocumentationSynthesizer(config)
            await synthesizer.initialize()
            
            # 1. 完全ドキュメント生成テスト
            result = await synthesizer.synthesize_complete_documentation([
                DocumentType.README,
                DocumentType.API_REFERENCE
            ])
            
            assert result['status'] == 'completed', f"Generation failed: {result.get('error', 'Unknown error')}"
            assert len(result['generated_files']) > 0, "Should generate files"
            
            # 2. 多言語プロジェクトサマリー生成テスト
            if hasattr(synthesizer, 'generate_multilingual_project_summary'):
                summary_result = await synthesizer.generate_multilingual_project_summary()
                assert summary_result['status'] == 'completed'
                assert len(summary_result['summaries']) > 0
            
            # 3. 生成ファイル確認
            generated_files = result['generated_files']
            files_exist = all(Path(file_path).exists() for file_path in generated_files)
            assert files_exist, "All generated files should exist"
            
            # 4. 統計情報確認
            stats = await synthesizer.get_generation_statistics()
            assert 'current_stats' in stats
            assert stats['current_stats']['documents_generated'] > 0
            
            self.test_results['tests_passed'] += 1
            self.logger.info(f"{test_name} PASSED")
            
            return {
                'status': 'passed',
                'generated_files_count': len(generated_files),
                'documents_generated': result['generation_stats']['documents_generated'],
                'languages_processed': result['generation_stats']['languages_processed'],
                'execution_time': result['execution_time'],
                'files_exist': files_exist
            }
            
        except Exception as e:
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {str(e)}")
            self.logger.error(f"{test_name} FAILED: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def test_quality_assurance(self) -> Dict[str, Any]:
        """品質保証機能テスト"""
        test_name = "Quality Assurance Test"
        self.test_results['tests_run'] += 1
        
        try:
            self.logger.info(f"Starting {test_name}")
            
            # テスト用ドキュメントファイル作成
            test_doc_path = self.output_dir / "test_quality.md"
            test_doc_content = '''# Test Document

This is a test document for quality analysis.

## Features

- Feature 1
- Feature 2

## Code Example

```python
def hello():
    return "Hello, World!"
```

## Links

[GitHub](https://github.com/test/repo)
'''
            
            test_doc_path.write_text(test_doc_content)
            
            # DocumentationSynthesizer で品質チェック
            config = DocumentationConfig(
                project_path=self.project_dir,
                output_path=self.output_dir,
                languages=[Language.ENGLISH],
                formats=[DocumentFormat.MARKDOWN],
                quality_level=DocumentationQuality.HIGH
            )
            
            synthesizer = DocumentationSynthesizer(config)
            await synthesizer.initialize()
            
            # 品質チェック実行
            quality_report = await synthesizer._perform_quality_check([str(test_doc_path)])
            
            assert 'file_sizes' in quality_report
            assert 'content_analysis' in quality_report
            
            # コンテンツ解析結果確認
            analysis = quality_report['content_analysis'][str(test_doc_path)]
            assert analysis['has_code_examples'] == True
            assert analysis['has_links'] == True
            assert analysis['header_count'] >= 2
            
            self.test_results['tests_passed'] += 1
            self.logger.info(f"{test_name} PASSED")
            
            return {
                'status': 'passed',
                'quality_report': quality_report,
                'has_code_examples': analysis['has_code_examples'],
                'has_links': analysis['has_links'],
                'header_count': analysis['header_count']
            }
            
        except Exception as e:
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {str(e)}")
            self.logger.error(f"{test_name} FAILED: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def cleanup_test_environment(self):
        """テスト環境クリーンアップ"""
        try:
            if self.test_dir and self.test_dir.exists():
                shutil.rmtree(self.test_dir)
                self.logger.info(f"Test environment cleaned up: {self.test_dir}")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """全テスト実行"""
        self.logger.info("Starting comprehensive multilingual system tests")
        
        test_results = {}
        
        try:
            # テスト環境セットアップ
            await self.setup_test_environment()
            
            # 個別テスト実行
            test_results['multilingual_manager'] = await self.test_multilingual_manager()
            test_results['multilingual_templates'] = await self.test_multilingual_templates()
            test_results['integrated_synthesizer'] = await self.test_integrated_documentation_synthesizer()
            test_results['quality_assurance'] = await self.test_quality_assurance()
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            test_results['setup_error'] = str(e)
        
        finally:
            # クリーンアップ
            await self.cleanup_test_environment()
        
        # テスト結果サマリー
        test_summary = {
            'overall_status': 'passed' if self.test_results['tests_failed'] == 0 else 'failed',
            'tests_run': self.test_results['tests_run'],
            'tests_passed': self.test_results['tests_passed'],
            'tests_failed': self.test_results['tests_failed'],
            'success_rate': f"{(self.test_results['tests_passed'] / max(self.test_results['tests_run'], 1)) * 100:.1f}%",
            'errors': self.test_results['errors'],
            'detailed_results': test_results
        }
        
        self.logger.info(f"All tests completed: {test_summary['overall_status']}")
        self.logger.info(f"Success rate: {test_summary['success_rate']}")
        
        return test_summary


async def main():
    """メインテスト実行関数"""
    print("🚀 Ultimate ShunsukeModel Ecosystem - Multilingual Documentation System Test")
    print("=" * 80)
    
    # テストインスタンス作成
    test_runner = MultilingualSystemTest()
    
    # 全テスト実行
    results = await test_runner.run_all_tests()
    
    # 結果表示
    print("\n📊 Test Results Summary:")
    print(f"Overall Status: {'✅ PASSED' if results['overall_status'] == 'passed' else '❌ FAILED'}")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"Success Rate: {results['success_rate']}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\n🔍 Detailed Results:")
    for test_name, test_result in results['detailed_results'].items():
        status = "✅ PASSED" if test_result.get('status') == 'passed' else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if test_result.get('error'):
            print(f"    Error: {test_result['error']}")
    
    # JSON結果出力
    output_file = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem' / 'multilingual_test_results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    print("\n🎉 Multilingual Documentation System Test Completed!")
    
    return results


if __name__ == "__main__":
    # asyncio実行
    results = asyncio.run(main())
    
    # 終了コード設定
    exit_code = 0 if results['overall_status'] == 'passed' else 1
    sys.exit(exit_code)