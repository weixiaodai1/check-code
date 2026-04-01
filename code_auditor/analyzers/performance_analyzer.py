"""
性能分析器
检查代码中的性能问题和优化机会
"""

from typing import List, Dict, Set, Tuple
import re
from .base_analyzer import BaseAnalyzer
from ..models import CheckResult, CheckCategory, SeverityLevel


class PerformanceAnalyzer(BaseAnalyzer):
    """性能分析器"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._file_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs']
        self._loop_detection_threshold = self.config.get('loop_threshold', 3)

    @property
    def name(self) -> str:
        return "性能分析器"

    @property
    def description(self) -> str:
        return "检查代码中的性能问题和优化机会"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.PERFORMANCE

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """执行性能分析"""
        self.results = []

        self._check_inefficient_loops(file_path, content)
        self._check_string_concatenation(file_path, content)
        self._check_unnecessary_list_copies(file_path, content)
        self._check_inefficient_data_structures(file_path, content)
        self._check_globals_usage(file_path, content)
        self._check_repeated_attribute_lookups(file_path, content)
        self._check_inefficient_regex(file_path, content)
        self._check_n_plus_one_queries(file_path, content)
        self._check_unnecessary_computations(file_path, content)
        self._check_cacheable_results(file_path, content)

        return self.results

    def _check_inefficient_loops(self, file_path: str, content: str) -> None:
        """检查低效循环"""
        # 检测嵌套循环
        lines = content.split('\n')
        in_function = False
        loop_stack = []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if stripped.startswith('def '):
                in_function = True
                loop_stack = []
            elif in_function:
                if stripped.startswith('return') or (stripped == '' and len(loop_stack) == 0):
                    continue

                # 检测循环开始
                if re.match(r'\b(for|while)\b', stripped):
                    loop_stack.append(line_num)
                    if len(loop_stack) >= 3:
                        self.results.append(self._create_result(
                            check_id="PERF001",
                            check_name="嵌套过深的循环",
                            message=f"行 {line_num}: 检测到 {len(loop_stack)} 层嵌套循环",
                            severity=SeverityLevel.MEDIUM,
                            file_path=file_path,
                            line_number=line_num,
                            snippet=stripped,
                            suggestion="深层嵌套循环可能影响性能，考虑重构为更高效的算法",
                            rule_id="deep-loop-nesting"
                        ))

                # 检测循环结束（简化判断）
                if loop_stack and not line.startswith(' ' * 4):
                    loop_stack.pop()

    def _check_string_concatenation(self, file_path: str, content: str) -> None:
        """检查字符串拼接"""
        # 检测循环中拼接字符串
        in_loop = False
        string_concat_in_loop = []

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if 'for ' in stripped or 'while ' in stripped:
                in_loop = True
            elif stripped.startswith('def ') or (in_loop and not line.startswith(' ' * 4)):
                in_loop = False

            if in_loop:
                # 检测 += 字符串拼接
                if re.search(r'\+=?\s*["\']', line):
                    string_concat_in_loop.append(line_num)

        if string_concat_in_loop:
            for line_num in string_concat_in_loop:
                self.results.append(self._create_result(
                    check_id="PERF002",
                    check_name="循环中拼接字符串",
                    message=f"行 {line_num}: 在循环中使用字符串拼接可能效率低下",
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=self._get_line_content(content, line_num),
                    suggestion="使用列表+join()或生成器表达式代替循环拼接",
                    rule_id="string-concat-in-loop"
                ))

        # 检测使用 + 连接多个字符串
        if re.search(r'["\'][^"\']+\+["\'][^"\']+\+["\']', content):
            self.results.append(self._create_result(
                check_id="PERF003",
                check_name="使用+连接多个字符串",
                message="检测到使用+运算符连接多个字符串",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="使用f-string或join()方法更高效",
                rule_id="multiple-string-concat"
            ))

    def _check_unnecessary_list_copies(self, file_path: str, content: str) -> None:
        """检查不必要的列表拷贝"""
        # 检测 [:] 拷贝模式
        copy_pattern = r'(\w+)\s*=\s*(\w+)\s*\[:\s*\]'

        matches = self._find_pattern(content, copy_pattern)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)

            # 检查拷贝后是否真正需要副本
            self.results.append(self._create_result(
                check_id="PERF004",
                check_name="不必要的列表拷贝",
                message=f"行 {line_num}: 创建了 '{var_name}' 的浅拷贝",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                line_number=line_num,
                snippet=match.group(0),
                suggestion="如果不需要副本，考虑直接引用原列表或使用切片拷贝的替代方案",
                rule_id="unnecessary-copy"
            ))

    def _check_inefficient_data_structures(self, file_path: str, content: str) -> None:
        """检查低效的数据结构使用"""
        # 检测使用列表进行频繁查找
        if 'append' in content and content.count('append') > 5:
            # 简单检查：可能应该使用集合
            self.results.append(self._create_result(
                check_id="PERF005",
                check_name="可能存在低效数据结构使用",
                message="代码中多次使用append，可能适合使用集合(set)进行快速查找",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="如果主要进行成员检查操作，考虑使用set代替list",
                rule_id="inefficient-data-structure"
            ))

        # 检测 in 操作在大型列表上
        if re.search(r'\bif\s+\w+\s+in\s+\w+', content):
            self.results.append(self._create_result(
                check_id="PERF006",
                check_name="成员检查可能低效",
                message="检测到使用 'in' 进行成员检查",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="如果列表较大，考虑使用set进行O(1)查找",
                rule_id="membership-check"
            ))

    def _check_globals_usage(self, file_path: str, content: str) -> None:
        """检查全局变量的使用"""
        # 检测global声明
        global_matches = self._find_pattern(content, r'\bglobal\s+\w+')

        for match in global_matches:
            line_num = content[:match.start()].count('\n') + 1
            self.results.append(self._create_result(
                check_id="PERF007",
                check_name="使用全局变量",
                message=f"行 {line_num}: 检测到全局变量声明",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                line_number=line_num,
                snippet=self._get_line_content(content, line_num),
                suggestion="全局变量可能影响性能和代码可维护性，考虑使用参数传递或类封装",
                rule_id="avoid-globals"
            ))

    def _check_repeated_attribute_lookups(self, file_path: str, content: str) -> None:
        """检查重复的属性查找"""
        # 检测循环中重复的属性访问
        lines = content.split('\n')
        in_loop = False
        prev_line = ""

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if 'for ' in stripped or 'while ' in stripped:
                in_loop = True
                prev_line = stripped
            elif in_loop:
                if not line.startswith(' ' * 4):
                    in_loop = False
                elif in_loop and stripped:
                    # 检测类似 obj.attr 在连续行中出现
                    if prev_line and '.' in prev_line:
                        prev_attrs = set(re.findall(r'(\w+\.\w+)', prev_line))
                        curr_attrs = set(re.findall(r'(\w+\.\w+)', stripped))
                        if prev_attrs & curr_attrs:
                            self.results.append(self._create_result(
                                check_id="PERF008",
                                check_name="重复的属性访问",
                                message=f"行 {line_num}: 检测到重复的属性访问，可能适合缓存",
                                severity=SeverityLevel.LOW,
                                file_path=file_path,
                                line_number=line_num,
                                snippet=stripped[:80],
                                suggestion="将重复访问的属性缓存在局部变量中",
                                rule_id="cache-attribute"
                            ))
                    prev_line = stripped

    def _check_inefficient_regex(self, file_path: str, content: str) -> None:
        """检查低效的正则表达式"""
        # 检测在循环中编译正则
        in_loop = False

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if 'for ' in stripped or 'while ' in stripped:
                in_loop = True
            elif not line.startswith(' ' * 4) and stripped:
                in_loop = False

            if in_loop and re.search(r're\.(compile|search|match|findall)', stripped):
                self.results.append(self._create_result(
                    check_id="PERF009",
                    check_name="循环中编译正则表达式",
                    message=f"行 {line_num}: 在循环中重复编译正则表达式",
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=stripped,
                    suggestion="将正则表达式编译移到循环外部",
                    rule_id="regex-in-loop"
                ))

    def _check_n_plus_one_queries(self, file_path: str, content: str) -> None:
        """检查N+1查询问题"""
        # 检测在循环中执行查询
        in_loop = False
        query_patterns = [
            r'\.query\s*\(',
            r'\.filter\s*\(',
            r'\.all\s*\(',
            r'\.get\s*\(',
            r'cursor\.execute',
            r'\.find\s*\(',
            r'\.select\s*\(',
        ]

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if 'for ' in stripped or 'while ' in stripped:
                in_loop = True
            elif not line.startswith(' ' * 4) and stripped:
                in_loop = False

            if in_loop:
                for pattern in query_patterns:
                    if re.search(pattern, stripped):
                        self.results.append(self._create_result(
                            check_id="PERF010",
                            check_name="可能的N+1查询问题",
                            message=f"行 {line_num}: 在循环中执行数据库查询",
                            severity=SeverityLevel.HIGH,
                            file_path=file_path,
                            line_number=line_num,
                            snippet=stripped[:80],
                            suggestion="考虑使用批量查询或预加载(JOIN/SELECT IN)来减少查询次数",
                            rule_id="n-plus-one"
                        ))
                        break

    def _check_unnecessary_computations(self, file_path: str, content: str) -> None:
        """检查不必要的重复计算"""
        # 检测重复的函数调用
        func_calls = []
        for match in re.finditer(r'(\w+)\s*\([^)]*\)\s*(?:\.(?:split|strip|lower|upper)\s*\(\s*\))?', content):
            func_name = match.group(1)
            if len(func_name) > 2 and not func_name.startswith('_'):
                func_calls.append((func_name, match.start()))

        seen = {}
        for func_name, pos in func_calls:
            if func_name not in seen:
                seen[func_name] = pos
            else:
                line_num = content[:pos].count('\n') + 1
                # 简化：只提示可能的重复计算
                pass  # 过于简化，这里不做具体实现

        # 检测可以预先计算的值
        if re.search(r'len\s*\(\s*list\s*\(\s*range\s*\(', content):
            self.results.append(self._create_result(
                check_id="PERF011",
                check_name="不必要的类型转换",
                message="使用len(list(range(...)))可以简化为range(...)的直接使用",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="避免不必要的类型转换",
                rule_id="unnecessary-conversion"
            ))

    def _check_cacheable_results(self, file_path: str, content: str) -> None:
        """检查可以缓存的结果"""
        # 检测纯函数可能被重复调用
        func_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*:'

        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            start_pos = match.end()
            func_body = content[start_pos:start_pos + 500]

            # 检查是否是纯函数（没有副作用）
            if 'global' not in func_body and 'print' not in func_body:
                # 检查函数是否被多次调用
                call_count = len(re.findall(rf'\b{func_name}\s*\(', content))
                if call_count > 3:
                    self.results.append(self._create_result(
                        check_id="PERF012",
                        check_name="可以添加缓存的函数",
                        message=f"函数 '{func_name}' 被调用 {call_count} 次，可能是纯函数",
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        suggestion="考虑使用@lru_cache装饰器缓存函数结果",
                        rule_id="cacheable-function"
                    ))
