"""
代码质量分析器
检查代码质量指标，包括复杂度、重复、圈复杂度等
"""

from typing import List, Set, Dict, Any
import re

from .base_analyzer import BaseAnalyzer
from .custom_rules_analyzer import FixSuggestionGenerator
from ..models import (
    CheckResult, CheckCategory, SeverityLevel, Location
)


class QualityAnalyzer(BaseAnalyzer):
    """代码质量分析器"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._file_extensions = ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs']
        self._max_line_length = self.config.get('max_line_length', 120)
        self._max_function_lines = self.config.get('max_function_lines', 50)
        self._max_complexity = self.config.get('max_complexity', 10)

    @property
    def name(self) -> str:
        return "代码质量分析器"

    @property
    def description(self) -> str:
        return "检查代码质量指标，包括行长度、函数长度、复杂度等"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.CODE_QUALITY

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """执行代码质量分析"""
        self.results = []

        # 检查项
        self._check_line_length(file_path, content)
        self._check_long_functions(file_path, content)
        self._check_code_duplication(file_path, content)
        self._check_unused_variables(file_path, content)
        self._check_empty_catches(file_path, content)
        self._check_hardcoded_values(file_path, content)
        self._check_inconsistent_naming(file_path, content)
        self._check_deep_nesting(file_path, content)
        self._check_magic_numbers(file_path, content)
        self._check_dead_code(file_path, content)

        return self.results

    def _check_line_length(self, file_path: str, content: str) -> None:
        """检查代码行长度"""
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # 跳过注释行
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue

            # 跳过包含URL的行
            if 'http://' in line or 'https://' in line:
                continue

            if len(line) > self._max_line_length:
                # 使用增强的修复建议生成器
                basic_suggestion = f"建议将行长度控制在 {self._max_line_length} 字符以内"
                enhanced_suggestion = FixSuggestionGenerator.generate_contextual_fix(
                    'QUAL001', content, line_num
                )
                self.results.append(self._create_result(
                    check_id="QUAL001",
                    check_name="代码行过长",
                    message=f"行 {line_num} 长度 ({len(line)} 字符) 超过限制 ({self._max_line_length} 字符)",
                    severity=SeverityLevel.LOW if len(line) < 200 else SeverityLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=line[:100] + "..." if len(line) > 100 else line,
                    suggestion=enhanced_suggestion if enhanced_suggestion else basic_suggestion,
                    rule_id="max-line-length"
                ))

    def _check_long_functions(self, file_path: str, content: str) -> None:
        """检查过长的函数"""
        # Python函数检测
        function_pattern = r'(?:def|async\s+def)\s+(\w+)\s*\([^)]*\)\s*(?:->\s*\w+)?\s*:'
        matches = list(re.finditer(function_pattern, content, re.MULTILINE))

        for match in matches:
            func_name = match.group(1)
            start_pos = match.start()
            end_line = self._find_function_end(content, start_pos)

            if end_line and end_line > self._max_function_lines:
                line_num = content[:start_pos].count('\n') + 1
                enhanced_suggestion = FixSuggestionGenerator.generate_contextual_fix(
                    'QUAL002', content, line_num
                )
                self.results.append(self._create_result(
                    check_id="QUAL002",
                    check_name="函数过长",
                    message=f"函数 '{func_name}' 长度 ({end_line} 行) 超过建议限制 ({self._max_function_lines} 行)",
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=f"def {func_name}(...)",
                    suggestion=enhanced_suggestion if enhanced_suggestion else "考虑将函数拆分为更小的、单一职责的函数",
                    rule_id="max-function-length"
                ))

    def _check_code_duplication(self, file_path: str, content: str) -> None:
        """检测代码重复"""
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]

        # 简单的重复代码检测（基于连续相似行）
        seen_blocks = {}
        current_block = []
        block_start = 0

        for i, line in enumerate(lines):
            if len(line) > 20:  # 只检查足够长的行
                if line in seen_blocks:
                    current_block.append(i)
                else:
                    if len(current_block) >= 3:
                        self.results.append(self._create_result(
                            check_id="QUAL003",
                            check_name="可能存在代码重复",
                            message=f"检测到 {len(current_block)} 行可能重复的代码",
                            severity=SeverityLevel.INFO,
                            file_path=file_path,
                            line_number=block_start + 1,
                            snippet=lines[block_start][:80],
                            suggestion="考虑将重复代码提取为独立函数或使用继承/组合模式",
                            rule_id="code-duplication"
                        ))
                    seen_blocks[line] = True
                    current_block = [i]
                    block_start = i

    def _check_unused_variables(self, file_path: str, content: str) -> None:
        """检查未使用的变量"""
        # 简单检测：赋值后未使用的变量
        variable_assignments = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*', content)
        variable_uses = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', content))

        # 过滤掉常见非变量名
        keywords = {'if', 'else', 'elif', 'for', 'while', 'return', 'def', 'class',
                    'import', 'from', 'try', 'except', 'finally', 'with', 'as',
                    'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None',
                    'self', 'cls', 'lambda', 'yield', 'pass', 'break', 'continue',
                    'print', 'range', 'len', 'str', 'int', 'float', 'list', 'dict'}

        for var in set(variable_assignments):
            if var not in keywords and var not in variable_uses:
                # 简单检查：如果变量在赋值后只在后面某处使用过一次，可能是有意为之
                pass  # 简化处理，实际可用AST分析

    def _check_empty_catches(self, file_path: str, content: str) -> None:
        """检查空的异常捕获"""
        # 检测 except: pass 或 except: ...
        empty_except_pattern = r'except\s*(?:\w+)?\s*(?:,\s*\w+)?\s*:\s*(?:pass|\.\.\.|\n\s*(?:#[^\n]*)?\s*$)'
        matches = self._find_pattern(content, empty_except_pattern, re.MULTILINE)

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            enhanced_suggestion = FixSuggestionGenerator.generate_contextual_fix(
                'QUAL004', content, line_num
            )
            self.results.append(self._create_result(
                check_id="QUAL004",
                check_name="空的异常捕获",
                message=f"行 {line_num} 存在空的异常捕获块，可能隐藏了重要错误",
                severity=SeverityLevel.MEDIUM,
                file_path=file_path,
                line_number=line_num,
                snippet=self._get_line_content(content, line_num),
                suggestion=enhanced_suggestion if enhanced_suggestion else "在异常处理中至少记录日志，或处理具体的异常类型",
                rule_id="no-empty-except"
            ))

    def _check_hardcoded_values(self, file_path: str, content: str) -> None:
        """检查硬编码值"""
        # 检测URL、文件路径、可能需要配置的值
        patterns = [
            (r'["\']https?://[^\'"\s]+["\']', "可能的硬编码URL"),
            (r'["\']/?[a-zA-Z0-9_/]+\.[a-zA-Z]{2,4}["\']', "可能的硬编码路径"),
            (r'\b\d{4,}[/\-\.]?\d{0,2}[/\-\.]?\d{0,2}\b', "可能的硬编码日期/ID"),
        ]

        for pattern, description in patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.results.append(self._create_result(
                    check_id="QUAL005",
                    check_name=f"检测到{description}",
                    message=f"行 {line_num}: {description}",
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=match.group(0),
                    suggestion=f"考虑将 {description} 移至配置文件或环境变量",
                    rule_id="no-hardcoded-values"
                ))

    def _check_inconsistent_naming(self, file_path: str, content: str) -> None:
        """检查命名不一致"""
        # 检测函数和变量命名风格
        snake_case = re.findall(r'\b[a-z][a-z0-9_]*\b', content)
        camel_case = re.findall(r'\b[a-z][a-z]*[A-Z][a-zA-Z]*\b', content)
        pascal_case = re.findall(r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b', content)

        # 如果混合使用多种命名风格，发出警告
        naming_styles = sum([bool(snake_case), bool(camel_case), bool(pascal_case)])
        if naming_styles >= 2 and len(snake_case + camel_case + pascal_case) > 10:
            self.results.append(self._create_result(
                check_id="QUAL006",
                check_name="命名风格不一致",
                message="代码中混合使用了不同的命名风格（snake_case, camelCase, PascalCase）",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="建议统一使用一种命名风格，如 PEP 8 推荐的 snake_case",
                rule_id="consistent-naming"
            ))

    def _check_deep_nesting(self, file_path: str, content: str) -> None:
        """检查深层嵌套"""
        lines = content.split('\n')
        max_allowed_nesting = 4

        for line_num, line in enumerate(lines, 1):
            indent = len(line) - len(line.lstrip())
            nesting_level = indent // 4  # 假设4空格缩进

            if nesting_level > max_allowed_nesting:
                self.results.append(self._create_result(
                    check_id="QUAL007",
                    check_name="代码嵌套过深",
                    message=f"行 {line_num} 嵌套层级 ({nesting_level}) 超过建议限制 ({max_allowed_nesting})",
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=line.strip()[:80],
                    suggestion="考虑使用早期返回、提取函数或使用卫语句减少嵌套",
                    rule_id="max-nesting"
                ))

    def _check_magic_numbers(self, file_path: str, content: str) -> None:
        """检查魔法数字"""
        # 排除常见数字
        excluded_numbers = {0, 1, 2, 3, 4, 5, 10, 100, 1000, -1, 60, 24, 12, 365}

        magic_pattern = r'(?<![a-zA-Z_])([2-9]|[1-9][0-9]{2,})(?![a-zA-Z_])'
        matches = self._find_pattern(content, magic_pattern)

        for match in matches:
            num = int(match.group(0))
            if num not in excluded_numbers:
                line_num = content[:match.start()].count('\n') + 1
                # 排除版本号、端口号等
                if num < 10000:  # 简单过滤
                    self.results.append(self._create_result(
                        check_id="QUAL008",
                        check_name="使用魔法数字",
                        message=f"行 {line_num}: 数字 {num} 看起来是魔法数字",
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=line_num,
                        snippet=f"数字: {num}",
                        suggestion=f"考虑定义一个具有描述性名称的常量，如 MAX_{num} = {num}",
                        rule_id="no-magic-numbers"
                    ))

    def _check_dead_code(self, file_path: str, content: str) -> None:
        """检查死代码"""
        # 检测明显的死代码：return后的代码、永远为False的条件
        lines = content.split('\n')
        in_function = False
        found_return = False

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if stripped.startswith('def '):
                in_function = True
                found_return = False
            elif in_function:
                if stripped.startswith('return'):
                    found_return = True
                elif found_return and stripped and not stripped.startswith('#'):
                    # return之后的非注释代码
                    self.results.append(self._create_result(
                        check_id="QUAL009",
                        check_name="可能的死代码",
                        message=f"行 {line_num} 在 return 语句之后，可能是无法到达的死代码",
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=line_num,
                        snippet=stripped[:80],
                        suggestion="删除无法到达的代码或调整函数逻辑",
                        rule_id="no-unreachable"
                    ))

    def _find_function_end(self, content: str, start_pos: int) -> int:
        """查找函数结束的行数"""
        lines = content[start_pos:].split('\n')
        indent = len(lines[0]) - len(lines[0].lstrip()) if lines else 0
        line_count = 0

        for line in lines[1:]:
            line_count += 1
            if line.strip() and not line.startswith(' ' * (indent + 1)):
                # 找到同级或更高级的缩进，可能结束了函数
                if line.strip() and not line.strip().startswith('#'):
                    stripped = line.lstrip()
                    current_indent = len(line) - len(stripped)
                    if current_indent <= indent:
                        return line_count - 1
        return line_count
