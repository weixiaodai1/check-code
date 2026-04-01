"""
代码审核数据模型
定义审核结果、检查项、技能等数据结构和枚举类型
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


class SeverityLevel(Enum):
    """问题严重级别"""
    CRITICAL = "critical"      # 严重问题
    HIGH = "high"              # 高优先级
    MEDIUM = "medium"          # 中优先级
    LOW = "low"                # 低优先级
    INFO = "info"              # 信息提示


class CheckCategory(Enum):
    """检查类别"""
    CODE_QUALITY = "code_quality"           # 代码质量
    BEST_PRACTICES = "best_practices"       # 最佳实践
    SECURITY = "security"                   # 安全性
    PERFORMANCE = "performance"             # 性能
    DOCUMENTATION = "documentation"         # 文档
    TESTING = "testing"                     # 测试
    MAINTAINABILITY = "maintainability"     # 可维护性
    PROFESSIONAL_STANDARDS = "professional" # 专业标准


class SkillLevel(Enum):
    """技能熟练度级别"""
    BEGINNER = "beginner"       # 初级
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"       # 高级
    EXPERT = "expert"           # 专家级


@dataclass
class Location:
    """代码位置信息"""
    file_path: str
    line_number: int
    column_number: int = 0
    snippet: str = ""           # 代码片段


@dataclass
class CheckResult:
    """单个检查结果"""
    check_id: str
    check_name: str
    category: CheckCategory
    severity: SeverityLevel
    message: str
    location: Optional[Location] = None
    suggestion: str = ""        # 修复建议
    rule_id: str = ""           # 规则标识符
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "check_id": self.check_id,
            "check_name": self.check_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "location": {
                "file_path": self.location.file_path,
                "line_number": self.location.line_number,
                "column_number": self.location.column_number,
                "snippet": self.location.snippet
            } if self.location else None,
            "suggestion": self.suggestion,
            "rule_id": self.rule_id,
            "metadata": self.metadata
        }


@dataclass
class Skill:
    """识别出的技能/技术"""
    name: str
    category: str              # e.g., "语言", "框架", "工具", "库"
    level: SkillLevel
    confidence: float          # 置信度 0.0-1.0
    evidence: List[str] = field(default_factory=list)  # 证据
    description: str = ""
    version_hint: str = ""     # 版本提示

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "level": self.level.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "description": self.description,
            "version_hint": self.version_hint
        }


@dataclass
class AuditSummary:
    """审核摘要统计"""
    total_files: int = 0
    total_lines: int = 0
    total_checks: int = 0
    issues_by_severity: Dict[SeverityLevel, int] = field(default_factory=dict)
    issues_by_category: Dict[CheckCategory, int] = field(default_factory=dict)
    skills_detected: List[Skill] = field(default_factory=list)
    overall_score: float = 0.0  # 0-100
    grade: str = ""            # A, B, C, D, F

    def calculate_grade(self) -> str:
        """根据分数计算等级"""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "total_checks": self.total_checks,
            "issues_by_severity": {
                k.value: v for k, v in self.issues_by_severity.items()
            },
            "issues_by_category": {
                k.value: v for k, v in self.issues_by_category.items()
            },
            "skills_detected": [s.to_dict() for s in self.skills_detected],
            "overall_score": self.overall_score,
            "grade": self.grade
        }


@dataclass
class AuditReport:
    """完整的审核报告"""
    project_name: str
    audit_date: datetime
    summary: AuditSummary
    results: List[CheckResult]
    file_results: Dict[str, List[CheckResult]] = field(default_factory=dict)
    skills_inventory: List[Skill] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "audit_date": self.audit_date.isoformat(),
            "summary": self.summary.to_dict(),
            "results": [r.to_dict() for r in self.results],
            "file_results": {
                k: [r.to_dict() for r in v]
                for k, v in self.file_results.items()
            },
            "skills_inventory": [s.to_dict() for s in self.skills_inventory],
            "recommendations": self.recommendations,
            "duration_seconds": self.duration_seconds
        }
