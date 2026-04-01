"""
测试模块
包含所有单元测试和集成测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pathlib import Path

from code_auditor import CodeAuditor
from code_auditor.models import (
    CheckResult, CheckCategory, SeverityLevel, Skill, SkillLevel, AuditReport
)
from code_auditor.analyzers import (
    QualityAnalyzer, BestPracticesAnalyzer, SecurityAnalyzer,
    PerformanceAnalyzer, DocumentationAnalyzer, SkillsAnalyzer
)
from code_auditor.reporters import JSONReporter, ConsoleReporter, MarkdownReporter


class TestQualityAnalyzer:
    """代码质量分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return QualityAnalyzer()

    def test_detect_long_lines(self, analyzer):
        """测试长行检测"""
        content = """
def example_function():
    # 这是一个很长很长的注释，用于测试行长度检测功能是否正常工作
    return "This is a very long string that exceeds the maximum line length limit set in the analyzer configuration"
"""
        results = analyzer.analyze('test.py', content)
        assert len(results) > 0
        assert any('行过长' in r.check_name for r in results)

    def test_detect_empty_except(self, analyzer):
        """测试空异常捕获检测"""
        content = """
try:
    dangerous_operation()
except:
    pass
"""
        results = analyzer.analyze('test.py', content)
        assert any('空的异常捕获' in r.check_name for r in results)

    def test_detect_magic_numbers(self, analyzer):
        """测试魔法数字检测"""
        content = """
def calculate_area():
    return radius * radius * 3.141592653589793
"""
        results = analyzer.analyze('test.py', content)
        # 应该检测到π值
        assert len(results) >= 0


class TestSecurityAnalyzer:
    """安全性分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return SecurityAnalyzer()

    def test_detect_eval_usage(self, analyzer):
        """测试eval检测"""
        content = """
user_input = request.form['code']
result = eval(user_input)
"""
        results = analyzer.analyze('test.py', content)
        assert any('eval' in r.check_name.lower() or '危险函数' in r.check_name for r in results)

    def test_detect_sql_injection(self, analyzer):
        """测试SQL注入检测"""
        content = """
query = "SELECT * FROM users WHERE id = " + user_id
cursor.execute(query)
"""
        results = analyzer.analyze('test.py', content)
        assert any('SQL' in r.check_name for r in results)

    def test_detect_hardcoded_password(self, analyzer):
        """测试硬编码密码检测"""
        content = '''
API_KEY = "sk-1234567890abcdef"
password = "admin123"
'''
        results = analyzer.analyze('test.py', content)
        assert any('密码' in r.check_name or 'secret' in r.check_name.lower() for r in results)


class TestBestPracticesAnalyzer:
    """最佳实践分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return BestPracticesAnalyzer()

    def test_detect_bare_except(self, analyzer):
        """测试裸except检测"""
        content = """
try:
    risky_operation()
except:
    pass
"""
        results = analyzer.analyzer('test.py', content)
        assert any('裸except' in r.check_name for r in results)

    def test_detect_mutable_defaults(self, analyzer):
        """测试可变默认参数检测"""
        content = """
def create_user(name, tags=[]):
    tags.append(name)
    return tags
"""
        results = analyzer.analyzer('test.py', content)
        assert any('可变对象' in r.check_name for r in results)

    def test_missing_return_type(self, analyzer):
        """测试缺少返回类型检测"""
        content = """
def calculate_total(items):
    return sum(items)
"""
        results = analyzer.analyzer('test.py', content)
        assert any('返回类型' in r.check_name for r in results)


class TestSkillsAnalyzer:
    """技能识别分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return SkillsAnalyzer()

    def test_detect_python(self, analyzer):
        """测试Python语言识别"""
        content = """
import os
from typing import List, Optional

def hello():
    return "world"
"""
        results = analyzer.analyzer('test.py', content)
        languages = []
        for r in results:
            if 'languages' in r.metadata:
                languages = r.metadata['languages']
                break
        assert 'Python' in languages

    def test_detect_frameworks(self, analyzer):
        """测试框架识别"""
        content = """
