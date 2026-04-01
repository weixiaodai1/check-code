"""
专业级代码审核工具 (Professional Code Auditor)
==============================================

该工具提供全面的代码质量检查、最佳实践验证、专业标准评估
以及技能/技术栈识别功能。

作者: MiniMax Agent
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "MiniMax Agent"

from .auditor import CodeAuditor
from .reporters.reporter import ReportType

__all__ = ["CodeAuditor", "ReportType"]
