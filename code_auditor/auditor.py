"""
代码审核器主类
整合所有分析器并提供统一的审核接口
"""

import os
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .models import (
    CheckResult, AuditReport, AuditSummary, Skill,
    SeverityLevel, CheckCategory, SkillLevel
)
from .analyzers import (
    QualityAnalyzer,
    BestPracticesAnalyzer,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    DocumentationAnalyzer,
    SkillsAnalyzer,
    JavaMavenAnalyzer,
    CustomRulesAnalyzer
)
from .reporters import Reporter, ReportType
from .rules_loader import RulesLoader, CheckRule


class CodeAuditor:
    """代码审核器主类"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化代码审核器

        Args:
            config: 配置选项
        """
        self.config = config or {}
        self.analyzers = []
        self.results: List[CheckResult] = []
        self.skills: List[Skill] = []
        self.file_results: Dict[str, List[CheckResult]] = {}

        # 性能优化配置
        self._max_workers = self.config.get('max_workers', min(8, os.cpu_count() or 4))
        self._enable_parallel = self.config.get('enable_parallel', True)
        
        # 正则表达式缓存（避免重复编译）
        self._regex_cache: Dict[str, re.Pattern] = {}
        self._cache_lock = threading.Lock()

        # 初始化分析器
        self._init_analyzers()

        # 支持的文件扩展名
        self.supported_extensions = self.config.get(
            'extensions',
            ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h']
        )

        # 排除的目录
        self.exclude_dirs = set(self.config.get(
            'exclude_dirs',
            ['node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build', '.idea', '.vscode']
        ))

    def _init_analyzers(self):
        """初始化所有分析器"""
        # 根据配置启用/禁用特定分析器
        enabled_analyzers = self.config.get('enabled_analyzers', 'all')
        
        # 处理 enabled_analyzers 可能是字符串或列表的情况
        if isinstance(enabled_analyzers, str):
            enabled_analyzers = [enabled_analyzers]
        
        is_all = 'all' in enabled_analyzers

        if is_all or 'quality' in enabled_analyzers:
            self.analyzers.append(QualityAnalyzer(self.config))

        if is_all or 'best_practices' in enabled_analyzers:
            self.analyzers.append(BestPracticesAnalyzer(self.config))

        if is_all or 'security' in enabled_analyzers:
            self.analyzers.append(SecurityAnalyzer(self.config))

        if is_all or 'performance' in enabled_analyzers:
            self.analyzers.append(PerformanceAnalyzer(self.config))

        if is_all or 'documentation' in enabled_analyzers:
            self.analyzers.append(DocumentationAnalyzer(self.config))

        if is_all or 'skills' in enabled_analyzers:
            self.analyzers.append(SkillsAnalyzer(self.config))

        # 初始化自定义规则分析器（如果配置了规则文件）
        if is_all or 'custom' in enabled_analyzers:
            custom_analyzer = CustomRulesAnalyzer(self.config)
            if custom_analyzer._loaded_rules:  # 只有加载了规则才添加
                self.analyzers.append(custom_analyzer)

    def audit(self, path: str, recursive: bool = True) -> AuditReport:
        """
        审核指定路径的代码

        Args:
            path: 文件或目录路径
            recursive: 是否递归处理子目录

        Returns:
            审核报告
        """
        start_time = time.time()

        # 重置状态
        self.results = []
        self.skills = []
        self.file_results = {}

        # 获取要审核的文件
        files = self._get_files(path, recursive)

        # 并行处理文件
        self._process_files(files)

        # 计算摘要
        summary = self._calculate_summary(files, self.results)

        # 生成报告
        report = AuditReport(
            project_name=Path(path).name,
            audit_date=datetime.now(),
            summary=summary,
            results=self.results,
            file_results=self.file_results,
            skills_inventory=self.skills,
            recommendations=self._generate_recommendations(),
            duration_seconds=time.time() - start_time
        )

        return report

    def audit_files(self, files: List[str]) -> AuditReport:
        """
        审核指定的文件列表

        Args:
            files: 文件路径列表

        Returns:
            审核报告
        """
        start_time = time.time()

        # 重置状态
        self.results = []
        self.skills = []
        self.file_results = {}

        # 处理文件
        self._process_files(files)

        # 计算摘要
        summary = self._calculate_summary(files, self.results)

        # 生成报告
        report = AuditReport(
            project_name="Multi-file Audit",
            audit_date=datetime.now(),
            summary=summary,
            results=self.results,
            file_results=self.file_results,
            skills_inventory=self.skills,
            recommendations=self._generate_recommendations(),
            duration_seconds=time.time() - start_time
        )

        return report

    def _get_files(self, path: str, recursive: bool) -> List[str]:
        """获取要审核的文件列表"""
        files = []

        path_obj = Path(path)

        if path_obj.is_file():
            if self._is_supported_file(path):
                files.append(str(path_obj.absolute()))
        elif path_obj.is_dir():
            if recursive:
                for root, dirs, filenames in os.walk(path):
                    # 过滤排除目录
                    dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        if self._is_supported_file(file_path):
                            files.append(file_path)
            else:
                for file_path in path_obj.iterdir():
                    if file_path.is_file() and self._is_supported_file(str(file_path)):
                        files.append(str(file_path.absolute()))

        return files

    def _is_supported_file(self, file_path: str) -> bool:
        """检查文件是否支持审核"""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions

    def _process_files(self, files: List[str]):
        """并行处理所有文件"""
        if not files:
            return
        
        # 小文件数量或禁用并行时使用串行处理
        if len(files) <= 2 or not self._enable_parallel:
            for file_path in files:
                self._process_single_file(file_path)
            return
        
        # 线程安全的锁
        results_lock = threading.Lock()
        
        def process_file_thread(file_path: str):
            """线程处理函数"""
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                file_results = []
                file_skills = []

                for analyzer in self.analyzers:
                    if analyzer.can_analyze(file_path):
                        # 运行分析器
                        results = analyzer.analyze(file_path, content)
                        file_results.extend(results)

                        # 获取技能信息
                        if hasattr(analyzer, 'get_skills'):
                            skills = analyzer.get_skills(file_path, content)
                            file_skills.extend(skills)

                # 线程安全地更新全局结果
                with results_lock:
                    self.results.extend(file_results)
                    self.skills.extend(file_skills)
                    self.file_results[file_path] = file_results

            except Exception as e:
                with results_lock:
                    print(f"处理文件 {file_path} 时出错: {e}")
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [executor.submit(process_file_thread, f) for f in files]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"处理文件时出错: {e}")

    def _process_single_file(self, file_path: str):
        """处理单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            file_results = []
            file_skills = []

            for analyzer in self.analyzers:
                if analyzer.can_analyze(file_path):
                    # 运行分析器
                    results = analyzer.analyze(file_path, content)
                    file_results.extend(results)

                    # 获取技能信息
                    if hasattr(analyzer, 'get_skills'):
                        skills = analyzer.get_skills(file_path, content)
                        file_skills.extend(skills)

            # 更新全局结果
            self.results.extend(file_results)
            self.skills.extend(file_skills)
            self.file_results[file_path] = file_results

        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

    def _calculate_summary(self, files: List[str], results: List[CheckResult]) -> AuditSummary:
        """计算审核摘要"""
        total_lines = 0
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    total_lines += len(f.readlines())
            except:
                pass

        # 统计问题
        issues_by_severity = {}
        issues_by_category = {}

        for result in results:
            # 按严重程度统计
            sev = result.severity
            issues_by_severity[sev] = issues_by_severity.get(sev, 0) + 1

            # 按类别统计
            cat = result.category
            issues_by_category[cat] = issues_by_category.get(cat, 0) + 1

        # 计算评分
        overall_score = self._calculate_score(issues_by_severity, len(files))

        # 合并去重技能
        unique_skills = self._deduplicate_skills(self.skills)

        summary = AuditSummary(
            total_files=len(files),
            total_lines=total_lines,
            total_checks=len(results),
            issues_by_severity=issues_by_severity,
            issues_by_category=issues_by_category,
            skills_detected=unique_skills,
            overall_score=overall_score
        )

        summary.grade = summary.calculate_grade()

        return summary

    def _calculate_score(
        self,
        issues_by_severity: Dict[SeverityLevel, int],
        file_count: int
    ) -> float:
        """
        计算代码评分

        基于问题数量和严重程度计算0-100的评分
        """
        if file_count == 0:
            return 100.0

        # 权重配置
        weights = {
            SeverityLevel.CRITICAL: 25,
            SeverityLevel.HIGH: 15,
            SeverityLevel.MEDIUM: 5,
            SeverityLevel.LOW: 2,
            SeverityLevel.INFO: 0,
        }

        total_penalty = 0
        for severity, count in issues_by_severity.items():
            total_penalty += count * weights.get(severity, 0)

        # 根据文件数量调整
        adjusted_penalty = total_penalty / max(1, file_count / 10)

        # 计算最终评分
        score = max(0, min(100, 100 - adjusted_penalty))

        return round(score, 1)

    def _deduplicate_skills(self, skills: List[Skill]) -> List[Skill]:
        """去重并合并技能"""
        skill_dict: Dict[str, Skill] = {}

        for skill in skills:
            key = f"{skill.name}:{skill.category}"
            if key not in skill_dict:
                skill_dict[key] = skill
            else:
                # 保留置信度更高的
                if skill.confidence > skill_dict[key].confidence:
                    skill_dict[key] = skill

        return list(skill_dict.values())

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于问题统计生成建议
        critical_count = self.results.count(lambda r: r.severity == SeverityLevel.CRITICAL)
        high_count = self.results.count(lambda r: r.severity == SeverityLevel.HIGH)

        if critical_count > 0:
            recommendations.append(
                f"存在 {critical_count} 个严重问题，请优先修复安全问题"
            )

        if high_count > 0:
            recommendations.append(
                f"存在 {high_count} 个高优先级问题，建议审查并修复"
            )

        # 检查是否有安全问题
        has_security = any(r.category == CheckCategory.SECURITY for r in self.results)
        if has_security:
            recommendations.append(
                "代码存在安全风险，建议进行安全审计并实施安全最佳实践"
            )

        # 检查文档完整性
        doc_count = sum(1 for r in self.results if '文档' in r.check_name)
        if doc_count > len(self.results) * 0.3:
            recommendations.append(
                "代码文档覆盖率较低，建议完善API文档和注释"
            )

        # 检查是否有性能问题
        has_performance = any(r.category == CheckCategory.PERFORMANCE for r in self.results)
        if has_performance:
            recommendations.append(
                "存在性能优化空间，建议审查数据库查询和算法复杂度"
            )

        # 检查技能多样性
        if len(self.skills) < 3:
            recommendations.append(
                "代码技术栈较为单一，考虑引入更多现代工具和框架"
            )

        return recommendations[:10]  # 最多返回10条建议

    def generate_report(
        self,
        report: AuditReport,
        output_path: Optional[str] = None,
        report_type: ReportType = ReportType.CONSOLE
    ) -> str:
        """
        生成报告

        Args:
            report: 审核报告
            output_path: 输出文件路径
            report_type: 报告类型

        Returns:
            报告内容
        """
        reporter = Reporter.get_reporter(report_type, output_path)
        content = reporter.generate(report)

        if output_path:
            reporter.save(content)

        return content

    def load_custom_rules(self, rule_file: str) -> int:
        """
        加载自定义规则文件

        Args:
            rule_file: 规则文件路径 (支持 JSON/YAML)

        Returns:
            加载的规则数量
        """
        loader = RulesLoader()
        rules = loader.load_from_file(rule_file)
        
        if rules:
            # 创建或更新自定义规则分析器
            custom_analyzer = None
            for analyzer in self.analyzers:
                if isinstance(analyzer, CustomRulesAnalyzer):
                    custom_analyzer = analyzer
                    break
            
            if custom_analyzer is None:
                custom_analyzer = CustomRulesAnalyzer(self.config)
                self.analyzers.append(custom_analyzer)
            
            custom_analyzer._loaded_rules.extend(rules)
        
        return len(rules)

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust', 'C', 'C++']

    def get_cached_regex(self, pattern: str, flags: int = 0) -> re.Pattern:
        """获取缓存的正则表达式（性能优化）"""
        cache_key = f"{pattern}:{flags}"
        
        if cache_key not in self._regex_cache:
            with self._cache_lock:
                if cache_key not in self._regex_cache:
                    self._regex_cache[cache_key] = re.compile(pattern, flags)
        
        return self._regex_cache[cache_key]

    def get_analyzer_info(self) -> List[Dict[str, str]]:
        """获取分析器信息"""
        return [
            {
                'name': analyzer.name,
                'description': analyzer.description,
                'category': analyzer.category.value
            }
            for analyzer in self.analyzers
        ]
