"""
自定义规则分析器
基于用户定义的检查规则进行代码审核
"""

import re
from typing import List, Dict, Optional, Any
from pathlib import Path

from .base_analyzer import BaseAnalyzer
from ..models import CheckResult, CheckCategory, SeverityLevel
from ..rules_loader import RulesLoader, CheckRule


class CustomRulesAnalyzer(BaseAnalyzer):
    """自定义规则分析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._file_extensions = []
        self.rules_loader = RulesLoader()
        self._loaded_rules: List[CheckRule] = []
        
        # 从配置加载规则
        self._load_rules_from_config()

    def _load_rules_from_config(self):
        """从配置加载规则"""
        # 从文件加载
        rule_files = self.config.get('rule_files', [])
        if isinstance(rule_files, str):
            rule_files = [rule_files]

        for rule_file in rule_files:
            rules = self.rules_loader.load_from_file(rule_file)
            self._loaded_rules.extend(rules)

        # 从目录加载
        rule_dirs = self.config.get('rule_dirs', [])
        if isinstance(rule_dirs, str):
            rule_dirs = [rule_dirs]

        for rule_dir in rule_dirs:
            rules = self.rules_loader.load_from_directory(rule_dir)
            self._loaded_rules.extend(rules)

    def load_rules(self, file_path: str) -> int:
        """
        加载额外的规则文件

        Args:
            file_path: 规则文件路径

        Returns:
            加载的规则数量
        """
        rules = self.rules_loader.load_from_file(file_path)
        self._loaded_rules.extend(rules)
        return len(rules)

    def load_rules_directory(self, dir_path: str, recursive: bool = True) -> int:
        """
        从目录加载规则

        Args:
            dir_path: 规则目录路径
            recursive: 是否递归

        Returns:
            加载的规则数量
        """
        rules = self.rules_loader.load_from_directory(dir_path, recursive)
        self._loaded_rules.extend(rules)
        return len(rules)

    @property
    def name(self) -> str:
        return "自定义规则分析器"

    @property
    def description(self) -> str:
        return f"基于用户定义的 {len(self._loaded_rules)} 条自定义规则进行检查"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.PROFESSIONAL_STANDARDS

    @property
    def supported_extensions(self) -> List[str]:
        """根据加载的规则返回支持的文件扩展名"""
        extensions = set()
        for rule in self._loaded_rules:
            extensions.update(rule.file_extensions)
        return list(extensions) if extensions else ['.*']

    def can_analyze(self, file_path: str) -> bool:
        """检查是否可以分析给定文件"""
        if not self._loaded_rules:
            return False

        ext = Path(file_path).suffix.lower()
        
        # 如果没有特定的文件扩展名限制，则分析所有文件
        for rule in self._loaded_rules:
            if not rule.file_extensions:
                return True
            if ext in rule.file_extensions:
                return True
        
        return False

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """使用自定义规则分析文件"""
        self.results = []
        
        if not self._loaded_rules:
            return self.results

        ext = Path(file_path).suffix.lower()

        for rule in self._loaded_rules:
            # 检查规则是否启用
            if not rule.enabled:
                continue

            # 检查文件扩展名
            if rule.file_extensions and ext not in rule.file_extensions:
                continue

            # 执行正则匹配
            if rule.pattern:
                self._check_with_rule(file_path, content, rule)

        return self.results

    def _check_with_rule(self, file_path: str, content: str, rule: CheckRule):
        """使用规则检查代码"""
        try:
            # 使用缓存的正则表达式
            matches = self._find_pattern(content, rule.pattern)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                # 获取匹配的代码片段
                snippet = self._get_line_content(content, line_num)
                
                # 生成修复建议
                suggestion = self._generate_fix_suggestion(rule, content, match, line_num)
                
                self.results.append(self._create_result(
                    check_id=rule.rule_id,
                    check_name=rule.name,
                    message=f"{rule.description} (行 {line_num})",
                    severity=rule.severity,
                    file_path=file_path,
                    line_number=line_num,
                    snippet=snippet,
                    suggestion=suggestion,
                    rule_id=rule.rule_id,
                    metadata={'rule': rule.rule_id, 'match': match.group(0)}
                ))
        except re.error as e:
            # 正则表达式错误
            self.results.append(self._create_result(
                check_id=rule.rule_id,
                check_name=f"规则配置错误: {rule.name}",
                message=f"规则 '{rule.rule_id}' 的正则表达式无效: {e}",
                severity=SeverityLevel.WARNING,
                file_path=file_path,
                suggestion="检查规则的正则表达式语法"
            ))
        except Exception as e:
            pass  # 忽略其他错误

    def _generate_fix_suggestion(self, rule: CheckRule, content: str, 
                                  match: re.Match, line_num: int) -> str:
        """生成修复建议"""
        suggestions = []
        
        # 基础建议
        if rule.suggestion:
            suggestions.append(rule.suggestion)
        
        # 提供修复代码模板
        if rule.fix_template:
            suggestions.append(f"\n修复示例:\n```\n{rule.fix_template}\n```")
        
        # 提供智能修复建议
        matched_text = match.group(0)
        
        if rule.rule_id.startswith('CUSTOM'):
            # 根据匹配内容提供更具体的建议
            if 'print' in matched_text.lower():
                suggestions.append("\n推荐使用:")
                suggestions.append("```python")
                suggestions.append("import logging")
                suggestions.append("logger = logging.getLogger(__name__)")
                suggestions.append("logger.info('message')  # 替代 print")
                suggestions.append("```")
            
            elif 'TODO' in matched_text or 'FIXME' in matched_text:
                suggestions.append("\n处理建议:")
                suggestions.append("1. 完成待办任务")
                suggestions.append("2. 如果暂时不需要，删除该标记")
                suggestions.append("3. 添加任务跟踪系统的链接")
        
        return '\n'.join(suggestions) if suggestions else "请根据项目规范修复此问题"


class FixSuggestionGenerator:
    """修复建议生成器 - 根据检测到的问题生成具体的修复代码"""

    # 常见问题的修复模板
    FIX_TEMPLATES = {
        'QUAL001': {
            'type': 'line_too_long',
            'template': '# 使用反斜杠或括号进行换行\nlong_expression = (\n    first_part +\n    second_part +\n    third_part\n)'
        },
        'QUAL002': {
            'type': 'function_too_long',
            'template': '# 将大函数拆分为多个小函数\ndef main_function():\n    data = fetch_data()\n    processed = process_data(data)\n    return format_output(processed)'
        },
        'QUAL004': {
            'type': 'empty_except',
            'template': 'try:\n    # 你的代码\nexcept SpecificException as e:\n    logger.error(f"Error occurred: {e}")\n    raise  # 或添加适当的错误处理'
        },
        'SEC001-eval': {
            'type': 'dangerous_eval',
            'template': '# 避免使用 eval，使用 ast.literal_eval\nimport ast\n\ndef safe_eval(expr):\n    return ast.literal_eval(expr)'
        },
        'SEC010': {
            'type': 'sql_injection',
            'template': '# 使用参数化查询\ncursor.execute(\n    "SELECT * FROM users WHERE id = %s",\n    (user_id,)\n)'
        },
        'SEC011': {
            'type': 'xss_vulnerability',
            'template': '# 对用户输入进行转义\nfrom html import escape\n\nsafe_content = escape(user_input)\nelement.textContent = safe_content'
        },
        'SEC012': {
            'type': 'command_injection',
            'template': '# 避免 shell=True，使用参数列表\nsubprocess.run(\n    ["ls", "-la", directory],\n    shell=False\n)'
        },
        'BP001': {
            'type': 'bare_except',
            'template': 'try:\n    # 你的代码\nexcept Exception as e:\n    # 处理特定异常\n    raise ValueError("具体错误信息") from e'
        },
        'BP006': {
            'type': 'mutable_default',
            'template': 'def func(data=None):\n    if data is None:\n        data = []  # 使用 None 作为默认值\n    data.append(1)\n    return data'
        }
    }

    @classmethod
    def get_fix_template(cls, check_id: str) -> Optional[Dict]:
        """获取修复模板"""
        return cls.FIX_TEMPLATES.get(check_id)

    @classmethod
    def generate_contextual_fix(cls, check_id: str, content: str, 
                                 line_num: int) -> str:
        """
        生成上下文相关的修复建议

        Args:
            check_id: 检查项ID
            content: 文件内容
            line_num: 问题所在行号

        Returns:
            修复建议文本
        """
        template = cls.get_fix_template(check_id)
        
        if not template:
            return "请参考相关文档进行修复"

        fix_type = template['type']
        base_suggestion = template['template']

        # 根据代码上下文定制建议
        lines = content.split('\n')
        
        context_lines = []
        start = max(0, line_num - 3)
        end = min(len(lines), line_num + 2)
        
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            context_lines.append(f"{prefix}{lines[i]}")

        context = '\n'.join(context_lines)

        return f"""问题位置:
