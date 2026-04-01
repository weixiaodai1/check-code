"""
最佳实践分析器
检查代码是否遵循业界最佳实践和编码规范
"""

from typing import List, Dict, Set
import re
from .base_analyzer import BaseAnalyzer
from ..models import CheckResult, CheckCategory, SeverityLevel


class BestPracticesAnalyzer(BaseAnalyzer):
    """最佳实践分析器"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._file_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs']
        self._language = self.config.get('language', 'python')

    @property
    def name(self) -> str:
        return "最佳实践分析器"

    @property
    def description(self) -> str:
        return "检查代码是否遵循业界最佳实践和编码规范"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.BEST_PRACTICES

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """执行最佳实践分析"""
        self.results = []

        # 根据语言选择检查项
        if self._detect_language(file_path):
            self._language = self._detect_language(file_path)

        # 通用最佳实践检查
        self._check_error_handling(file_path, content)
        self._check_resource_management(file_path, content)
        self._check_type_hints(file_path, content)
        self._check_documentation(file_path, content)
        self._check_imports(file_path, content)
        self._check_constants(file_path, content)
        self._check_mutable_defaults(file_path, content)
        self._check_comprehension_style(file_path, content)

        # 语言特定检查
        if self._language == 'python':
            self._check_python_specific(file_path, content)
        elif self._language in ['javascript', 'typescript']:
            self._check_js_specific(file_path, content)

        return self.results

    def _detect_language(self, file_path: str) -> str:
        """检测编程语言"""
        ext = file_path.split('.')[-1].lower()
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'java': 'java',
            'go': 'go',
            'rs': 'rust'
        }
        return lang_map.get(ext, 'unknown')

    def _check_error_handling(self, file_path: str, content: str) -> None:
        """检查错误处理"""
        # 检测裸露的except语句
        bare_except = re.finditer(r'except\s*:', content)
        for match in bare_except:
            line_num = content[:match.start()].count('\n') + 1
            self.results.append(self._create_result(
                check_id="BP001",
                check_name="使用裸except子句",
                message=f"行 {line_num}: 使用了 except: 而不是 except Exception:",
                severity=SeverityLevel.HIGH,
                file_path=file_path,
                line_number=line_num,
                snippet=self._get_line_content(content, line_num),
                suggestion="明确指定要捕获的异常类型，避免捕获 KeyboardInterrupt 等系统异常",
                rule_id="no-bare-except"
            ))

        # 检测捕获后又重新抛出相同的异常
        re_raise = re.finditer(r'except.*:\s*raise', content)
        for match in re_raise:
            line_num = content[:match.start()].count('\n') + 1
            line = self._get_line_content(content, line_num)
            if 'raise' in line and 'raise ' not in line.replace('raise', '', 1):
                self.results.append(self._create_result(
                    check_id="BP002",
                    check_name="异常重新抛出",
                    message=f"行 {line_num}: 检测到异常被捕获后直接重新抛出",
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="考虑使用 raise from 或让异常自然传播",
                    rule_id="reraise-exception"
                ))

    def _check_resource_management(self, file_path: str, content: str) -> None:
        """检查资源管理"""
        # Python: 检查没有使用with语句的文件操作
        if 'open(' in content and 'with open(' not in content:
            self.results.append(self._create_result(
                check_id="BP003",
                check_name="未使用上下文管理器",
                message="代码中存在未使用 with 语句的文件操作，可能导致资源泄漏",
                severity=SeverityLevel.MEDIUM,
                file_path=file_path,
                suggestion="使用 with open() 语句确保文件正确关闭",
                rule_id="use-context-manager"
            ))

        # 检查数据库连接未关闭
        if re.search(r'\.(connect|open|create)\s*\(', content):
            if 'with' not in content and 'finally' not in content:
                self.results.append(self._create_result(
                    check_id="BP004",
                    check_name="可能存在资源泄漏",
                    message="检测到连接/资源操作，可能未正确释放资源",
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    suggestion="确保所有资源在使用后被正确关闭，或使用上下文管理器",
                    rule_id="resource-cleanup"
                ))

    def _check_type_hints(self, file_path: str, content: str) -> None:
        """检查类型提示"""
        # 检查函数是否缺少返回类型注解
        func_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*(?::\s*(\w+))?\s*:'
        matches = re.finditer(func_pattern, content)

        for match in matches:
            func_name = match.group(1)
            return_type = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # 跳过私有函数和特殊方法
            if func_name.startswith('_') and func_name not in ['__init__', '__str__', '__repr__']:
                continue

            if not return_type and func_name not in ['__init__']:
                self.results.append(self._create_result(
                    check_id="BP005",
                    check_name="缺少返回类型注解",
                    message=f"函数 '{func_name}' 缺少返回类型注解",
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=f"def {func_name}(...):",
                    suggestion="添加类型注解以提高代码可读性和类型检查支持",
                    rule_id="add-return-type"
                ))

            # 检查参数是否缺少类型提示
            params_with_hints = re.search(
                rf'def\s+{func_name}\s*\([^)]*\):',
                content
            )
            if params_with_hints:
                param_str = params_with_hints.group(0)
                if '->' not in param_str and ': ' not in param_str:
                    self.results.append(self._create_result(
                        check_id="BP006",
                        check_name="参数缺少类型提示",
                        message=f"函数 '{func_name}' 的参数缺少类型提示",
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="为所有参数添加类型注解",
                        rule_id="add-parameter-types"
                    ))

    def _check_documentation(self, file_path: str, content: str) -> None:
        """检查文档字符串"""
        # 检查公共函数是否缺少文档字符串
        public_func_pattern = r'def\s+([a-z][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?::\s*\w+)?\s*:'
        matches = re.finditer(public_func_pattern, content)

        for match in matches:
            func_name = match.group(1)
            if func_name.startswith('_') and func_name not in ['__init__', '__call__']:
                continue

            # 检查后续是否有文档字符串
            start_pos = match.end()
            next_lines = content[start_pos:start_pos + 200]
            has_docstring = '"""' in next_lines or "'''" in next_lines

            if not has_docstring:
                line_num = content[:match.start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="BP007",
                    check_name="缺少文档字符串",
                    message=f"公共函数 '{func_name}' 缺少文档字符串",
                    severity=SeverityLevel.LOW,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=f"def {func_name}(...):",
                    suggestion="为所有公共函数添加描述性文档字符串，说明功能、参数和返回值",
                    rule_id="add-docstring"
                ))

    def _check_imports(self, file_path: str, content: str) -> None:
        """检查导入语句"""
        import re as regex

        # 检查import语句的位置
        import_lines = []
        code_lines = content.split('\n')
        first_code_line = 0

        for i, line in enumerate(code_lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                first_code_line = i
                break

        # 检查import是否在文件开头
        imports_at_top = True
        for i, line in enumerate(code_lines[:first_code_line]):
            if i < 5 and ('import ' in line or 'from ' in line):
                imports_at_top = True
                break
        else:
            # 在前几行之后还有import
            for line in code_lines[min(5, len(code_lines)):]:
                if 'import ' in line or 'from ' in line:
                    imports_at_top = False
                    break

        if not imports_at_top:
            self.results.append(self._create_result(
                check_id="BP008",
                check_name="导入语句位置不当",
                message="import语句应该放在文件顶部",
                severity=SeverityLevel.LOW,
                file_path=file_path,
                suggestion="将所有import语句移到文件顶部，标准库优先，然后是第三方库，最后是本地模块",
                rule_id="imports-at-top"
            ))

        # 检查是否有循环导入
        import_names = re.findall(r'from\s+(\S+)\s+import', content)
        for module in import_names:
            if module in [name.split('.')[0] for name in import_names]:
                self.results.append(self._create_result(
                    check_id="BP009",
                    check_name="可能存在循环导入",
                    message=f"可能存在循环导入问题：模块 '{module}'",
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    suggestion="重构代码以避免循环导入，可使用延迟导入或重新组织模块结构",
                    rule_id="no-circular-imports"
                ))

    def _check_constants(self, file_path: str, content: str) -> None:
        """检查常量定义"""
        # 查找大写命名但未定义为常量的变量
        uppercase_vars = re.findall(r'\b([A-Z][A-Z0-9_]+)\s*=', content)

        # 检查是否有大写变量但定义为普通变量
        for var in set(uppercase_vars):
            if not any(x in var for x in ['MAX', 'MIN', 'DEFAULT', 'CONFIG', 'SIZE']):
                continue

            pattern = rf'\b{var}\s*=\s*(?![A-Z_])'
            if re.search(pattern, content):
                line_num = content[:re.search(rf'\b{var}\s*=', content).start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="BP010",
                    check_name="常量未使用大写命名",
                    message=f"常量 '{var}' 使用了大写命名但可能被当作普通变量处理",
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="确保常量定义在大写的同时，也放在模块顶部或专门的常量文件中",
                    rule_id="constant-naming"
                ))

    def _check_mutable_defaults(self, file_path: str, content: str) -> None:
        """检查可变默认参数"""
        mutable_defaults = re.finditer(
            r'def\s+\w+\s*\([^)]*=\s*(\[\]|{}|\w+\s*\[)',
            content
        )

        for match in mutable_defaults:
            line_num = content[:match.start()].count('\n') + 1
            self.results.append(self._create_result(
                check_id="BP011",
                check_name="使用可变对象作为默认参数",
                message=f"行 {line_num}: 使用可变对象（列表或字典）作为函数默认参数",
                severity=SeverityLevel.CRITICAL,
                file_path=file_path,
                line_number=line_num,
                snippet=self._get_line_content(content, line_num),
                suggestion="使用 None 作为默认值，然后在函数内部初始化空列表/字典",
                rule_id="no-mutable-defaults"
            ))

    def _check_comprehension_style(self, file_path: str, content: str) -> None:
        """检查列表推导式使用"""
        # 检测过于复杂的列表推导式
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if 'for' in line and '[' in line:
                # 简单检查：包含多层嵌套for的推导式
                if line.count('for') > 2 or line.count('if') > 2:
                    self.results.append(self._create_result(
                        check_id="BP012",
                        check_name="过于复杂的列表推导式",
                        message=f"行 {line_num}: 检测到可能过于复杂的列表推导式",
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=line_num,
                        snippet=line.strip()[:80],
                        suggestion="考虑拆分为多个步骤或使用普通循环以提高可读性",
                        rule_id="complex-comprehension"
                    ))

    def _check_python_specific(self, file_path: str, content: str) -> None:
        """Python特定的最佳实践"""
        # 检查是否使用了print进行调试
        if re.search(r'\bprint\s*\(', content):
            # 排除__repr__中的print
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if re.search(r'\bprint\s*\(', line):
                    if not re.search(r'def __repr__', line):
                        self.results.append(self._create_result(
                            check_id="BP013",
                            check_name="使用print语句",
                            message=f"行 {line_num}: 检测到使用print进行输出",
                            severity=SeverityLevel.INFO,
                            file_path=file_path,
                            line_number=line_num,
                            suggestion="使用logging模块进行日志输出，便于控制日志级别",
                            rule_id="use-logging"
                        ))
                        break

        # 检查 == True/False 的使用
        if re.search(r'==\s*True|==\s*False', content):
            self.results.append(self._create_result(
                check_id="BP014",
                check_name="使用 == True/False 比较",
                message="检测到使用 == True 或 == False 进行比较",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="直接使用 if condition: 而不是 if condition == True:",
                rule_id="no-bool-comparison"
            ))

        # 检查 __all__ 定义
        if 'def ' in content and '__all__' not in content:
            self.results.append(self._create_result(
                check_id="BP015",
                check_name="缺少__all__定义",
                message="模块定义了函数但没有 __all__ 列表",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="定义 __all__ 列表以明确模块的公共API",
                rule_id="define-all"
            ))

    def _check_js_specific(self, file_path: str, content: str) -> None:
        """JavaScript/TypeScript特定的最佳实践"""
        # 检查是否使用了var而非let/const
        if re.search(r'\bvar\s+', content):
            self.results.append(self._create_result(
                check_id="BP016",
                check_name="使用var关键字",
                message="检测到使用var声明变量",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="使用let或const替代var，const用于不变的值，let用于会变化的值",
                rule_id="no-var"
            ))

        # 检查==和!=的使用
        if re.search(r'[^!]=[^=]|[^!]![^=]', content):
            self.results.append(self._create_result(
                check_id="BP017",
                check_name="使用松散相等比较",
                message="检测到使用 == 或 != 进行比较",
                severity=SeverityLevel.MEDIUM,
                file_path=file_path,
                suggestion="使用 === 或 !== 进行严格相等比较，避免类型转换带来的意外行为",
                rule_id="use-strict-equality"
            ))

        # 检查console.log
        if re.search(r'console\.log\s*\(', content):
            self.results.append(self._create_result(
                check_id="BP018",
                check_name="使用console.log",
                message="检测到使用console.log进行调试",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="使用专业的日志库如loglevel或winston，便于控制日志级别",
                rule_id="no-console-log"
            ))
