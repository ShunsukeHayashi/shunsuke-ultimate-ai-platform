#!/usr/bin/env python3
"""
シュンスケ式セキュリティテストスイート - Ultimate ShunsukeModel Ecosystem

包括的なセキュリティ脆弱性検証フレームワーク
"""

from .security_test_framework import (
    SecurityTestFramework,
    VulnerabilityType,
    SeverityLevel,
    TestStatus,
    SecurityTestCase,
    SecurityFinding,
    SecurityTestResult,
    SecurityReport,
    create_security_test_framework
)

from .vulnerability_payloads import (
    VulnerabilityPayloads,
    PayloadCategory
)

__version__ = "1.0.0"
__author__ = "ShunsukeModel Team"

__all__ = [
    # Security Test Framework
    "SecurityTestFramework",
    "VulnerabilityType",
    "SeverityLevel",
    "TestStatus",
    "SecurityTestCase",
    "SecurityFinding",
    "SecurityTestResult",
    "SecurityReport",
    "create_security_test_framework",
    
    # Vulnerability Payloads
    "VulnerabilityPayloads",
    "PayloadCategory"
]

# モジュール情報
__doc__ = """
Ultimate ShunsukeModel Ecosystem - Security Test Suite

包括的なセキュリティ脆弱性検証フレームワーク

主要コンポーネント:

1. Security Test Framework (セキュリティテストフレームワーク)
   - 包括的な脆弱性スキャン
   - 自動ペネトレーションテスト
   - コード静的解析
   - セキュリティ設定監査
   - コンプライアンスチェック
   - リスク評価とスコアリング

2. Vulnerability Payloads (脆弱性ペイロード)
   - SQLインジェクション
   - クロスサイトスクリプティング（XSS）
   - コマンドインジェクション
   - パストラバーサル
   - XML外部エンティティ（XXE）
   - サーバーサイドテンプレートインジェクション（SSTI）
   - LDAPインジェクション
   - HTTPヘッダーインジェクション
   - サーバーサイドリクエストフォージェリ（SSRF）

使用例:

# 基本的なセキュリティスキャン
from tests.security import create_security_test_framework

async def run_security_scan():
    framework = create_security_test_framework()
    report = await framework.run_security_scan("./target_project")
    
    print(f"Risk Score: {report.overall_risk_score}/10")
    print(f"Critical Findings: {report.critical_findings}")

# カスタムセキュリティポリシー
framework = create_security_test_framework({
    'security_policy': {
        'min_password_length': 16,
        'require_mfa': True,
        'allowed_protocols': ['https'],
        'banned_functions': ['eval', 'exec', 'system']
    }
})

# ペイロード使用例
from tests.security import VulnerabilityPayloads, PayloadCategory

# SQLインジェクションペイロード取得
sql_payloads = VulnerabilityPayloads.get_sql_injection_payloads()

# 全カテゴリのペイロード取得
all_payloads = VulnerabilityPayloads.get_all_payloads()

# ペイロードエンコーディング
encoded = VulnerabilityPayloads.encode_payload(
    "<script>alert('XSS')</script>",
    'html_entity'
)

脆弱性タイプ:
- INJECTION: インジェクション攻撃
- BROKEN_AUTH: 認証の不備
- SENSITIVE_DATA: 機密データ露出
- XXE: XML外部エンティティ
- BROKEN_ACCESS: アクセス制御の不備
- MISCONFIG: セキュリティ設定ミス
- XSS: クロスサイトスクリプティング
- DESERIALIZATION: 安全でないデシリアライゼーション
- COMPONENTS: 既知の脆弱性を持つコンポーネント
- LOGGING: 不十分なロギング
- SSRF: サーバーサイドリクエストフォージェリ
- PATH_TRAVERSAL: ディレクトリトラバーサル
- RACE_CONDITION: 競合状態
- DOS: サービス拒否

深刻度レベル:
- CRITICAL: 緊急対応が必要
- HIGH: 高リスク
- MEDIUM: 中リスク
- LOW: 低リスク
- INFO: 情報提供

レポート機能:
- HTMLレポート（視覚的）
- JSONレポート（プログラマティック）
- エグゼクティブサマリー
- 技術詳細
- 修正優先度リスト
- コンプライアンス状態

コンプライアンス基準:
- OWASP Top 10
- PCI DSS
- GDPR
- SOC 2

統合機能:
- Command Tower連携
- Quality Guardian連携
- Resource Monitor統合
- 自動修正提案
- CI/CDパイプライン統合
"""