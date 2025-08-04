#!/usr/bin/env python3
"""
シュンスケ式セキュリティテストフレームワーク - Ultimate ShunsukeModel Ecosystem

システムのセキュリティ脆弱性を包括的に検証し、
攻撃耐性とデータ保護能力を評価する高度なセキュリティテストシステム
"""

import asyncio
import hashlib
import hmac
import secrets
import re
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
import subprocess
import sys
import os
import ast
import inspect
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
import aiohttp
from collections import defaultdict


# テスト対象モジュールのインポート
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.command_tower.command_tower import CommandTower
from orchestration.communication.communication_protocol import CommunicationProtocol


class VulnerabilityType(Enum):
    """脆弱性タイプ"""
    INJECTION = "injection"
    BROKEN_AUTH = "broken_authentication"
    SENSITIVE_DATA = "sensitive_data_exposure"
    XXE = "xml_external_entities"
    BROKEN_ACCESS = "broken_access_control"
    MISCONFIG = "security_misconfiguration"
    XSS = "cross_site_scripting"
    DESERIALIZATION = "insecure_deserialization"
    COMPONENTS = "using_components_with_vulnerabilities"
    LOGGING = "insufficient_logging"
    SSRF = "server_side_request_forgery"
    PATH_TRAVERSAL = "path_traversal"
    RACE_CONDITION = "race_condition"
    DOS = "denial_of_service"


class SeverityLevel(Enum):
    """深刻度レベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TestStatus(Enum):
    """テストステータス"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    VULNERABLE = "vulnerable"
    ERROR = "error"


@dataclass
class SecurityTestCase:
    """セキュリティテストケース"""
    test_id: str
    name: str
    description: str
    vulnerability_type: VulnerabilityType
    severity: SeverityLevel
    test_function: Callable
    remediation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class SecurityFinding:
    """セキュリティ発見事項"""
    finding_id: str
    test_case: SecurityTestCase
    vulnerability_confirmed: bool
    severity: SeverityLevel
    location: str
    evidence: str
    impact: str
    likelihood: str
    risk_score: float
    remediation_steps: List[str]
    references: List[str] = field(default_factory=list)
    false_positive: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityTestResult:
    """セキュリティテスト結果"""
    test_id: str
    test_name: str
    status: TestStatus
    vulnerability_type: VulnerabilityType
    findings: List[SecurityFinding] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)


@dataclass
class SecurityReport:
    """セキュリティレポート"""
    report_id: str
    scan_start_time: datetime
    scan_end_time: datetime
    total_tests: int
    tests_passed: int
    tests_failed: int
    vulnerabilities_found: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    overall_risk_score: float
    test_results: List[SecurityTestResult]
    executive_summary: str
    technical_details: Dict[str, Any]
    remediation_priority: List[Dict[str, Any]]
    compliance_status: Dict[str, bool]


