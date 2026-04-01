"""
分析器基类
定义所有分析器的通用接口和功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import re
from pathlib import Path

from ..models import CheckResult, CheckCategory, SeverityLevel, Location


class BaseAnalyzer(ABC):
    """所有分析器的抽象基类"""

    # 类级别的正则表达式缓存（所有实例共享）
    _regex_cache: Dict[str, re.Pattern] = {}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分析器

        Args:
            config: 分析器配置选项
        """
        self.config = config or {}
        self.results: List[CheckResult] = []
        self._file_extensions: List[str] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """分析器名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """分析器描述"""
        pass

    @property
    @abstractmethod
    def category(self) -> CheckCategory:
        """分析器所属类别"""
        pass

    @property
    def supported_extensions(self) -> List[str]:
        """支持的文件扩展名"""
        return self._file_extensions

    def can_analyze(self, file_path: str) -> bool:
        """检查此分析器是否可以分析给定文件"""
        if not self._file_extensions:
            return True
        ext = Path(file_path).suffix.lower()
        return ext in self._file_extensions or f"*{ext}" in self._file_extensions

    @abstractmethod
    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """
        分析单个文件

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            检查结果列表
        """
        pass

    def _create_result(
        self,
        check_id: str,
        check_name: str,
        message: str,
        severity: SeverityLevel,
        file_path: str,
        line_number: int = 0,
        snippet: str = "",
        suggestion: str = "",
        rule_id: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> CheckResult:
        """创建检查结果的辅助方法"""
        location = None
        if file_path:
            location = Location(
                file_path=file_path,
                line_number=line_number,
                snippet=snippet
            )

        return CheckResult(
            check_id=check_id,
            check_name=check_name,
            category=self.category,
            severity=severity,
            message=message,
            location=location,
            suggestion=suggestion,
            rule_id=rule_id,
            metadata=metadata or {}
        )

    def _find_pattern(
        self,
        content: str,
        pattern: str,
        flags: int = 0
    ) -> List[re.Match]:
        """查找所有匹配的模式（使用缓存的正则表达式）"""
        cache_key = f"{pattern}:{flags}"
        
        if cache_key not in BaseAnalyzer._regex_cache:
            BaseAnalyzer._regex_cache[cache_key] = re.compile(pattern, flags)
        
        compiled_pattern = BaseAnalyzer._regex_cache[cache_key]
        return list(compiled_pattern.finditer(content))

    def _get_line_content(self, content: str, line_number: int) -> str:
        """获取指定行的内容"""
        lines = content.split('\n')
        if 0 < line_number <= len(lines):
            return lines[line_number - 1]
        return ""

    def _count_lines(self, content: str) -> int:
        """计算代码行数（排除空行和注释）"""
        lines = content.split('\n')
        code_lines = 0
        in_multiline_comment = False

        for line in lines:
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                continue

            # 处理多行注释
            if '"""' in stripped or "'''" in stripped:
                if stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1:
                    in_multiline_comment = not in_multiline_comment
                if in_multiline_comment:
                    continue

            if in_multiline_comment:
                continue

            # 跳过单行注释
            if stripped.startswith('#') or stripped.startswith('//'):
                continue

            code_lines += 1

        return code_lines

    def _calculate_complexity(self, content: str) -> int:
        """计算代码复杂度（基于控制流语句数量）"""
        control_flow_patterns = [
            r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bfor\b', r'\bwhile\b', r'\bdo\b',
            r'\bswitch\b', r'\bcase\b',
            r'\bcatch\b', r'\btry\b', r'\bfinally\b',
            r'\band\b', r'\bor\b', r'\&\&', r'\|\|'
        ]

        complexity = 1  # 基础复杂度
        for pattern in control_flow_patterns:
            matches = re.findall(pattern, content)
            complexity += len(matches)

        return complexity

    def _check_naming_convention(
        self,
        name: str,
        convention: str = "snake_case"
    ) -> bool:
        """检查命名是否符合规范"""
        if convention == "snake_case":
            return bool(re.match(r'^[a-z][a-z0-9_]*$', name))
        elif convention == "camelCase":
            return bool(re.match(r'^[a-z][a-zA-Z0-9]*$', name))
        elif convention == "PascalCase":
            return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
        elif convention == "SCREAMING_SNAKE_CASE":
            return bool(re.match(r'^[A-Z][A-Z0-9_]*$', name))
        return True

    def get_results(self) -> List[CheckResult]:
        """获取所有检查结果"""
        return self.results

    def clear_results(self):
        """清除所有检查结果"""
        self.results = []
