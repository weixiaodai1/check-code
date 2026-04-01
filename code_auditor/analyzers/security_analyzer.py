"""
安全性分析器
检查代码中的安全漏洞和潜在风险
"""

from typing import List, Dict, Set, Any
import re
from .base_analyzer import BaseAnalyzer
from .custom_rules_analyzer import FixSuggestionGenerator
from ..models import CheckResult, CheckCategory, SeverityLevel


class SecurityAnalyzer(BaseAnalyzer):
    """安全性分析器"""

    # 危险函数/模式列表
    DANGEROUS_PATTERNS = {
        'eval': (r'\beval\s*\(', SeverityLevel.CRITICAL, "使用eval()函数可能导致代码注入"),
        'exec': (r'\bexec\s*\(', SeverityLevel.CRITICAL, "使用exec()函数可能导致代码注入"),
        'pickle': (r'pickle\.loads|pickle\.load', SeverityLevel.HIGH, "使用pickle可能导致反序列化攻击"),
        'yaml_load': (r'yaml\.load\s*\(', SeverityLevel.HIGH, "yaml.load()默认不安全，可能导致代码执行"),
        'subprocess_shell': (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', SeverityLevel.HIGH, "shell=True可能导致命令注入"),
        'os_system': (r'os\.system\s*\(', SeverityLevel.HIGH, "os.system()可能导致命令注入"),
        'os_popen': (r'os\.popen\s*\(', SeverityLevel.HIGH, "os.popen()可能导致命令注入"),
        'sql_raw': (r'execute\s*\([^)]*\+[^)]*\)', SeverityLevel.CRITICAL, "SQL拼接可能导致SQL注入"),
        'command_injection': (r'\|\s*os\.', SeverityLevel.CRITICAL, "管道命令可能导致命令注入"),
        'hardcoded_password': (r'["\'][^"\']*(?:password|passwd|pwd|secret|api_key|apikey|token)[^"\']*["\']\s*[=:]\s*["\']', SeverityLevel.HIGH, "硬编码密码/密钥存在安全风险"),
        'insecure_hash': (r'md5\s*\(', SeverityLevel.MEDIUM, "MD5不适合用于安全目的"),
        'weak_crypto': (r'DES\.new|RC4', SeverityLevel.HIGH, "使用弱加密算法"),
        'ssl_verify': (r'verify\s*=\s*False', SeverityLevel.HIGH, "SSL验证被禁用，存在安全风险"),
        'xss_raw_html': (r'dangerouslySetInnerHTML', SeverityLevel.HIGH, "直接设置HTML可能导致XSS攻击"),
        'path_traversal': (r'\.\.[/\\]', SeverityLevel.MEDIUM, "检测到路径遍历模式"),
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._file_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rb', '.php']
        self._enable_sql_check = self.config.get('check_sql_injection', True)
        self._enable_xss_check = self.config.get('check_xss', True)
        self._enable_cmd_check = self.config.get('check_command_injection', True)

    @property
    def name(self) -> str:
        return "安全性分析器"

    @property
    def description(self) -> str:
        return "检查代码中的安全漏洞和潜在风险"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.SECURITY

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """执行安全性分析"""
        self.results = []

        # 基础安全检查
        self._check_dangerous_functions(file_path, content)
        self._check_sql_injection(file_path, content)
        self._check_xss_vulnerabilities(file_path, content)
        self._check_command_injection(file_path, content)
        self._check_credential_exposure(file_path, content)
        self._check_insecure_randomness(file_path, content)
        self._check_weak_cryptography(file_path, content)
        self._check_path_traversal(file_path, content)
        self._check_insecure_deserialization(file_path, content)
        self._check_xxe_vulnerability(file_path, content)
        self._check_csrf_protection(file_path, content)
        self._check_cors_configuration(file_path, content)

        return self.results

    def _check_dangerous_functions(self, file_path: str, content: str) -> None:
        """检查危险函数的使用"""
        for name, (pattern, severity, description) in self.DANGEROUS_PATTERNS.items():
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                # 使用增强的修复建议
                check_id = f"SEC001-{name}"
                enhanced_suggestion = FixSuggestionGenerator.generate_contextual_fix(
                    check_id, content, line_num
                )
                basic_suggestion = self._get_fix_suggestion(name)
                
                self.results.append(self._create_result(
                    check_id=check_id,
                    check_name=f"使用危险函数: {name}",
                    message=f"行 {line_num}: {description}",
                    severity=severity,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion=enhanced_suggestion if enhanced_suggestion != basic_suggestion else basic_suggestion,
                    rule_id=f"dangerous-{name}"
                ))

    def _get_fix_suggestion(self, issue: str) -> str:
        """获取修复建议"""
        suggestions = {
            'eval': "避免使用eval()，考虑使用ast.literal_eval()解析字面量或重新设计代码逻辑",
            'exec': "避免使用exec()，考虑使用其他安全的代码执行方式",
            'pickle': "使用JSON代替pickle进行数据交换，或使用加密签名验证pickle数据",
            'yaml_load': "使用yaml.safe_load()代替yaml.load()",
            'subprocess_shell': "使用shell=False并传递参数列表，或对输入进行严格验证",
            'os_system': "使用subprocess模块并避免shell=True",
            'os_popen': "使用subprocess.Popen并避免shell=True",
            'sql_raw': "使用参数化查询或ORM框架",
            'hardcoded_password': "使用环境变量或安全的密钥管理服务",
            'insecure_hash': "使用hashlib.sha256()或hashlib.sha512()",
            'weak_crypto': "使用现代加密算法如AES-256",
            'ssl_verify': "启用SSL验证，或使用自定义CA证书",
            'xss_raw_html': "使用文本插值或HTML转义库",
            'path_traversal': "验证和规范化用户输入的路径"
        }
        return suggestions.get(issue, "请审查此代码并确保安全的实现方式")

    def _check_sql_injection(self, file_path: str, content: str) -> None:
        """检查SQL注入漏洞"""
        # SQL拼接模式
        sql_patterns = [
            (r'execute\s*\([^)]*\+[^)]*\)', "SQL查询使用字符串拼接"),
            (r'cursor\.execute\s*\([^)]*%[^)]*%[^)]*\)', "SQL查询使用%s格式化"),
            (r'cursor\.execute\s*\([^)]*f["\']', "SQL查询使用f-string"),
            (r'cursor\.execute\s*\([^)]*\.format\s*\(', "SQL查询使用format()"),
            (r'\$\{?[a-zA-Z_][a-zA-Z0-9_]*\}?', "模板字符串中直接插入变量"),  # JS
        ]

        for pattern, description in sql_patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                enhanced_suggestion = FixSuggestionGenerator.generate_contextual_fix(
                    'SEC010', content, line_num
                )
                self.results.append(self._create_result(
                    check_id="SEC010",
                    check_name="潜在的SQL注入风险",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.CRITICAL,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion=enhanced_suggestion if enhanced_suggestion else "使用参数化查询（Prepared Statements）或ORM框架",
                    rule_id="sql-injection"
                ))

    def _check_xss_vulnerabilities(self, file_path: str, content: str) -> None:
        """检查XSS跨站脚本漏洞"""
        xss_patterns = [
            (r'innerHTML\s*=', "直接设置innerHTML可能导致XSS"),
            (r'document\.write\s*\(', "document.write可能导致XSS"),
            (r'eval\s*\([^)]*input|eval\s*\([^)]*params', "eval用户输入可能导致XSS"),
            (r'render\s*\(.*innerHTML', "使用innerHTML渲染可能导致XSS"),
            (r'django\.utils\.html\.escape', "使用escape但可能不完整"),
        ]

        for pattern, description in xss_patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                enhanced_suggestion = FixSuggestionGenerator.generate_contextual_fix(
                    'SEC011', content, line_num
                )
                self.results.append(self._create_result(
                    check_id="SEC011",
                    check_name="潜在的XSS风险",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion=enhanced_suggestion if enhanced_suggestion else "对用户输入进行HTML转义，使用安全的DOM操作API",
                    rule_id="xss-vulnerability"
                ))

    def _check_command_injection(self, file_path: str, content: str) -> None:
        """检查命令注入漏洞"""
        cmd_patterns = [
            (r'subprocess\.[^:]+\([^)]*shell\s*=\s*True', "subprocess使用shell=True"),
            (r'os\.system\s*\(', "os.system()调用"),
            (r'os\.popen\s*\(', "os.popen()调用"),
            (r'\bspawn.*shell\s*=\s*True', "spawn shell=True"),
            (r'commands\.getstatusoutput', "commands模块使用"),
            (r'\|\s*sh\b', "管道到shell脚本"),
        ]

        for pattern, description in cmd_patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                enhanced_suggestion = FixSuggestionGenerator.generate_contextual_fix(
                    'SEC012', content, line_num
                )
                self.results.append(self._create_result(
                    check_id="SEC012",
                    check_name="潜在的命令注入风险",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.CRITICAL,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion=enhanced_suggestion if enhanced_suggestion else "避免shell=True，使用参数列表而非字符串",
                    rule_id="command-injection"
                ))

    def _check_credential_exposure(self, file_path: str, content: str) -> None:
        """检查凭证泄露"""
        # 敏感关键词模式
        sensitive_patterns = [
            (r'["\'][^"\']*(?:password|passwd|pwd|secret|api_key|api_key|apikey|token|auth_token|access_token|private_key)[^"\']*["\']\s*[=:]\s*["\'][^"\']+["\']',
             "检测到硬编码的敏感信息"),
            (r'(?:github|aws|azure|gcp|stripe|sendgrid|mailgun)[_-]?(?:key|token|secret)',
             "检测到可能的API密钥"),
            (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
             "检测到私钥"),
        ]

        for pattern, description in sensitive_patterns:
            matches = self._find_pattern(content, pattern, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                # 排除注释中的内容
                line = self._get_line_content(content, line_num)
                if not line.strip().startswith('#'):
                    self.results.append(self._create_result(
                        check_id="SEC013",
                        check_name="敏感信息泄露风险",
                        message=f"行 {line_num}: {description}",
                        severity=SeverityLevel.CRITICAL,
                        file_path=file_path,
                        line_number=line_num,
                        snippet="[敏感信息已隐藏]",
                        suggestion="将敏感信息移至环境变量或安全的密钥管理服务",
                        rule_id="credential-exposure"
                    ))

    def _check_insecure_randomness(self, file_path: str, content: str) -> None:
        """检查不安全的随机数"""
        insecure_random = [
            (r'random\.random\s*\(', "random模块不是加密安全的"),
            (r'random\.randint\s*\(', "random模块不是加密安全的"),
            (r'random\.choice\s*\(', "random模块不是加密安全的"),
        ]

        for pattern, description in insecure_random:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="SEC014",
                    check_name="不安全的随机数生成",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion="用于安全目的时使用secrets模块或os.urandom()",
                    rule_id="insecure-random"
                ))

    def _check_weak_cryptography(self, file_path: str, content: str) -> None:
        """检查弱加密算法"""
        weak_crypto = [
            (r'md5\s*\(', "MD5是已破解的哈希算法"),
            (r'sha1\s*\(', "SHA1是已弃用的哈希算法"),
            (r'DES\.new\s*\(', "DES是不安全的加密算法"),
            (r'RC4\s*\(', "RC4是已破解的加密算法"),
            (r'Cipher\.\w+MODE_ECB', "ECB模式是不安全的"),
        ]

        for pattern, description in weak_crypto:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="SEC015",
                    check_name="使用弱加密算法",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion="使用SHA-256/SHA-512进行哈希，AES进行加密",
                    rule_id="weak-cryptography"
                ))

    def _check_path_traversal(self, file_path: str, content: str) -> None:
        """检查路径遍历漏洞"""
        traversal_patterns = [
            (r'\.\.[/\\]', "检测到路径遍历模式"),
            (r'open\s*\([^)]*%s', "文件路径使用格式化可能存在路径遍历"),
            (r'os\.path\.join\s*\([^)]*\+[^)]*\)', "路径拼接可能存在安全问题"),
        ]

        for pattern, description in traversal_patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line = self._get_line_content(content, line_num)
                # 排除注释
                if not line.strip().startswith('#'):
                    self.results.append(self._create_result(
                        check_id="SEC016",
                        check_name="路径遍历风险",
                        message=f"行 {line_num}: {description}",
                        severity=SeverityLevel.MEDIUM,
                        file_path=file_path,
                        line_number=line_num,
                        snippet=self._get_line_content(content, line_num),
                        suggestion="对用户提供的路径进行验证和规范化",
                        rule_id="path-traversal"
                    ))

    def _check_insecure_deserialization(self, file_path: str, content: str) -> None:
        """检查不安全的反序列化"""
        insecure_deser = [
            (r'pickle\.load\s*\(', "pickle反序列化存在安全风险"),
            (r'pickle\.loads\s*\(', "pickle反序列化存在安全风险"),
            (r'yaml\.load\s*\([^)]*Loader\s*=\s*yaml\.Loader\)', "不安全的YAML加载"),
            (r'yaml\.unsafe_load\s*\(', "YAML unsafe_load存在安全风险"),
            (r'marshal\.load\s*\(', "marshal反序列化存在安全风险"),
            (r'jsonpickle\.decode\s*\(', "jsonpickle可能存在安全风险"),
        ]

        for pattern, description in insecure_deser:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="SEC017",
                    check_name="不安全的反序列化",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion="使用JSON代替，或验证/签名反序列化数据",
                    rule_id="insecure-deserialization"
                ))

    def _check_xxe_vulnerability(self, file_path: str, content: str) -> None:
        """检查XXE漏洞"""
        xxe_patterns = [
            (r'ET\.parse\s*\([^)]*parser\s*=\s*None', "XML解析可能存在XXE"),
            (r'defusedxml', "检测到defusedxml，但使用方式可能不安全"),
        ]

        for pattern, description in xxe_patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="SEC018",
                    check_name="可能的XXE漏洞",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion="禁用外部实体，使用安全的XML解析器配置",
                    rule_id="xxe-vulnerability"
                ))

    def _check_csrf_protection(self, file_path: str, content: str) -> None:
        """检查CSRF保护"""
        # 检测表单是否缺少CSRF令牌
        if 'form' in content.lower() and 'action=' in content:
            if 'csrf' not in content.lower() and 'token' not in content.lower():
                self.results.append(self._create_result(
                    check_id="SEC019",
                    check_name="可能缺少CSRF保护",
                    message="检测到表单但未发现CSRF保护机制",
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    suggestion="为所有表单添加CSRF令牌验证",
                    rule_id="csrf-protection"
                ))

    def _check_cors_configuration(self, file_path: str, content: str) -> None:
        """检查CORS配置"""
        # 检测过于宽松的CORS配置
        cors_patterns = [
            (r'Access-Control-Allow-Origin\s*:\s*\*', "CORS允许所有来源"),
            (r'allowedOrigins\s*=\s*\["\*"\]', "CORS允许所有来源"),
        ]

        for pattern, description in cors_patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="SEC020",
                    check_name="CORS配置过于宽松",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion="限制允许的来源，避免使用通配符*",
                    rule_id="insecure-cors"
                ))
