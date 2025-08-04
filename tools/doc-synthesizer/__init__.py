#!/usr/bin/env python3
"""
シュンスケ式ドキュメント統合システム - Ultimate ShunsukeModel Ecosystem

自動ドキュメント生成、多言語対応、品質保証機能を統合したドキュメント作成システム
"""

try:
    from .documentation_synthesizer import (
        DocumentationSynthesizer,
        DocumentationConfig,
        DocumentType,
        DocumentFormat,
        DocumentationQuality,
        Language,
        QualityLevel,
        DocumentSection
    )

    from .multilingual_manager import (
        MultilingualManager,
        LanguageCode,
        DocumentStyle,
        TranslationRequest,
        TranslationResult,
        LocalizationRule,
        TerminologyEntry,
        create_multilingual_manager
    )

    from .multilingual_templates import (
        MultilingualTemplateManager,
        TemplateType,
        TemplateMetadata,
        LocalizationSettings,
        LanguageTemplateEngine,
        JapaneseTemplateEngine,
        EnglishTemplateEngine,
        create_multilingual_template_manager
    )

    from .multilingual_documentation_methods import (
        add_multilingual_methods_to_synthesizer
    )

    # 多言語メソッドをDocumentationSynthesizerクラスに統合
    add_multilingual_methods_to_synthesizer()
    
except ImportError as import_error:
    print(f"Warning: Could not import doc-synthesizer modules: {import_error}")
    
    # フォールバック用のダミークラス
    class DocumentationSynthesizer:
        def __init__(self, *args, **kwargs):
            raise ImportError("DocumentationSynthesizer not available due to import error")
    
    # 基本的なエクスポート用のダミー
    class MultilingualManager:
        pass
    
    class LanguageCode:
        JAPANESE = "ja"
        ENGLISH = "en"

__version__ = "1.0.0"
__author__ = "ShunsukeModel Team"

__all__ = [
    # Core Documentation System
    "DocumentationSynthesizer",
    "DocumentationConfig",
    "DocumentType",
    "DocumentFormat", 
    "DocumentationQuality",
    "Language",
    "QualityLevel",
    "DocumentSection",
    
    # Multilingual Management
    "MultilingualManager", 
    "LanguageCode",
    "DocumentStyle",
    "TranslationRequest",
    "TranslationResult",
    "LocalizationRule",
    "TerminologyEntry",
    "create_multilingual_manager",
    
    # Template System
    "MultilingualTemplateManager",
    "TemplateType",
    "TemplateMetadata",
    "LocalizationSettings",
    "LanguageTemplateEngine",
    "JapaneseTemplateEngine",
    "EnglishTemplateEngine",
    "create_multilingual_template_manager",
    
    # Integration
    "add_multilingual_methods_to_synthesizer"
]

# モジュール情報
__doc__ = """
Ultimate ShunsukeModel Ecosystem - Documentation Synthesizer

主要機能:
1. 自動ドキュメント生成 - コードベースから包括的なドキュメントを自動生成
2. 多言語対応 - 複数言語での一貫したドキュメント作成
3. 品質保証 - 自動品質チェックと改善提案
4. テンプレート管理 - 言語固有のドキュメントテンプレート
5. 翻訳システム - 高品質な技術文書翻訳

使用例:
```python
from tools.doc_synthesizer import (
    DocumentationSynthesizer,
    DocumentationConfig,
    DocumentType,
    LanguageCode
)

# 設定
config = DocumentationConfig(
    project_path=Path("./my_project"),
    output_path=Path("./docs"),
    languages=[Language.ENGLISH, Language.JAPANESE]
)

# システム初期化
synthesizer = DocumentationSynthesizer(config)
await synthesizer.initialize()

# 完全ドキュメント生成
result = await synthesizer.synthesize_complete_documentation([
    DocumentType.README,
    DocumentType.API_REFERENCE,
    DocumentType.USER_GUIDE
])

print(f"Generated {result['documents_generated']} documents")
```

アーキテクチャ:
- DocumentationSynthesizer: メインのドキュメント生成システム
- MultilingualManager: 翻訳・言語処理エンジン
- MultilingualTemplateManager: 言語固有テンプレート管理
- Quality Guardian: 品質監視・改善システム

統合機能:
- Claude Code グローバル設定対応
- GitHub Actions 自動化
- MCP (Model Context Protocol) サーバー統合
- リアルタイム品質監視
- 自動改善提案システム
"""