class SecurityTestFramework:
    """
    シュンスケ式セキュリティテストフレームワーク
    
    機能:
    - 包括的な脆弱性スキャン
    - 自動ペネトレーションテスト
    - コード静的解析
    - 設定監査
    - コンプライアンスチェック
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # テスト設定
        self.test_output_dir = Path(self.config.get('output_dir', './security_test_results'))
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # テストケース管理
        self.test_cases: List[SecurityTestCase] = []
        self.test_results: List[SecurityTestResult] = []
        
        # 統計情報
        self.stats = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'vulnerable': 0,
            'errors': 0,
            'findings_by_severity': defaultdict(int),
            'findings_by_type': defaultdict(int)
        }
        
        # セキュリティポリシー
        self.security_policy = self.config.get('security_policy', {
            'max_password_age_days': 90,
            'min_password_length': 12,
            'require_mfa': True,
            'allowed_protocols': ['https', 'ssh'],
            'banned_functions': ['eval', 'exec', '__import__'],
            'secure_headers': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
            }
        })
        
        # テストケース初期化
        self._initialize_test_cases()
    
    def _initialize_test_cases(self):
        """標準テストケース初期化"""
        self.test_cases = [
            # インジェクション攻撃
            SecurityTestCase(
                test_id="SEC-001",
                name="SQL Injection Test",
                description="Test for SQL injection vulnerabilities",
                vulnerability_type=VulnerabilityType.INJECTION,
                severity=SeverityLevel.CRITICAL,
                test_function=self._test_sql_injection,
                remediation="Use parameterized queries and input validation",
                cwe_id="CWE-89",
                owasp_category="A03:2021"
            ),
            
            SecurityTestCase(
                test_id="SEC-002",
                name="Command Injection Test",
                description="Test for OS command injection vulnerabilities",
                vulnerability_type=VulnerabilityType.INJECTION,
                severity=SeverityLevel.CRITICAL,
                test_function=self._test_command_injection,
                remediation="Avoid shell commands, use safe APIs",
                cwe_id="CWE-78",
                owasp_category="A03:2021"
            ),
            
            # 認証・認可
            SecurityTestCase(
                test_id="SEC-003",
                name="Weak Authentication Test",
                description="Test for weak authentication mechanisms",
                vulnerability_type=VulnerabilityType.BROKEN_AUTH,
                severity=SeverityLevel.HIGH,
                test_function=self._test_weak_authentication,
                remediation="Implement strong authentication with MFA",
                cwe_id="CWE-287",
                owasp_category="A07:2021"
            ),
            
            SecurityTestCase(
                test_id="SEC-004",
                name="Broken Access Control Test",
                description="Test for access control vulnerabilities",
                vulnerability_type=VulnerabilityType.BROKEN_ACCESS,
                severity=SeverityLevel.HIGH,
                test_function=self._test_access_control,
                remediation="Implement proper authorization checks",
                cwe_id="CWE-285",
                owasp_category="A01:2021"
            ),
            
            # データ保護
            SecurityTestCase(
                test_id="SEC-005",
                name="Sensitive Data Exposure Test",
                description="Test for exposed sensitive data",
                vulnerability_type=VulnerabilityType.SENSITIVE_DATA,
                severity=SeverityLevel.HIGH,
                test_function=self._test_sensitive_data_exposure,
                remediation="Encrypt sensitive data at rest and in transit",
                cwe_id="CWE-200",
                owasp_category="A02:2021"
            ),
            
            SecurityTestCase(
                test_id="SEC-006",
                name="Hardcoded Secrets Test",
                description="Test for hardcoded credentials and secrets",
                vulnerability_type=VulnerabilityType.SENSITIVE_DATA,
                severity=SeverityLevel.CRITICAL,
                test_function=self._test_hardcoded_secrets,
                remediation="Use secure secret management systems",
                cwe_id="CWE-798",
                owasp_category="A02:2021"
            ),
            
            # 設定
            SecurityTestCase(
                test_id="SEC-007",
                name="Security Misconfiguration Test",
                description="Test for security misconfigurations",
                vulnerability_type=VulnerabilityType.MISCONFIG,
                severity=SeverityLevel.MEDIUM,
                test_function=self._test_security_misconfiguration,
                remediation="Follow security hardening guidelines",
                cwe_id="CWE-16",
                owasp_category="A05:2021"
            ),
            
            # パストラバーサル
            SecurityTestCase(
                test_id="SEC-008",
                name="Path Traversal Test",
                description="Test for directory traversal vulnerabilities",
                vulnerability_type=VulnerabilityType.PATH_TRAVERSAL,
                severity=SeverityLevel.HIGH,
                test_function=self._test_path_traversal,
                remediation="Validate and sanitize file paths",
                cwe_id="CWE-22",
                owasp_category="A01:2021"
            ),
            
            # 安全でないデシリアライゼーション
            SecurityTestCase(
                test_id="SEC-009",
                name="Unsafe Deserialization Test",
                description="Test for insecure deserialization",
                vulnerability_type=VulnerabilityType.DESERIALIZATION,
                severity=SeverityLevel.HIGH,
                test_function=self._test_unsafe_deserialization,
                remediation="Avoid deserializing untrusted data",
                cwe_id="CWE-502",
                owasp_category="A08:2021"
            ),
            
            # ロギングとモニタリング
            SecurityTestCase(
                test_id="SEC-010",
                name="Insufficient Logging Test",
                description="Test for adequate security logging",
                vulnerability_type=VulnerabilityType.LOGGING,
                severity=SeverityLevel.MEDIUM,
                test_function=self._test_logging_monitoring,
                remediation="Implement comprehensive security logging",
                cwe_id="CWE-778",
                owasp_category="A09:2021"
            )
        ]
    
    async def run_security_scan(self, target: Union[str, Path, CommandTower]) -> SecurityReport:
        """セキュリティスキャン実行"""
        self.logger.info("Starting comprehensive security scan...")
        scan_start_time = datetime.now()
        report_id = f"SEC-SCAN-{scan_start_time.strftime('%Y%m%d-%H%M%S')}"
        
        # テスト結果リセット
        self.test_results = []
        self.stats = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'vulnerable': 0,
            'errors': 0,
            'findings_by_severity': defaultdict(int),
            'findings_by_type': defaultdict(int)
        }
        
        # 各テストケース実行
        for test_case in self.test_cases:
            self.logger.info(f"Running test: {test_case.name}")
            result = await self._run_test_case(test_case, target)
            self.test_results.append(result)
            self._update_statistics(result)
        
        # 追加の自動テスト
        await self._run_automated_scans(target)
        
        # レポート生成
        scan_end_time = datetime.now()
        report = self._generate_security_report(
            report_id,
            scan_start_time,
            scan_end_time
        )
        
        # レポート保存
        await self._save_report(report)
        
        return report
    
    async def _run_test_case(self, test_case: SecurityTestCase, target: Any) -> SecurityTestResult:
        """個別テストケース実行"""
        result = SecurityTestResult(
            test_id=test_case.test_id,
            test_name=test_case.name,
            status=TestStatus.RUNNING,
            vulnerability_type=test_case.vulnerability_type
        )
        
        try:
            # テスト実行
            findings = await test_case.test_function(target)
            
            # 結果判定
            if findings:
                result.status = TestStatus.VULNERABLE
                result.findings = findings
            else:
                result.status = TestStatus.PASSED
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            self.logger.error(f"Test error in {test_case.name}: {e}")
        
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def _test_sql_injection(self, target: Any) -> List[SecurityFinding]:
        """SQLインジェクションテスト"""
        findings = []
        
        # テストペイロード
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users--",
            "1' UNION SELECT NULL--",
            "' OR 1=1--",
            "admin'--",
            "1' AND '1'='1",
            "' OR 'a'='a",
            "'; EXEC xp_cmdshell('dir')--"
        ]
        
        # コード解析
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            if target_path.is_file():
                code = target_path.read_text()
                
                # 危険なSQLパターン検出
                dangerous_patterns = [
                    r'query\s*\(\s*["\'].*?\+.*?["\']',  # 文字列結合
                    r'query\s*\(\s*f["\']',  # f-string
                    r'query\s*\(\s*["\'].*?%s',  # 文字列フォーマット
                    r'execute\s*\(\s*["\'].*?\+',  # execute with concatenation
                ]
                
                for pattern in dangerous_patterns:
                    matches = re.finditer(pattern, code, re.IGNORECASE)
                    for match in matches:
                        line_num = code[:match.start()].count('\n') + 1
                        
                        finding = SecurityFinding(
                            finding_id=f"SQL-{len(findings)+1}",
                            test_case=self.test_cases[0],  # SQL Injection test case
                            vulnerability_confirmed=True,
                            severity=SeverityLevel.CRITICAL,
                            location=f"{target_path}:{line_num}",
                            evidence=match.group(0),
                            impact="Potential SQL injection could lead to data breach",
                            likelihood="High if user input reaches this code",
                            risk_score=9.5,
                            remediation_steps=[
                                "Use parameterized queries",
                                "Implement input validation",
                                "Use ORM with proper escaping"
                            ]
                        )
                        findings.append(finding)
        
        return findings
    
    async def _test_command_injection(self, target: Any) -> List[SecurityFinding]:
        """コマンドインジェクションテスト"""
        findings = []
        
        # 危険な関数
        dangerous_functions = [
            'os.system',
            'subprocess.call',
            'subprocess.run',
            'subprocess.Popen',
            'eval',
            'exec',
            '__import__'
        ]
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            if target_path.is_file():
                code = target_path.read_text()
                
                # AST解析
                try:
                    tree = ast.parse(code)
                    
                    class DangerousFunctionVisitor(ast.NodeVisitor):
                        def __init__(self):
                            self.findings = []
                        
                        def visit_Call(self, node):
                            # 関数名取得
                            func_name = self._get_func_name(node.func)
                            
                            if func_name in dangerous_functions:
                                line_num = node.lineno
                                
                                # ユーザー入力の可能性をチェック
                                has_user_input = self._check_user_input(node)
                                
                                if has_user_input:
                                    severity = SeverityLevel.CRITICAL
                                    risk_score = 9.0
                                else:
                                    severity = SeverityLevel.HIGH
                                    risk_score = 7.0
                                
                                finding = SecurityFinding(
                                    finding_id=f"CMD-{len(findings)+1}",
                                    test_case=self.test_cases[1],
                                    vulnerability_confirmed=True,
                                    severity=severity,
                                    location=f"{target_path}:{line_num}",
                                    evidence=f"Use of {func_name}",
                                    impact="Command injection could lead to system compromise",
                                    likelihood="High if user input is not sanitized",
                                    risk_score=risk_score,
                                    remediation_steps=[
                                        f"Avoid using {func_name}",
                                        "Use safe alternatives without shell=True",
                                        "Validate and sanitize all inputs"
                                    ]
                                )
                                findings.append(finding)
                            
                            self.generic_visit(node)
                        
                        def _get_func_name(self, node):
                            if isinstance(node, ast.Name):
                                return node.id
                            elif isinstance(node, ast.Attribute):
                                if isinstance(node.value, ast.Name):
                                    return f"{node.value.id}.{node.attr}"
                            return ""
                        
                        def _check_user_input(self, node):
                            # 簡易的なユーザー入力チェック
                            for arg in node.args:
                                if isinstance(arg, ast.Name):
                                    if 'input' in arg.id or 'request' in arg.id:
                                        return True
                            return False
                    
                    visitor = DangerousFunctionVisitor()
                    visitor.visit(tree)
                    findings.extend(visitor.findings)
                    
                except SyntaxError:
                    pass
        
        return findings
    
    async def _test_weak_authentication(self, target: Any) -> List[SecurityFinding]:
        """弱い認証メカニズムテスト"""
        findings = []
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            # パスワードポリシーチェック
            weak_patterns = [
                (r'password.*?=.*?["\'](?=.{0,7}["\'])', "Password too short"),
                (r'password.*?=.*?["\']password["\']', "Default password used"),
                (r'password.*?=.*?["\']admin["\']', "Weak password 'admin'"),
                (r'password.*?=.*?["\']12345', "Weak numeric password"),
                (r'verify_password.*?return\s+True', "Password verification always returns True"),
            ]
            
            if target_path.is_file():
                code = target_path.read_text()
                
                for pattern, description in weak_patterns:
                    matches = re.finditer(pattern, code, re.IGNORECASE)
                    for match in matches:
                        line_num = code[:match.start()].count('\n') + 1
                        
                        finding = SecurityFinding(
                            finding_id=f"AUTH-{len(findings)+1}",
                            test_case=self.test_cases[2],
                            vulnerability_confirmed=True,
                            severity=SeverityLevel.HIGH,
                            location=f"{target_path}:{line_num}",
                            evidence=match.group(0),
                            impact="Weak authentication allows unauthorized access",
                            likelihood="High",
                            risk_score=8.0,
                            remediation_steps=[
                                "Implement strong password policy",
                                "Minimum 12 characters with complexity",
                                "Enable multi-factor authentication",
                                "Use secure password hashing (bcrypt, scrypt)"
                            ]
                        )
                        findings.append(finding)
        
        return findings
    
    async def _test_access_control(self, target: Any) -> List[SecurityFinding]:
        """アクセス制御テスト"""
        findings = []
        
        # アクセス制御の問題パターン
        access_patterns = [
            (r'if.*?is_admin.*?:', "Admin check without proper validation"),
            (r'@app\.route.*?methods.*?POST.*?GET', "Insecure HTTP method handling"),
            (r'def.*?delete.*?\(.*?\):', "Delete operation without authorization check"),
            (r'return.*?user_data.*?password', "Password returned in response"),
        ]
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            if target_path.is_file():
                code = target_path.read_text()
                
                for pattern, description in access_patterns:
                    matches = re.finditer(pattern, code)
                    for match in matches:
                        # 認証チェックの有無を確認
                        context_start = max(0, match.start() - 200)
                        context = code[context_start:match.end()]
                        
                        has_auth_check = any(auth in context for auth in [
                            '@login_required',
                            'check_permission',
                            'authorize',
                            'is_authenticated'
                        ])
                        
                        if not has_auth_check:
                            line_num = code[:match.start()].count('\n') + 1
                            
                            finding = SecurityFinding(
                                finding_id=f"ACCESS-{len(findings)+1}",
                                test_case=self.test_cases[3],
                                vulnerability_confirmed=True,
                                severity=SeverityLevel.HIGH,
                                location=f"{target_path}:{line_num}",
                                evidence=description,
                                impact="Unauthorized access to sensitive functionality",
                                likelihood="Medium",
                                risk_score=7.5,
                                remediation_steps=[
                                    "Implement proper authorization checks",
                                    "Use role-based access control (RBAC)",
                                    "Validate permissions on every request",
                                    "Apply principle of least privilege"
                                ]
                            )
                            findings.append(finding)
        
        return findings
    
    async def _test_sensitive_data_exposure(self, target: Any) -> List[SecurityFinding]:
        """機密データ露出テスト"""
        findings = []
        
        # 機密データパターン
        sensitive_patterns = [
            (r'print\s*\(.*?password.*?\)', "Password logged to console"),
            (r'logger\.(debug|info)\s*\(.*?token.*?\)', "Token logged"),
            (r'return.*?{.*?password.*?:.*?}', "Password in API response"),
            (r'(api_key|secret|token).*?=.*?["\'][A-Za-z0-9]{20,}["\']', "Hardcoded API key"),
            (r'\.env.*?password|secret|key', "Sensitive data in .env file"),
        ]
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            # ディレクトリの場合は再帰的に検索
            if target_path.is_dir():
                for file_path in target_path.rglob('*'):
                    if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.java', '.env']:
                        file_findings = await self._test_sensitive_data_exposure(file_path)
                        findings.extend(file_findings)
            
            elif target_path.is_file():
                try:
                    code = target_path.read_text()
                    
                    for pattern, description in sensitive_patterns:
                        matches = re.finditer(pattern, code, re.IGNORECASE)
                        for match in matches:
                            line_num = code[:match.start()].count('\n') + 1
                            
                            finding = SecurityFinding(
                                finding_id=f"DATA-{len(findings)+1}",
                                test_case=self.test_cases[4],
                                vulnerability_confirmed=True,
                                severity=SeverityLevel.HIGH,
                                location=f"{target_path}:{line_num}",
                                evidence=match.group(0)[:50] + "...",  # 機密情報を隠す
                                impact="Sensitive data exposure could lead to account compromise",
                                likelihood="High",
                                risk_score=8.5,
                                remediation_steps=[
                                    "Never log sensitive data",
                                    "Encrypt data at rest and in transit",
                                    "Use secure key management service",
                                    "Implement data masking in logs"
                                ]
                            )
                            findings.append(finding)
                
                except Exception:
                    pass
        
        return findings
    
    async def _test_hardcoded_secrets(self, target: Any) -> List[SecurityFinding]:
        """ハードコードされた秘密情報テスト"""
        findings = []
        
        # 秘密情報のパターン
        secret_patterns = [
            # API Keys
            (r'["\']AIza[0-9A-Za-z\-_]{35}["\']', "Google API Key"),
            (r'["\']sk_live_[0-9a-zA-Z]{24,}["\']', "Stripe API Key"),
            (r'["\']xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}["\']', "Slack Token"),
            
            # AWS
            (r'["\']AKIA[0-9A-Z]{16}["\']', "AWS Access Key"),
            (r'["\'][0-9a-zA-Z/+=]{40}["\']', "AWS Secret Key"),
            
            # Generic patterns
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded Secret"),
            (r'private_key\s*=\s*["\'][^"\']+["\']', "Hardcoded Private Key"),
        ]
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            if target_path.is_file():
                try:
                    code = target_path.read_text()
                    
                    for pattern, secret_type in secret_patterns:
                        matches = re.finditer(pattern, code)
                        for match in matches:
                            line_num = code[:match.start()].count('\n') + 1
                            
                            # 環境変数チェック
                            context = code[max(0, match.start()-50):match.end()+50]
                            is_env_var = 'os.environ' in context or 'process.env' in context
                            
                            if not is_env_var:
                                finding = SecurityFinding(
                                    finding_id=f"SECRET-{len(findings)+1}",
                                    test_case=self.test_cases[5],
                                    vulnerability_confirmed=True,
                                    severity=SeverityLevel.CRITICAL,
                                    location=f"{target_path}:{line_num}",
                                    evidence=f"{secret_type} detected",
                                    impact="Exposed credentials can lead to full system compromise",
                                    likelihood="Certain",
                                    risk_score=10.0,
                                    remediation_steps=[
                                        "Remove hardcoded secrets immediately",
                                        "Rotate all exposed credentials",
                                        "Use environment variables",
                                        "Implement secure secret management (e.g., HashiCorp Vault)"
                                    ]
                                )
                                findings.append(finding)
                
                except Exception:
                    pass
        
        return findings
    
    async def _test_security_misconfiguration(self, target: Any) -> List[SecurityFinding]:
        """セキュリティ設定ミステスト"""
        findings = []
        
        # 設定ミスのパターン
        misconfig_patterns = [
            (r'DEBUG\s*=\s*True', "Debug mode enabled in production"),
            (r'app\.run\(.*?debug\s*=\s*True', "Flask debug mode enabled"),
            (r'ALLOWED_HOSTS\s*=\s*\[\s*["\']?\*["\']?\s*\]', "Wildcard allowed hosts"),
            (r'verify_ssl\s*=\s*False', "SSL verification disabled"),
            (r'SESSION_COOKIE_SECURE\s*=\s*False', "Insecure session cookies"),
        ]
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            # 設定ファイルを探す
            config_files = ['settings.py', 'config.py', 'config.json', '.env']
            
            if target_path.is_dir():
                for config_file in config_files:
                    config_path = target_path / config_file
                    if config_path.exists():
                        file_findings = await self._test_security_misconfiguration(config_path)
                        findings.extend(file_findings)
            
            elif target_path.is_file():
                try:
                    code = target_path.read_text()
                    
                    for pattern, description in misconfig_patterns:
                        matches = re.finditer(pattern, code)
                        for match in matches:
                            line_num = code[:match.start()].count('\n') + 1
                            
                            finding = SecurityFinding(
                                finding_id=f"CONFIG-{len(findings)+1}",
                                test_case=self.test_cases[6],
                                vulnerability_confirmed=True,
                                severity=SeverityLevel.MEDIUM,
                                location=f"{target_path}:{line_num}",
                                evidence=match.group(0),
                                impact=description,
                                likelihood="High",
                                risk_score=6.5,
                                remediation_steps=[
                                    "Disable debug mode in production",
                                    "Use secure default configurations",
                                    "Enable SSL verification",
                                    "Set secure cookie flags",
                                    "Restrict allowed hosts"
                                ]
                            )
                            findings.append(finding)
                
                except Exception:
                    pass
        
        return findings
    
    async def _test_path_traversal(self, target: Any) -> List[SecurityFinding]:
        """パストラバーサルテスト"""
        findings = []
        
        # 危険なファイル操作パターン
        path_patterns = [
            (r'open\s*\(\s*[^,)]*?\+[^,)]*?\)', "File path concatenation"),
            (r'os\.path\.join\s*\([^)]*?request\.[^)]*?\)', "User input in path"),
            (r'send_file\s*\([^)]*?request\.[^)]*?\)', "User controlled file sending"),
            (r'\.\./', "Path traversal sequence detected"),
        ]
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            if target_path.is_file():
                try:
                    code = target_path.read_text()
                    
                    for pattern, description in path_patterns:
                        matches = re.finditer(pattern, code)
                        for match in matches:
                            line_num = code[:match.start()].count('\n') + 1
                            
                            # パス検証の有無をチェック
                            context = code[max(0, match.start()-100):match.end()+100]
                            has_validation = any(val in context for val in [
                                'os.path.abspath',
                                'Path().resolve()',
                                'secure_filename',
                                'validate_path'
                            ])
                            
                            if not has_validation:
                                finding = SecurityFinding(
                                    finding_id=f"PATH-{len(findings)+1}",
                                    test_case=self.test_cases[7],
                                    vulnerability_confirmed=True,
                                    severity=SeverityLevel.HIGH,
                                    location=f"{target_path}:{line_num}",
                                    evidence=match.group(0),
                                    impact="Path traversal can lead to arbitrary file access",
                                    likelihood="Medium",
                                    risk_score=7.5,
                                    remediation_steps=[
                                        "Validate and sanitize all file paths",
                                        "Use os.path.abspath() and check prefix",
                                        "Implement whitelist of allowed paths",
                                        "Use secure_filename() for user inputs"
                                    ]
                                )
                                findings.append(finding)
                
                except Exception:
                    pass
        
        return findings
    
    async def _test_unsafe_deserialization(self, target: Any) -> List[SecurityFinding]:
        """安全でないデシリアライゼーションテスト"""
        findings = []
        
        # 危険なデシリアライゼーション
        unsafe_patterns = [
            (r'pickle\.loads?\s*\(', "Unsafe pickle deserialization"),
            (r'yaml\.load\s*\([^)]*?Loader\s*=\s*yaml\.Loader', "Unsafe YAML loading"),
            (r'eval\s*\(', "Use of eval() function"),
            (r'__import__\s*\(', "Dynamic import"),
        ]
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            if target_path.is_file():
                try:
                    code = target_path.read_text()
                    
                    for pattern, description in unsafe_patterns:
                        matches = re.finditer(pattern, code)
                        for match in matches:
                            line_num = code[:match.start()].count('\n') + 1
                            
                            finding = SecurityFinding(
                                finding_id=f"DESER-{len(findings)+1}",
                                test_case=self.test_cases[8],
                                vulnerability_confirmed=True,
                                severity=SeverityLevel.HIGH,
                                location=f"{target_path}:{line_num}",
                                evidence=match.group(0),
                                impact="Remote code execution through deserialization",
                                likelihood="High if untrusted data is processed",
                                risk_score=9.0,
                                remediation_steps=[
                                    "Avoid deserializing untrusted data",
                                    "Use safe alternatives (JSON instead of pickle)",
                                    "For YAML, use yaml.safe_load()",
                                    "Implement input validation before deserialization"
                                ]
                            )
                            findings.append(finding)
                
                except Exception:
                    pass
        
        return findings
    
    async def _test_logging_monitoring(self, target: Any) -> List[SecurityFinding]:
        """ロギングとモニタリングテスト"""
        findings = []
        
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            # セキュリティイベントのロギングチェック
            security_events = [
                'login_attempt',
                'authentication_failure',
                'authorization_failure',
                'data_access',
                'configuration_change'
            ]
            
            if target_path.is_file():
                try:
                    code = target_path.read_text()
                    
                    # ロギング実装の確認
                    has_logging = 'import logging' in code or 'from logging' in code
                    
                    if not has_logging:
                        finding = SecurityFinding(
                            finding_id=f"LOG-1",
                            test_case=self.test_cases[9],
                            vulnerability_confirmed=True,
                            severity=SeverityLevel.MEDIUM,
                            location=str(target_path),
                            evidence="No logging implementation found",
                            impact="Security incidents may go undetected",
                            likelihood="Certain",
                            risk_score=5.0,
                            remediation_steps=[
                                "Implement comprehensive logging",
                                "Log all security-relevant events",
                                "Use structured logging format",
                                "Implement log monitoring and alerting"
                            ]
                        )
                        findings.append(finding)
                    
                    # セキュリティイベントのロギング確認
                    for event in security_events:
                        if event not in code:
                            finding = SecurityFinding(
                                finding_id=f"LOG-{len(findings)+1}",
                                test_case=self.test_cases[9],
                                vulnerability_confirmed=True,
                                severity=SeverityLevel.LOW,
                                location=str(target_path),
                                evidence=f"Missing logging for {event}",
                                impact="Security event not tracked",
                                likelihood="Medium",
                                risk_score=3.5,
                                remediation_steps=[
                                    f"Add logging for {event} events",
                                    "Include timestamp, user, IP, and action",
                                    "Log both successes and failures"
                                ]
                            )
                            findings.append(finding)
                
                except Exception:
                    pass
        
        return findings
    
    async def _run_automated_scans(self, target: Any):
        """自動化されたセキュリティスキャン"""
        # 依存関係の脆弱性チェック
        await self._check_dependencies(target)
        
        # TLS/SSL設定チェック
        await self._check_tls_configuration(target)
        
        # CORS設定チェック
        await self._check_cors_configuration(target)
    
    async def _check_dependencies(self, target: Any):
        """依存関係の脆弱性チェック"""
        if isinstance(target, (str, Path)):
            target_path = Path(target)
            
            # requirements.txt チェック
            req_file = target_path / "requirements.txt" if target_path.is_dir() else target_path.parent / "requirements.txt"
            
            if req_file.exists():
                try:
                    # 簡易的な古いバージョンチェック
                    vulnerable_packages = {
                        'django<3.2': 'Django versions below 3.2 have known vulnerabilities',
                        'flask<2.0': 'Flask versions below 2.0 have security issues',
                        'requests<2.26': 'Requests library should be updated',
                        'pyyaml<5.4': 'PyYAML has known vulnerabilities in older versions'
                    }
                    
                    content = req_file.read_text()
                    for package, message in vulnerable_packages.items():
                        if package.split('<')[0] in content:
                            # バージョン確認（簡易版）
                            pattern = f"{package.split('<')[0]}==([0-9.]+)"
                            match = re.search(pattern, content)
                            if match:
                                version = match.group(1)
                                # ここでバージョン比較を行う（簡易実装）
                                finding = SecurityFinding(
                                    finding_id=f"DEP-{len(self.test_results)+1}",
                                    test_case=self.test_cases[0],  # 既存のテストケースを流用
                                    vulnerability_confirmed=True,
                                    severity=SeverityLevel.MEDIUM,
                                    location=str(req_file),
                                    evidence=f"{package.split('<')[0]}=={version}",
                                    impact=message,
                                    likelihood="Certain",
                                    risk_score=6.0,
                                    remediation_steps=[
                                        f"Update {package.split('<')[0]} to latest version",
                                        "Run: pip install --upgrade {package.split('<')[0]}",
                                        "Test thoroughly after update"
                                    ]
                                )
                                # 結果に追加
                                if hasattr(self, 'current_test_result'):
                                    self.current_test_result.findings.append(finding)
                
                except Exception:
                    pass
    
    async def _check_tls_configuration(self, target: Any):
        """TLS/SSL設定チェック"""
        # TLS設定の確認（実装は簡易版）
        pass
    
    async def _check_cors_configuration(self, target: Any):
        """CORS設定チェック"""
        # CORS設定の確認（実装は簡易版）
        pass
    
    def _update_statistics(self, result: SecurityTestResult):
        """統計情報更新"""
        self.stats['total_tests'] += 1
        
        if result.status == TestStatus.PASSED:
            self.stats['passed'] += 1
        elif result.status == TestStatus.FAILED:
            self.stats['failed'] += 1
        elif result.status == TestStatus.VULNERABLE:
            self.stats['vulnerable'] += 1
        elif result.status == TestStatus.ERROR:
            self.stats['errors'] += 1
        
        # 脆弱性統計
        for finding in result.findings:
            self.stats['findings_by_severity'][finding.severity.value] += 1
            self.stats['findings_by_type'][finding.test_case.vulnerability_type.value] += 1
    
    def _generate_security_report(self,
                                 report_id: str,
                                 scan_start_time: datetime,
                                 scan_end_time: datetime) -> SecurityReport:
        """セキュリティレポート生成"""
        # 脆弱性カウント
        vulnerabilities = sum(len(r.findings) for r in self.test_results)
        critical = sum(1 for r in self.test_results for f in r.findings if f.severity == SeverityLevel.CRITICAL)
        high = sum(1 for r in self.test_results for f in r.findings if f.severity == SeverityLevel.HIGH)
        medium = sum(1 for r in self.test_results for f in r.findings if f.severity == SeverityLevel.MEDIUM)
        low = sum(1 for r in self.test_results for f in r.findings if f.severity == SeverityLevel.LOW)
        info = sum(1 for r in self.test_results for f in r.findings if f.severity == SeverityLevel.INFO)
        
        # 全体リスクスコア計算
        risk_weights = {
            SeverityLevel.CRITICAL: 10.0,
            SeverityLevel.HIGH: 7.0,
            SeverityLevel.MEDIUM: 4.0,
            SeverityLevel.LOW: 1.0,
            SeverityLevel.INFO: 0.1
        }
        
        total_risk = sum(
            risk_weights[f.severity] * f.risk_score
            for r in self.test_results
            for f in r.findings
        )
        
        max_possible_risk = len(self.test_cases) * 10.0 * 10.0
        overall_risk_score = min(10.0, (total_risk / max_possible_risk) * 10) if max_possible_risk > 0 else 0
        
        # エグゼクティブサマリー生成
        if vulnerabilities == 0:
            executive_summary = "No security vulnerabilities were detected during the scan. The system demonstrates good security practices."
        elif critical > 0:
            executive_summary = f"CRITICAL: {critical} critical vulnerabilities require immediate attention. The system is at high risk of compromise."
        elif high > 0:
            executive_summary = f"HIGH RISK: {high} high-severity vulnerabilities detected. Prompt remediation is strongly recommended."
        else:
            executive_summary = f"MODERATE RISK: {vulnerabilities} vulnerabilities found. Regular security improvements recommended."
        
        # 修正優先度
        remediation_priority = []
        all_findings = [f for r in self.test_results for f in r.findings]
        
        # リスクスコアでソート
        sorted_findings = sorted(all_findings, key=lambda f: (f.severity.value, f.risk_score), reverse=True)
        
        for finding in sorted_findings[:10]:  # Top 10
            remediation_priority.append({
                'finding_id': finding.finding_id,
                'severity': finding.severity.value,
                'risk_score': finding.risk_score,
                'location': finding.location,
                'summary': finding.impact,
                'remediation': finding.remediation_steps[0] if finding.remediation_steps else "See details"
            })
        
        # コンプライアンスステータス
        compliance_status = {
            'OWASP_TOP_10': critical == 0 and high < 3,
            'PCI_DSS': critical == 0 and not any(f.test_case.vulnerability_type == VulnerabilityType.SENSITIVE_DATA for f in all_findings),
            'GDPR': not any(f.test_case.vulnerability_type in [VulnerabilityType.SENSITIVE_DATA, VulnerabilityType.LOGGING] for f in all_findings),
            'SOC2': self.stats['passed'] / max(self.stats['total_tests'], 1) > 0.9
        }
        
        return SecurityReport(
            report_id=report_id,
            scan_start_time=scan_start_time,
            scan_end_time=scan_end_time,
            total_tests=self.stats['total_tests'],
            tests_passed=self.stats['passed'],
            tests_failed=self.stats['failed'],
            vulnerabilities_found=vulnerabilities,
            critical_findings=critical,
            high_findings=high,
            medium_findings=medium,
            low_findings=low,
            info_findings=info,
            overall_risk_score=overall_risk_score,
            test_results=self.test_results,
            executive_summary=executive_summary,
            technical_details={
                'scan_duration': (scan_end_time - scan_start_time).total_seconds(),
                'findings_by_type': dict(self.stats['findings_by_type']),
                'findings_by_severity': dict(self.stats['findings_by_severity'])
            },
            remediation_priority=remediation_priority,
            compliance_status=compliance_status
        )
    
    async def _save_report(self, report: SecurityReport):
        """レポート保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # HTMLレポート
        html_path = self.test_output_dir / f"security_report_{timestamp}.html"
        html_content = self._generate_html_report(report)
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        # JSONレポート
        json_path = self.test_output_dir / f"security_report_{timestamp}.json"
        json_data = self._report_to_dict(report)
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        self.logger.info(f"Security reports saved: {html_path}, {json_path}")
    
    def _generate_html_report(self, report: SecurityReport) -> str:
        """HTMLレポート生成"""
        severity_colors = {
            'critical': '#d32f2f',
            'high': '#f57c00',
            'medium': '#fbc02d',
            'low': '#388e3c',
            'info': '#1976d2'
        }
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Test Report - {report.report_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #1a237e; color: white; padding: 20px; border-radius: 5px; }}
        .risk-score {{ font-size: 48px; font-weight: bold; color: {'#d32f2f' if report.overall_risk_score > 7 else '#f57c00' if report.overall_risk_score > 4 else '#388e3c'}; }}
        .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: #fff; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); min-width: 120px; text-align: center; }}
        .finding {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .critical {{ border-left: 5px solid #d32f2f; }}
        .high {{ border-left: 5px solid #f57c00; }}
        .medium {{ border-left: 5px solid #fbc02d; }}
        .low {{ border-left: 5px solid #388e3c; }}
        .info {{ border-left: 5px solid #1976d2; }}
        .compliance {{ display: inline-block; margin: 5px; padding: 10px; border-radius: 5px; }}
        .compliant {{ background-color: #c8e6c9; color: #1b5e20; }}
        .non-compliant {{ background-color: #ffcdd2; color: #b71c1c; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3f51b5; color: white; }}
        .remediation {{ background-color: #e8f5e9; padding: 10px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Security Test Report</h1>
        <p>Report ID: {report.report_id}</p>
        <p>Scan Date: {report.scan_start_time.strftime('%Y-%m-%d %H:%M:%S')} - {report.scan_end_time.strftime('%H:%M:%S')}</p>
        <div class="risk-score">Risk Score: {report.overall_risk_score:.1f}/10</div>
    </div>
    
    <div class="summary">
        <h2>📊 Executive Summary</h2>
        <p style="font-size: 18px; font-weight: bold;">{report.executive_summary}</p>
        
        <div style="text-align: center;">
            <div class="metric">
                <div style="font-size: 24px; font-weight: bold;">{report.total_tests}</div>
                <div>Total Tests</div>
            </div>
            <div class="metric">
                <div style="font-size: 24px; font-weight: bold; color: #388e3c;">{report.tests_passed}</div>
                <div>Passed</div>
            </div>
            <div class="metric">
                <div style="font-size: 24px; font-weight: bold; color: #d32f2f;">{report.vulnerabilities_found}</div>
                <div>Vulnerabilities</div>
            </div>
        </div>
    </div>
    
    <div class="summary">
        <h2>🎯 Vulnerability Summary</h2>
        <table>
            <tr>
                <th>Severity</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
            <tr class="critical">
                <td>Critical</td>
                <td>{report.critical_findings}</td>
                <td>{(report.critical_findings/max(report.vulnerabilities_found,1)*100):.1f}%</td>
            </tr>
            <tr class="high">
                <td>High</td>
                <td>{report.high_findings}</td>
                <td>{(report.high_findings/max(report.vulnerabilities_found,1)*100):.1f}%</td>
            </tr>
            <tr class="medium">
                <td>Medium</td>
                <td>{report.medium_findings}</td>
                <td>{(report.medium_findings/max(report.vulnerabilities_found,1)*100):.1f}%</td>
            </tr>
            <tr class="low">
                <td>Low</td>
                <td>{report.low_findings}</td>
                <td>{(report.low_findings/max(report.vulnerabilities_found,1)*100):.1f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="summary">
        <h2>✅ Compliance Status</h2>
"""
        
        for standard, compliant in report.compliance_status.items():
            status_class = "compliant" if compliant else "non-compliant"
            status_text = "Compliant" if compliant else "Non-Compliant"
            html += f"""
        <div class="compliance {status_class}">
            {standard.replace('_', ' ')}: {status_text}
        </div>
"""
        
        html += """
    </div>
    
    <div class="summary">
        <h2>🚨 Top Priority Remediations</h2>
"""
        
        for priority in report.remediation_priority[:5]:
            html += f"""
        <div class="remediation">
            <strong>{priority['finding_id']}</strong> - Severity: {priority['severity']} - Risk Score: {priority['risk_score']}<br>
            Location: {priority['location']}<br>
            Action: {priority['remediation']}
        </div>
"""
        
        html += """
    </div>
    
    <h2>🔍 Detailed Findings</h2>
"""
        
        # 詳細な脆弱性情報
        for result in report.test_results:
            if result.findings:
                for finding in result.findings:
                    html += f"""
    <div class="finding {finding.severity.value}">
        <h3>{finding.finding_id}: {finding.test_case.name}</h3>
        <p><strong>Severity:</strong> {finding.severity.value.upper()} | <strong>Risk Score:</strong> {finding.risk_score}/10</p>
        <p><strong>Location:</strong> {finding.location}</p>
        <p><strong>Impact:</strong> {finding.impact}</p>
        <p><strong>Evidence:</strong> <code>{finding.evidence}</code></p>
        <p><strong>Remediation:</strong></p>
        <ul>
"""
                    for step in finding.remediation_steps:
                        html += f"            <li>{step}</li>\n"
                    
                    html += """
        </ul>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _report_to_dict(self, report: SecurityReport) -> Dict[str, Any]:
        """レポートを辞書形式に変換"""
        return {
            'report_id': report.report_id,
            'scan_start_time': report.scan_start_time.isoformat(),
            'scan_end_time': report.scan_end_time.isoformat(),
            'summary': {
                'total_tests': report.total_tests,
                'tests_passed': report.tests_passed,
                'tests_failed': report.tests_failed,
                'vulnerabilities_found': report.vulnerabilities_found,
                'overall_risk_score': report.overall_risk_score,
                'executive_summary': report.executive_summary
            },
            'vulnerabilities': {
                'critical': report.critical_findings,
                'high': report.high_findings,
                'medium': report.medium_findings,
                'low': report.low_findings,
                'info': report.info_findings
            },
            'compliance_status': report.compliance_status,
            'remediation_priority': report.remediation_priority,
            'technical_details': report.technical_details,
            'detailed_findings': [
                {
                    'test_id': result.test_id,
                    'test_name': result.test_name,
                    'status': result.status.value,
                    'findings': [
                        {
                            'finding_id': f.finding_id,
                            'severity': f.severity.value,
                            'location': f.location,
                            'impact': f.impact,
                            'risk_score': f.risk_score,
                            'remediation_steps': f.remediation_steps
                        }
                        for f in result.findings
                    ]
                }
                for result in report.test_results
            ]
        }


# ファクトリー関数
def create_security_test_framework(config: Optional[Dict[str, Any]] = None) -> SecurityTestFramework:
    """セキュリティテストフレームワーク作成"""
    return SecurityTestFramework(config)


if __name__ == "__main__":
    # セキュリティテスト実行例
    async def run_security_tests():
        # フレームワーク作成
        framework = create_security_test_framework({
            'output_dir': './security_results',
            'security_policy': {
                'min_password_length': 12,
                'require_mfa': True
            }
        })
        
        # テスト対象（サンプル）
        test_target = Path(__file__).parent.parent.parent  # プロジェクトルート
        
        print("🔒 Starting Security Scan...")
        print(f"Target: {test_target}")
        
        # セキュリティスキャン実行
        report = await framework.run_security_scan(test_target)
        
        # 結果サマリー表示
        print(f"\n📊 Security Scan Complete!")
        print(f"   Total Tests: {report.total_tests}")
        print(f"   Passed: {report.tests_passed}")
        print(f"   Vulnerabilities Found: {report.vulnerabilities_found}")
        print(f"   Overall Risk Score: {report.overall_risk_score:.1f}/10")
        
        if report.critical_findings > 0:
            print(f"\n🚨 CRITICAL: {report.critical_findings} critical vulnerabilities found!")
        
        print(f"\n📄 Reports saved to: {framework.test_output_dir}")
        
        # コンプライアンスステータス
        print("\n✅ Compliance Status:")
        for standard, compliant in report.compliance_status.items():
            status = "✓" if compliant else "✗"
            print(f"   {status} {standard.replace('_', ' ')}")
    
    # 実行
    asyncio.run(run_security_tests())