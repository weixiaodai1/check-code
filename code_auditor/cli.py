#!/usr/bin/env python3
"""
代码审核工具 CLI 工具
提供命令行界面进行代码审核
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Optional

from code_auditor import CodeAuditor
from code_auditor.reporters import ReportType


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='code-auditor',
        description='专业级代码审核工具 - 检查代码质量、安全性和最佳实践',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 审核整个项目
  code-auditor /path/to/project

  # 审核特定文件
  code-auditor main.py utils.py

  # 生成HTML报告
  code-auditor /path/to/project -o report.html --format html

  # 只检查安全问题
  code-auditor /path/to/project --analyzers security

  # 审核并输出JSON格式
  code-auditor /path/to/project -o report.json --format json

  # 显示支持的选项
  code-auditor --info
        """
    )

    # 位置参数
    parser.add_argument(
        'paths',
        nargs='*',
        help='要审核的文件或目录路径'
    )

    # 基本选项
    parser.add_argument(
        '-o', '--output',
        help='输出报告文件路径'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['console', 'json', 'html', 'markdown'],
        default='console',
        help='报告输出格式 (默认: console)'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=True,
        help='递归处理子目录 (默认: 开启)'
    )

    # 分析器选项
    parser.add_argument(
        '-a', '--analyzers',
        nargs='+',
        choices=['quality', 'best_practices', 'security', 'performance', 'documentation', 'skills', 'custom', 'all'],
        default=['all'],
        help='启用的分析器'
    )

    # 自定义规则选项
    parser.add_argument(
        '--rule-file', '--rules',
        nargs='+',
        dest='rule_files',
        help='自定义规则文件路径 (支持 JSON/YAML)'
    )

    parser.add_argument(
        '--rules-dir', '-rd',
        help='自定义规则目录路径'
    )

    # 过滤选项
    parser.add_argument(
        '-e', '--extensions',
        nargs='+',
        default=['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp'],
        help='要审核的文件扩展名'
    )

    parser.add_argument(
        '--exclude-dirs',
        nargs='+',
        default=['node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build'],
        help='排除的目录'
    )

    # 严重程度过滤
    parser.add_argument(
        '--min-severity',
        choices=['critical', 'high', 'medium', 'low', 'info'],
        help='只显示此严重程度及以上的问题'
    )

    # 信息选项
    parser.add_argument(
        '--info',
        action='store_true',
        help='显示支持的编程语言和分析器信息'
    )

    parser.add_argument(
        '--list-analyzers',
        action='store_true',
        help='列出所有可用的分析器'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='code-auditor v1.0.0'
    )

    # 详细选项
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细输出'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='只显示摘要，不显示详细信息'
    )

    return parser


def show_info(auditor: CodeAuditor):
    """显示工具信息"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    代码审核工具 (Code Auditor)                ║
║                       专业级代码质量分析                        ║
╚═══════════════════════════════════════════════════════════════╝

版本: 1.0.0
作者: MiniMax Agent
""")

    # 支持的语言
    print("支持的编程语言:")
    print("-" * 40)
    languages = auditor.get_supported_languages()
    for lang in languages:
        print(f"  • {lang}")

    print("\n" + "=" * 40 + "\n")

    # 分析器信息
    print("可用分析器:")
    print("-" * 40)
    analyzers = auditor.get_analyzer_info()
    for info in analyzers:
        print(f"\n  [{info['category']}]")
        print(f"    名称: {info['name']}")
        print(f"    描述: {info['description']}")


def main(args: Optional[list] = None) -> int:
    """主函数"""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # 处理 --info 选项
    if parsed_args.info:
        auditor = CodeAuditor()
        show_info(auditor)
        return 0

    # 处理 --list-analyzers 选项
    if parsed_args.list_analyzers:
        auditor = CodeAuditor()
        analyzers = auditor.get_analyzer_info()
        for info in analyzers:
            print(f"[{info['category']}] {info['name']}: {info['description']}")
        return 0

    # 检查路径参数
    if not parsed_args.paths:
        parser.print_help()
        print("\n错误: 请提供要审核的文件或目录路径")
        return 1

    # 构建配置
    config = {
        'enabled_analyzers': parsed_args.analyzers,
        'extensions': parsed_args.extensions,
        'exclude_dirs': parsed_args.exclude_dirs,
        'rule_files': parsed_args.rule_files or [],
        'rule_dirs': [parsed_args.rules_dir] if parsed_args.rules_dir else [],
        'max_workers': min(8, (os.cpu_count() or 4)),  # 性能优化
    }

    # 创建审核器
    auditor = CodeAuditor(config)

    # 显示审核开始信息
    if not parsed_args.quiet:
        print(f"开始审核代码...")
        print(f"分析器: {', '.join(parsed_args.analyzers)}")
        print(f"格式: {parsed_args.format}")
        print()

    # 执行审核
    try:
        if len(parsed_args.paths) == 1:
            # 单个路径
            report = auditor.audit(
                parsed_args.paths[0],
                recursive=parsed_args.recursive
            )
        else:
            # 多个路径
            all_files = []
            for path in parsed_args.paths:
                if Path(path).is_file():
                    all_files.append(path)
                else:
                    file_report = auditor.audit(path, recursive=True)
                    all_files.extend(file_report.file_results.keys())

            report = auditor.audit_files(all_files)

    except Exception as e:
        print(f"错误: 审核过程中出现异常: {e}", file=sys.stderr)
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # 生成报告
    output_path = parsed_args.output
    report_format = {
        'console': ReportType.CONSOLE,
        'json': ReportType.JSON,
        'html': ReportType.HTML,
        'markdown': ReportType.MARKDOWN
    }.get(parsed_args.format, ReportType.CONSOLE)

    content = auditor.generate_report(
        report,
        output_path=output_path,
        report_type=report_format
    )

    # 输出报告
    if not parsed_args.quiet or parsed_args.output:
        if parsed_args.format == 'console':
            print(content)
        elif not parsed_args.quiet:
            print(f"报告已生成: {output_path}")

    # 显示摘要（如果使用控制台输出且不是quiet模式）
    if parsed_args.format == 'console' and not parsed_args.quiet:
        print(f"\n审核完成!")
        print(f"  文件数: {report.summary.total_files}")
        print(f"  代码行数: {report.summary.total_lines}")
        print(f"  发现问题: {report.summary.total_checks}")
        print(f"  评分: {report.summary.overall_score}/100 ({report.summary.grade})")

        if report.skills_inventory:
            print(f"\n识别的技术栈: {', '.join([s.name for s in report.skills_inventory[:5]])}")

    # 返回退出码
    if report.summary.issues_by_severity.get('critical', 0) > 0:
        return 2  # 存在严重问题
    elif report.summary.issues_by_severity.get('high', 0) > 0:
        return 1  # 存在高优先级问题

    return 0


if __name__ == '__main__':
    sys.exit(main())
