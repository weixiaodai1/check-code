"""
报告生成器基类
定义报告生成器的通用接口
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from pathlib import Path

from ..models import AuditReport


class ReportType(Enum):
    """报告类型枚举"""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CONSOLE = "console"
    XML = "xml"


class Reporter(ABC):
    """报告生成器抽象基类"""

    def __init__(self, output_path: Optional[str] = None):
        """
        初始化报告生成器

        Args:
            output_path: 输出文件路径，如果为None则输出到标准输出
        """
        self.output_path = output_path

    @abstractmethod
    def generate(self, report: AuditReport) -> str:
        """
        生成报告

        Args:
            report: 审核报告数据

        Returns:
            报告内容字符串
        """
        pass

    def save(self, content: str) -> Optional[str]:
        """保存报告到文件"""
        if self.output_path:
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return self.output_path
        return None

    @staticmethod
    def get_reporter(report_type: ReportType, output_path: Optional[str] = None) -> 'Reporter':
        """
        工厂方法：根据报告类型获取对应的报告生成器

        Args:
            report_type: 报告类型
            output_path: 输出路径

        Returns:
            报告生成器实例
        """
        reporters = {
            ReportType.JSON: JSONReporter,
            ReportType.HTML: HTMLReporter,
            ReportType.MARKDOWN: MarkdownReporter,
            ReportType.CONSOLE: ConsoleReporter,
        }

        reporter_class = reporters.get(report_type, JSONReporter)
        return reporter_class(output_path)


class JSONReporter(Reporter):
    """JSON格式报告生成器"""

    def generate(self, report: AuditReport) -> str:
        """生成JSON格式报告"""
        import json

        report_dict = report.to_dict()
        return json.dumps(report_dict, ensure_ascii=False, indent=2)


class MarkdownReporter(Reporter):
    """Markdown格式报告生成器"""

    def generate(self, report: AuditReport) -> str:
        """生成Markdown格式报告"""
        lines = []

        # 标题
        lines.append(f"# 代码审核报告")
        lines.append(f"\n**项目**: {report.project_name}")
        lines.append(f"**审核日期**: {report.audit_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**审核时长**: {report.duration_seconds:.2f}秒\n")

        # 摘要
        lines.append("## 审核摘要")
        lines.append(f"- **总体评分**: {report.summary.overall_score:.1f}/100 ({report.summary.grade})")
        lines.append(f"- **文件数量**: {report.summary.total_files}")
        lines.append(f"- **代码总行数**: {report.summary.total_lines}")
        lines.append(f"- **检查项总数**: {report.summary.total_checks}")

        # 问题统计
        lines.append("\n### 问题统计")
        if report.summary.issues_by_severity:
            for severity, count in report.summary.issues_by_severity.items():
                emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢',
                    'info': '🔵'
                }.get(severity.value, '⚪')
                lines.append(f"- {emoji} {severity.value.upper()}: {count}")
        else:
            lines.append("- 未发现问题")

        # 技能清单
        if report.skills_inventory:
            lines.append("\n## 识别的技能/技术栈")
            for skill in report.skills_inventory:
                level_emoji = {
                    'expert': '⭐',
                    'advanced': '🌟',
                    'intermediate': '✨',
                    'beginner': '📚'
                }.get(skill.level.value, '📝')
                lines.append(f"- {level_emoji} **{skill.name}** ({skill.category}) - {skill.level.value}")

        # 详细结果
        if report.results:
            lines.append("\n## 详细问题列表")

            # 按严重程度分组
            by_severity = {}
            for result in report.results:
                sev = result.severity.value
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(result)

            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                if severity in by_severity:
                    lines.append(f"\n### {severity.upper()} - {len(by_severity[severity])}个问题")
                    for result in by_severity[severity]:
                        loc = f"**{result.location.file_path}:{result.location.line_number}**" if result.location else ""
                        lines.append(f"\n#### {result.check_name} {loc}")
                        lines.append(f"- **问题**: {result.message}")
                        if result.suggestion:
                            lines.append(f"- **建议**: {result.suggestion}")
                        if result.location and result.location.snippet:
                            lines.append(f"```\n{result.location.snippet}\n```")

        # 建议
        if report.recommendations:
            lines.append("\n## 改进建议")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")

        return '\n'.join(lines)


class HTMLReporter(Reporter):
    """HTML格式报告生成器"""

    def generate(self, report: AuditReport) -> str:
        """生成HTML格式报告"""
        from datetime import datetime

        # 获取评分颜色
        score_color = self._get_score_color(report.summary.overall_score)

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码审核报告 - {report.project_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin-bottom: 10px; }}
        .score-card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .score {{ font-size: 72px; font-weight: bold; color: {score_color}; text-align: center; }}
        .grade {{ font-size: 36px; text-align: center; color: #666; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }}
        .stat-item {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ font-size: 12px; color: #666; }}
        .section {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ margin-bottom: 15px; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .severity-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; margin-right: 10px; }}
        .critical {{ background: #dc3545; }}
        .high {{ background: #fd7e14; }}
        .medium {{ background: #ffc107; color: #333; }}
        .low {{ background: #28a745; }}
        .info {{ background: #17a2b8; }}
        .issue {{ padding: 15px; border-left: 4px solid #667eea; margin-bottom: 15px; background: #f8f9fa; }}
        .issue h4 {{ margin-bottom: 5px; }}
        .issue-meta {{ font-size: 12px; color: #666; margin-bottom: 8px; }}
        .issue-suggestion {{ background: #e7f3ff; padding: 10px; border-radius: 5px; font-size: 14px; }}
        .skill-item {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 20px; margin: 5px; }}
        .code-snippet {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Consolas', monospace; font-size: 13px; }}
        .footer {{ text-align: center; color: #666; margin-top: 30px; padding: 20px; }}
        @media (max-width: 768px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 代码审核报告</h1>
            <p>项目: <strong>{report.project_name}</strong></p>
            <p>审核日期: {report.audit_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="score-card">
            <div class="score">{report.summary.overall_score:.1f}</div>
            <div class="grade">等级: {report.summary.grade}</div>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{report.summary.total_files}</div>
                    <div class="stat-label">文件数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{report.summary.total_lines}</div>
                    <div class="stat-label">代码行数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{report.summary.total_checks}</div>
                    <div class="stat-label">检查项</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(report.results)}</div>
                    <div class="stat-label">发现问题</div>
                </div>
            </div>
        </div>
"""

        # 问题分类统计
        if report.summary.issues_by_severity:
            html += f"""
        <div class="section">
            <h2>📊 问题统计</h2>
"""
            for severity, count in report.summary.issues_by_severity.items():
                html += f'                <span class="severity-badge {severity.value}">{severity.value.upper()}: {count}</span>\n'
            html += "        </div>\n"

        # 识别的技能
        if report.skills_inventory:
            html += f"""
        <div class="section">
            <h2>🛠️ 识别的技术栈</h2>
            <div>
"""
            for skill in report.skills_inventory:
                html += f'                <span class="skill-item">{skill.name} ({skill.level.value})</span>\n'
            html += """
            </div>
        </div>
"""

        # 详细问题列表
        if report.results:
            # 按严重程度分组
            by_severity = {}
            for result in report.results:
                sev = result.severity.value
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(result)

            html += f"""
        <div class="section">
            <h2>🐛 详细问题</h2>
"""

            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                if severity in by_severity:
                    html += f'<h3 style="margin-top:20px;">{severity.upper()} - {len(by_severity[severity])}个问题</h3>\n'
                    for result in by_severity[severity]:
                        loc = f"{result.location.file_path}:{result.location.line_number}" if result.location else ""
                        snippet_html = f'<pre class="code-snippet">{result.location.snippet if result.location and result.location.snippet else "N/A"}</pre>' if result.location and result.location.snippet else ""

                        html += f"""
            <div class="issue">
                <h4>{result.check_name} <span class="severity-badge {severity}">{severity}</span></h4>
                <div class="issue-meta">位置: {loc}</div>
                <p>{result.message}</p>
                {snippet_html}
                <div class="issue-suggestion">💡 建议: {result.suggestion if result.suggestion else "请审查并修复此问题"}</div>
            </div>
"""

            html += "        </div>\n"

        # 建议
        if report.recommendations:
            html += f"""
        <div class="section">
            <h2>💡 改进建议</h2>
            <ol>
"""
            for rec in report.recommendations:
                html += f"                <li>{rec}</li>\n"
            html += """
            </ol>
        </div>
"""

        html += f"""
        <div class="footer">
            <p>由 MiniMax Agent 代码审核工具生成 | 审核时长: {report.duration_seconds:.2f}秒</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def _get_score_color(self, score: float) -> str:
        """根据评分获取颜色"""
        if score >= 90:
            return "#28a745"  # 绿色
        elif score >= 70:
            return "#ffc107"  # 黄色
        elif score >= 50:
            return "#fd7e14"  # 橙色
        else:
            return "#dc3545"  # 红色


class ConsoleReporter(Reporter):
    """控制台格式报告生成器"""

    def generate(self, report: AuditReport) -> str:
        """生成控制台格式报告"""
        lines = []

        # 标题
        lines.append("\n" + "=" * 60)
        lines.append("             📋 代码审核报告")
        lines.append("=" * 60)
        lines.append(f"  项目: {report.project_name}")
        lines.append(f"  日期: {report.audit_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        # 评分
        lines.append(f"\n  总体评分: {report.summary.overall_score:.1f}/100  [{report.summary.grade}]")
        lines.append(f"  文件数量: {report.summary.total_files}")
        lines.append(f"  代码行数: {report.summary.total_lines}")
        lines.append(f"  检查项数: {report.summary.total_checks}")
        lines.append(f"  发现问题: {len(report.results)}")

        # 问题统计
        if report.summary.issues_by_severity:
            lines.append("\n  问题分类统计:")
            for severity, count in report.summary.issues_by_severity.items():
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢', 'info': '🔵'}.get(severity.value, '⚪')
                lines.append(f"    {emoji} {severity.value.upper()}: {count}")

        # 识别的技能
        if report.skills_inventory:
            lines.append("\n  识别的技术栈:")
            for skill in report.skills_inventory[:10]:
                lines.append(f"    • {skill.name} ({skill.level.value})")
            if len(report.skills_inventory) > 10:
                lines.append(f"    ... 还有 {len(report.skills_inventory) - 10} 项")

        # 关键问题
        critical_issues = [r for r in report.results if r.severity.value in ['critical', 'high']]
        if critical_issues:
            lines.append(f"\n  ⚠️  关键问题 ({len(critical_issues)}):")
            for result in critical_issues[:5]:
                loc = f"[{result.location.file_path}:{result.location.line_number}]" if result.location else ""
                lines.append(f"    • {result.check_name} {loc}")
                lines.append(f"      {result.message[:60]}...")
            if len(critical_issues) > 5:
                lines.append(f"    ... 还有 {len(critical_issues) - 5} 个问题")

        # 建议
        if report.recommendations:
            lines.append("\n  改进建议:")
            for i, rec in enumerate(report.recommendations[:5], 1):
                lines.append(f"    {i}. {rec[:50]}...")
            if len(report.recommendations) > 5:
                lines.append(f"    ... 还有 {len(report.recommendations) - 5} 条建议")

        lines.append("\n" + "=" * 60)
        lines.append(f"  审核完成 | 耗时: {report.duration_seconds:.2f}秒")
        lines.append("=" * 60 + "\n")

        return '\n'.join(lines)
