"""
文档分析器
检查代码文档的完整性和质量
"""

from typing import List, Dict, Set, Tuple
import re
from pathlib import Path
from .base_analyzer import BaseAnalyzer
from ..models import CheckResult, CheckCategory, SeverityLevel


class DocumentationAnalyzer(BaseAnalyzer):
    """文档分析器"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._file_extensions = ['.py', '.js', '.ts', '.java', '.go', '.md', '.rst']
        self._project_root = self.config.get('project_root', '.')

    @property
    def name(self) -> str:
        return "文档分析器"

    @property
    def description(self) -> str:
        return "检查代码文档的完整性和质量"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.DOCUMENTATION

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """执行文档分析"""
        self.results = []

        self._check_module_documentation(file_path, content)
        self._check_function_documentation(file_path, content)
        self._check_class_documentation(file_path, content)
        self._check_inline_comments(file_path, content)
        self._check_todo_comments(file_path, content)
        self._check_api_documentation(file_path, content)
        self._check_readme_quality(file_path, content)

        return self.results

    def _check_module_documentation(self, file_path: str, content: str) -> None:
        """检查模块级文档"""
        lines = content.split('\n')

        # 检查是否有模块级文档字符串
        if not (content.startswith('"""') or content.startswith("'''")):
            # 检查是否以注释开头
            first_meaningful_line = None
            for line in lines[:10]:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    first_meaningful_line = stripped
                    break

            if first_meaningful_line:
                self.results.append(self._create_result(
                    check_id="DOC001",
                    check_name="缺少模块文档",
                    message="模块缺少文档字符串",
                    severity=SeverityLevel.LOW,
                    file_path=file_path,
                    suggestion="在文件顶部添加模块级文档字符串，描述模块的功能和用途",
                    rule_id="module-docstring"
                ))

    def _check_function_documentation(self, file_path: str, content: str) -> None:
        """检查函数文档"""
        # 匹配函数定义
        func_pattern = r"def\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([\w\[\],\s|]+))?\s*:\s*(['\"])?"

        matches = list(re.finditer(func_pattern, content))

        for i, match in enumerate(matches):
            func_name = match.group(1)
            params = match.group(2) or ""
            return_type = match.group(3)
            has_docstring = match.group(4) is not None

            # 获取函数开始位置
            func_start = match.start()
            line_num = content[:func_start].count('\n') + 1

            # 跳过私有函数（但检查重要私有函数）
            if func_name.startswith('_') and func_name not in [
                '__init__', '__str__', '__repr__', '__call__',
                '__enter__', '__exit__', '__getitem__', '__setitem__'
            ]:
                continue

            # 检查是否有文档字符串
            if not has_docstring:
                self.results.append(self._create_result(
                    check_id="DOC002",
                    check_name="函数缺少文档",
                    message=f"函数 '{func_name}' 缺少文档字符串",
                    severity=SeverityLevel.LOW,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=f"def {func_name}({params}):",
                    suggestion=f"为 '{func_name}' 添加文档字符串，说明功能、参数和返回值",
                    rule_id="function-docstring"
                ))

            # 检查参数是否有文档
            if params.strip():
                # 获取函数体前几行
                func_body_start = match.end()
                func_body = content[func_body_start:func_body_start + 500]

                # 检查docstring中是否包含Args或参数描述
                if has_docstring:
                    if not re.search(r'(Args|Arguments|Parameters|参数)', func_body):
                        self.results.append(self._create_result(
                            check_id="DOC003",
                            check_name="文档缺少参数说明",
                            message=f"函数 '{func_name}' 的文档缺少参数说明",
                            severity=SeverityLevel.INFO,
                            file_path=file_path,
                            line_number=line_num,
                            suggestion=f"在 '{func_name}' 的文档中添加 Args 或参数说明",
                            rule_id="document-args"
                        ))

                # 检查返回类型是否有文档
                if return_type and return_type != 'None':
                    if has_docstring:
                        if not re.search(r'(Returns?|返回)', func_body):
                            self.results.append(self._create_result(
                                check_id="DOC004",
                                check_name="文档缺少返回值说明",
                                message=f"函数 '{func_name}' 指定了返回类型但文档缺少返回说明",
                                severity=SeverityLevel.INFO,
                                file_path=file_path,
                                line_number=line_num,
                                suggestion=f"在 '{func_name}' 的文档中添加 Returns 说明",
                                rule_id="document-return"
                            ))

    def _check_class_documentation(self, file_path: str, content: str) -> None:
        """检查类文档"""
        class_pattern = r"class\s+(\w+)(?:\([^)]*\))?\s*:\s*(['\"])?"

        matches = list(re.finditer(class_pattern, content))

        for match in matches:
            class_name = match.group(1)
            has_docstring = match.group(2) is not None
            line_num = content[:match.start()].count('\n') + 1

            # 跳过私有类
            if class_name.startswith('_'):
                continue

            if not has_docstring:
                self.results.append(self._create_result(
                    check_id="DOC005",
                    check_name="类缺少文档",
                    message=f"类 '{class_name}' 缺少文档字符串",
                    severity=SeverityLevel.LOW,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=f"class {class_name}:",
                    suggestion=f"为 '{class_name}' 添加文档字符串，描述类的功能和用法",
                    rule_id="class-docstring"
                ))

    def _check_inline_comments(self, file_path: str, content: str) -> None:
        """检查内联注释质量"""
        lines = content.split('\n')
        uninformative_comments = []

        # 无意义的注释词
        meaningless = [
            r'^\s*#.*\b(the|a|an)\s+\w+\s*$',  # "the something"
            r'^\s*#.*\b(and|or|but)\s+\w+\s*$',  # "and something"
            r'^\s*#\s*(ok|okay|yes|no)\s*$',  # 单字注释
            r'^\s*#.*(?<![a-zA-Z])([a-z])\s*$',  # 单字符注释
        ]

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                # 跳过版权和文件头注释
                if any(kw in stripped.lower() for kw in ['copyright', 'license', 'author', '@author']):
                    continue

                # 检查无意义注释
                for pattern in meaningless:
                    if re.match(pattern, stripped, re.IGNORECASE):
                        uninformative_comments.append((line_num, stripped))
                        break

        if uninformative_comments:
            for line_num, comment in uninformative_comments[:3]:  # 只报告前3个
                self.results.append(self._create_result(
                    check_id="DOC006",
                    check_name="无意义注释",
                    message=f"行 {line_num}: 存在无意义的注释",
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=comment[:80],
                    suggestion="删除无意义的注释，或用有意义的说明替代",
                    rule_id="meaningless-comment"
                ))

    def _check_todo_comments(self, file_path: str, content: str) -> None:
        """检查TODO/FIXME注释"""
        todo_patterns = [
            (r'\bTODO\b', "TODO注释"),
            (r'\bFIXME\b', "FIXME注释"),
            (r'\bHACK\b', "HACK注释"),
            (r'\bXXX\b', "XXX注释"),
            (r'\bBUG\b', "BUG注释"),
        ]

        todos = []
        for pattern, name in todo_patterns:
            matches = self._find_pattern(content, pattern, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line = self._get_line_content(content, line_num)
                todos.append((line_num, name, line.strip()))

        if todos:
            for line_num, todo_type, line in todos[:5]:  # 报告前5个
                self.results.append(self._create_result(
                    check_id="DOC007",
                    check_name=f"存在{todo_type}",
                    message=f"行 {line_num}: 检测到{todo_type}标记",
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=line[:100],
                    suggestion=f"考虑处理此{todo_type}标记，或添加更详细的说明和JIRA/Issue链接",
                    rule_id="todo-comment"
                ))

    def _check_api_documentation(self, file_path: str, content: str) -> None:
        """检查API文档"""
        # 检测可能暴露的API端点
        api_patterns = [
            (r'@app\.(route|get|post|put|delete|patch)', "Flask路由"),
            (r'@router\.(get|post|put|delete|patch)', "FastAPI路由"),
            (r'def\s+\w+\s*\([^)]*\):\s*(?:->\s*\w+\s*)?\s*["\']{3}', "FastAPI端点"),
            (r'@\w+\.route\s*\(["\']', "Express路由"),
            (r'@\w+\.(Get|Post|Put|Delete|Patch)\s*\(', "NestJS路由"),
        ]

        detected_apis = []
        for pattern, api_type in api_patterns:
            matches = self._find_pattern(content, pattern)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                detected_apis.append((line_num, api_type))

        # 检查是否有API文档注释
        for line_num, api_type in detected_apis[:5]:
            line = self._get_line_content(content, line_num)
            # 检查后续几行是否有文档
            lines_after = content.split('\n')[line_num:line_num + 10]
            has_doc = any('"""' in l or "'''" in l or '//' in l or '/**' in l for l in lines_after[:5])

            if not has_doc:
                self.results.append(self._create_result(
                    check_id="DOC008",
                    check_name=f"{api_type}缺少API文档",
                    message=f"行 {line_num}: {api_type}缺少API文档",
                    severity=SeverityLevel.LOW,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=line.strip()[:80],
                    suggestion=f"为{api_type}添加API文档，说明端点功能、参数和响应格式",
                    rule_id="api-documentation"
                ))

    def _check_readme_quality(self, file_path: str, content: str) -> None:
        """检查README质量"""
        # 检查README文件
        if 'readme' in file_path.lower():
            # 检查基本要素
            has_title = re.search(r'^#\s+\w+', content, re.MULTILINE)
            has_install = 'install' in content.lower()
            has_usage = 'usage' in content.lower() or 'example' in content.lower()
            has_license = 'license' in content.lower()

            issues = []
            if not has_title:
                issues.append("缺少标题")
            if not has_install:
                issues.append("缺少安装说明")
            if not has_usage:
                issues.append("缺少使用示例")
            if not has_license:
                issues.append("缺少许可证信息")

            if issues:
                line_num = 1
                self.results.append(self._create_result(
                    check_id="DOC009",
                    check_name="README质量可改进",
                    message=f"README缺少以下内容: {', '.join(issues)}",
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="完善README以提高项目可维护性和可发现性",
                    rule_id="readme-quality"
                ))