```python
{context}
```

推荐修复:
```python
{base_suggestion}
```

修复说明:
{cls._get_fix_explanation(fix_type)}"""

    @staticmethod
    def _get_fix_explanation(fix_type: str) -> str:
        """获取修复说明"""
        explanations = {
            'line_too_long': '将长行拆分为多行，使用括号或反斜杠续行可以提高代码可读性。',
            'function_too_long': '将大函数拆分为多个小函数，每个函数只做一件事，提高代码可维护性。',
            'empty_except': '空的异常处理会隐藏错误。应该记录日志或进行适当的错误处理。',
            'dangerous_eval': 'eval() 可以执行任意代码，存在严重的安全风险。使用 ast.literal_eval() 解析字面量。',
            'sql_injection': '字符串拼接SQL容易受到注入攻击。使用参数化查询可以防止SQL注入。',
            'xss_vulnerability': '直接插入HTML可能导致跨站脚本攻击。对用户输入进行HTML转义。',
            'command_injection': 'shell=True 和字符串拼接命令可能导致命令注入。使用参数列表。',
            'bare_except': '捕获所有异常可能隐藏重要错误。应该捕获特定异常类型。',
            'mutable_default': '使用可变对象作为默认参数可能导致意外修改。使用 None 并在函数内初始化。'
        }
        return explanations.get(fix_type, '请参考相关文档进行修复。')