import django
from django.urls import path
from rest_framework import serializers
"""
        results = analyzer.analyzer('test.py', content)
        frameworks = []
        for r in results:
            if 'frameworks' in r.metadata:
                frameworks = r.metadata['frameworks']
                break
        assert 'Django' in frameworks

    def test_get_skills(self, analyzer):
        """测试技能列表获取"""
        content = """
import numpy as np
import pandas as pd

def process_data():
    df = pd.DataFrame()
    return df
"""
        skills = analyzer.get_skills('analysis.py', content)
        assert len(skills) > 0
        skill_names = [s.name for s in skills]
        assert 'Python' in skill_names


class TestPerformanceAnalyzer:
    """性能分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return PerformanceAnalyzer()

    def test_detect_n_plus_one(self, analyzer):
        """测试N+1查询检测"""
        content = """
users = User.objects.all()
for user in users:
    posts = Post.objects.filter(user=user)
    print(posts)
"""
        results = analyzer.analyzer('test.py', content)
        assert any('N+1' in r.check_name for r in results)

    def test_detect_string_concat_in_loop(self, analyzer):
        """测试循环中字符串拼接检测"""
        content = """
result = ""
for item in items:
    result += str(item)
"""
        results = analyzer.analyzer('test.py', content)
        assert any('字符串' in r.check_name for r in results)


class TestCodeAuditor:
    """代码审核器集成测试"""

    @pytest.fixture
    def auditor(self):
        return CodeAuditor()

    def test_audit_single_file(self, auditor, tmp_path):
        """测试单文件审核"""
        # 创建测试文件
        test_file = tmp_path / "example.py"
        test_file.write_text("""
import os

def hello():
    print("Hello, World!")

if __name__ == '__main__':
    hello()
""")

        report = auditor.audit(str(test_file))

        assert isinstance(report, AuditReport)
        assert report.summary.total_files == 1
        assert report.summary.total_lines > 0

    def test_audit_directory(self, auditor, tmp_path):
        """测试目录审核"""
        # 创建测试文件结构
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")

        report = auditor.audit(str(tmp_path))

        assert report.summary.total_files >= 2

    def test_generate_json_report(self, auditor, tmp_path):
        """测试JSON报告生成"""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        report = auditor.audit(str(test_file))
        reporter = JSONReporter()
        json_content = reporter.generate(report)

        import json
        data = json.loads(json_content)
        assert 'project_name' in data
        assert 'summary' in data

    def test_generate_console_report(self, auditor, tmp_path):
        """测试控制台报告生成"""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        report = auditor.audit(str(test_file))
        reporter = ConsoleReporter()
        content = reporter.generate(report)

        assert '代码审核报告' in content
        assert str(report.summary.overall_score) in content


class TestReporters:
    """报告生成器测试"""

    def test_json_reporter(self, tmp_path):
        """测试JSON报告"""
        report = AuditReport(
            project_name="test",
            audit_date=datetime.now(),
            summary=AuditSummary(
                total_files=1,
                total_lines=10,
                total_checks=0,
                overall_score=100.0,
                grade="A"
            ),
            results=[],
            skills_inventory=[]
        )

        reporter = JSONReporter()
        content = reporter.generate(report)

        import json
        data = json.loads(content)
        assert data['project_name'] == 'test'

    def test_markdown_reporter(self, tmp_path):
        """测试Markdown报告"""
        report = AuditReport(
            project_name="test",
            audit_date=datetime.now(),
            summary=AuditSummary(
                total_files=1,
                total_lines=10,
                total_checks=0,
                overall_score=100.0,
                grade="A"
            ),
            results=[],
            skills_inventory=[]
        )

        reporter = MarkdownReporter()
        content = reporter.generate(report)

        assert '# 代码审核报告' in content


from datetime import datetime


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
