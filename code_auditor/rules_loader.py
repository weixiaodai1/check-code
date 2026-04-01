"""
自定义检查规则加载器
支持从 YAML/JSON 文件加载自定义检查规则
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class RuleFormat(Enum):
    """规则文件格式"""
    JSON = "json"
    YAML = "yaml"


# 延迟导入避免循环依赖
_models_imported = False

def _get_severity_level():
    global _models_imported
    if not _models_imported:
        from ..models import SeverityLevel
        globals()['SeverityLevel'] = SeverityLevel
        _models_imported = True
    return globals()['SeverityLevel']


def _get_check_category():
    global _models_imported
    if not _models_imported:
        from ..models import CheckCategory
        globals()['CheckCategory'] = CheckCategory
        _models_imported = True
    return globals()['CheckCategory']


@dataclass
class CheckRule:
    """单个检查规则"""
    rule_id: str
    name: str
    description: str
    category: Any  # CheckCategory
    severity: Any  # SeverityLevel
    pattern: str  # 正则表达式模式
    suggestion: str = ""  # 修复建议
    fix_template: str = ""  # 修复代码模板
    file_extensions: List[str] = field(default_factory=list)  # 适用的文件扩展名
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # 延迟转换为枚举类型
        if isinstance(self.category, str):
            try:
                CheckCategory = _get_check_category()
                self.category = CheckCategory(self.category)
            except ValueError:
                from ..models import CheckCategory
                self.category = CheckCategory.CODE_QUALITY
        
        if isinstance(self.severity, str):
            try:
                SeverityLevel = _get_severity_level()
                self.severity = SeverityLevel(self.severity.lower())
            except ValueError:
                from ..models import SeverityLevel
                self.severity = SeverityLevel.MEDIUM


class RulesLoader:
    """自定义规则加载器"""

    def __init__(self):
        self.rules: List[CheckRule] = []
        self._errors: List[str] = []

    def load_from_file(self, file_path: str) -> List[CheckRule]:
        """
        从文件加载规则

        Args:
            file_path: 规则文件路径（支持 .json, .yaml, .yml）

        Returns:
            加载的规则列表
        """
        path = Path(file_path)
        
        if not path.exists():
            self._errors.append(f"规则文件不存在: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if path.suffix.lower() in ['.yaml', '.yml']:
                return self._parse_yaml(content)
            elif path.suffix.lower() == '.json':
                return self._parse_json(content)
            else:
                # 尝试自动检测格式
                try:
                    return self._parse_json(content)
                except json.JSONDecodeError:
                    return self._parse_yaml(content)

        except Exception as e:
            self._errors.append(f"加载规则文件出错: {e}")
            return []

    def load_from_directory(self, dir_path: str, recursive: bool = True) -> List[CheckRule]:
        """
        从目录加载所有规则文件

        Args:
            dir_path: 规则目录路径
            recursive: 是否递归搜索子目录

        Returns:
            加载的所有规则列表
        """
        path = Path(dir_path)
        
        if not path.exists() or not path.is_dir():
            self._errors.append(f"规则目录不存在: {dir_path}")
            return []

        all_rules = []
        patterns = ['*.json', '*.yaml', '*.yml'] if recursive else []

        for pattern in patterns:
            for rule_file in path.rglob(pattern):
                rules = self.load_from_file(str(rule_file))
                all_rules.extend(rules)

        # 如果非递归模式，直接查找顶层文件
        if not recursive:
            for ext in ['.json', '.yaml', '.yml']:
                for rule_file in path.glob(f'*{ext}'):
                    if rule_file.is_file():
                        rules = self.load_from_file(str(rule_file))
                        all_rules.extend(rules)

        self.rules.extend(all_rules)
        return all_rules

    def _parse_json(self, content: str) -> List[CheckRule]:
        """解析 JSON 格式规则"""
        data = json.loads(content)
        return self._parse_rules_data(data)

    def _parse_yaml(self, content: str) -> List[CheckRule]:
        """解析 YAML 格式规则"""
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            # 如果是单个规则对象，包装成列表
            if 'rule_id' in data:
                data = [data]
            # 如果是 rules 键包含规则列表
            elif 'rules' in data:
                data = data['rules']
        return self._parse_rules_data(data)

    def _parse_rules_data(self, data) -> List[CheckRule]:
        """解析规则数据"""
        rules = []
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'rules' in data:
            items = data['rules']
        else:
            items = [data]

        for item in items:
            try:
                rule = self._parse_single_rule(item)
                if rule:
                    rules.append(rule)
                    self.rules.append(rule)
            except Exception as e:
                self._errors.append(f"解析规则出错: {e}")

        return rules

    def _parse_single_rule(self, item: Dict) -> Optional[CheckRule]:
        """解析单个规则"""
        if not isinstance(item, dict):
            return None

        # 获取规则ID
        rule_id = item.get('rule_id') or item.get('id')
        if not rule_id:
            return None

        # 解析文件扩展名
        extensions = item.get('file_extensions', [])
        if isinstance(extensions, str):
            extensions = [extensions]

        # 创建规则对象，类型转换会在 __post_init__ 中处理
        return CheckRule(
            rule_id=rule_id,
            name=item.get('name', rule_id),
            description=item.get('description', ''),
            category=item.get('category', 'code_quality'),
            severity=item.get('severity', 'medium'),
            pattern=item.get('pattern', ''),
            suggestion=item.get('suggestion', ''),
            fix_template=item.get('fix_template', ''),
            file_extensions=extensions,
            enabled=item.get('enabled', True),
            metadata=item.get('metadata', {})
        )

    def get_errors(self) -> List[str]:
        """获取加载过程中的错误"""
        return self._errors.copy()

    def clear_errors(self):
        """清除错误列表"""
        self._errors.clear()

    def get_rules_by_category(self, category: Any) -> List[CheckRule]:
        """按类别获取规则"""
        from ..models import CheckCategory
        return [r for r in self.rules if r.category == category]

    def get_rules_by_extension(self, ext: str) -> List[CheckRule]:
        """按文件扩展名获取规则"""
        return [r for r in self.rules 
                if not r.file_extensions or ext in r.file_extensions]


# 示例规则文件内容（用于文档）
EXAMPLE_RULES_JSON = '''
{
  "rules": [
    {
      "rule_id": "CUSTOM001",
      "name": "禁止使用 print 语句",
      "description": "生产代码中不应使用 print 语句，应使用日志框架",
      "category": "best_practices",
      "severity": "medium",
      "pattern": "\\\\bprint\\\\s*\\\\(",
      "suggestion": "使用 Python 日志模块 (logging) 代替 print",
      "file_extensions": [".py"]
    },
    {
      "rule_id": "CUSTOM002", 
      "name": "API 必须有版本控制",
      "description": "API 路径应包含版本号",
      "category": "best_practices",
      "severity": "high",
      "pattern": "@app\\\\.route\\\\(['\\\"]\\\\/(?!v[0-9])",
      "suggestion": "在 API 路径中添加版本号，如 /v1/resource",
      "file_extensions": [".py"]
    }
  ]
}
'''

EXAMPLE_RULES_YAML = '''
rules:
  - rule_id: CUSTOM001
    name: 禁止使用 print 语句
    description: 生产代码中不应使用 print 语句，应使用日志框架
    category: best_practices
    severity: medium
    pattern: "\\bprint\\s*\\("
    suggestion: 使用 Python 日志模块 (logging) 代替 print
    file_extensions:
      - .py

  - rule_id: CUSTOM002
    name: API 必须有版本控制
    description: API 路径应包含版本号
    category: best_practices
    severity: high
    pattern: '@app\\.route\\([\\'"]\\/(?!v[0-9])'
    suggestion: 在 API 路径中添加版本号，如 /v1/resource
    file_extensions:
      - .py
'''
