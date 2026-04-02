

# 专业级代码审核工具

## 概述

专业级代码审核工具是一个全面的代码质量分析平台，能够检查代码质量、最佳实践、安全性、性能问题，并智能识别代码中使用的技术栈和开发技能。

## 功能特性

### 1. 多维度代码分析

- **代码质量分析**: 检查代码行长度、函数长度、复杂度、重复代码等
- **最佳实践验证**: 验证是否遵循业界编码规范和最佳实践
- **安全漏洞检测**: 检测SQL注入、XSS、命令注入等常见安全风险
- **性能优化检查**: 发现N+1查询、低效算法等性能问题
- **文档完整性检查**: 评估代码文档的覆盖率和质量

### 2. 智能技能识别

自动识别代码中的专业技能和技术栈:

- 编程语言 (Python, JavaScript, TypeScript, Java, Go, Rust等)
- 框架和库 (Django, React, Spring, FastAPI等)
- 架构模式 (MVC, 微服务, Clean Architecture等)
- DevOps工具 (Docker, Kubernetes, CI/CD等)
- 云原生技术 (容器化, 服务网格, Serverless等)

### 3. 专业评分系统

- 0-100分综合评分
- A/B/C/D/F等级评估
- 按严重程度分类统计问题
- 改进建议自动生成

### 4. 多格式报告

- **控制台**: 实时输出，适合CI/CD集成
- **HTML**: 美观的可视化报告
- **JSON**: 程序化处理和数据分析
- **Markdown**: 文档化和分享

## 安装

### 使用pip安装

```bash
pip install code-auditor
```

### 从源码安装

```bash
git clone https://github.com/weixiaodai1/check-code
cd code-auditor
pip install -e .
```

## 快速开始

### 命令行使用

```bash
# 审核整个项目
code-auditor /path/to/project

# 审核特定文件
code-auditor main.py utils.py

# 生成HTML报告
code-auditor /path/to/project -o report.html --format html

# 只检查安全问题
code-auditor /path/to/project --analyzers security

# 显示帮助信息
code-auditor --help
```

### Python API使用

```python
from code_auditor import CodeAuditor
from code_auditor.reporters import ReportType

# 创建审核器
auditor = CodeAuditor({
    'enabled_analyzers': ['all'],
    'extensions': ['.py', '.js']
})

# 执行审核
report = auditor.audit('/path/to/project')

# 生成报告
auditor.generate_report(
    report,
    output_path='report.html',
    report_type=ReportType.HTML
)

# 查看结果
print(f"评分: {report.summary.overall_score}/100")
print(f"等级: {report.summary.grade}")
print(f"发现问题: {len(report.results)}")
print(f"识别技能: {[s.name for s in report.skills_inventory]}")
```

## 配置选项

### 分析器配置

```python
config = {
    # 启用的分析器
    'enabled_analyzers': [
        'quality',           # 代码质量
        'best_practices',    # 最佳实践
        'security',          # 安全性
        'performance',       # 性能
        'documentation',     # 文档
        'skills',            # 技能识别
        'all'                # 全部启用
    ],

    # 支持的文件扩展名
    'extensions': ['.py', '.js', '.ts', '.java'],

    # 排除的目录
    'exclude_dirs': ['node_modules', '.git', '__pycache__', 'venv']
}
```

### CLI参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出报告文件路径 | - |
| `-f, --format` | 报告格式 (console/json/html/markdown) | console |
| `-r, --recursive` | 递归处理子目录 | True |
| `-a, --analyzers` | 启用的分析器列表 | all |
| `-e, --extensions` | 文件扩展名列表 | .py等 |
| `--exclude-dirs` | 排除的目录 | node_modules等 |
| `-v, --verbose` | 显示详细输出 | False |

## 检查项目

### 代码质量 (Quality)

- QUAL001: 代码行过长
- QUAL002: 函数过长
- QUAL003: 代码重复
- QUAL004: 空的异常捕获
- QUAL005: 硬编码值
- QUAL006: 命名不一致
- QUAL007: 深层嵌套
- QUAL008: 魔法数字
- QUAL009: 死代码

### 最佳实践 (Best Practices)

- BP001: 裸except子句
- BP002: 资源未正确释放
- BP003: 缺少类型提示
- BP004: 缺少文档字符串
- BP005: 导入语句位置不当
- BP006: 可变默认参数
- BP007: 不当的列表推导式

### 安全性 (Security)

- SEC001: 使用危险函数 (eval, exec)
- SEC010: SQL注入风险
- SEC011: XSS跨站脚本
- SEC012: 命令注入
- SEC013: 敏感信息泄露
- SEC014: 不安全的随机数
- SEC015: 弱加密算法
- SEC016: 路径遍历
- SEC017: 不安全反序列化

### 性能 (Performance)

- PERF001: 嵌套过深的循环
- PERF002: 循环中字符串拼接
- PERF003: 不必要的列表拷贝
- PERF004: 低效数据结构
- PERF005: 全局变量使用
- PERF009: 循环中编译正则
- PERF010: N+1查询问题

### 文档 (Documentation)

- DOC001: 缺少模块文档
- DOC002: 函数缺少文档
- DOC005: 类缺少文档
- DOC006: 无意义注释
- DOC007: TODO/FIXME标记
- DOC008: API缺少文档

## 严重程度等级

| 等级 | 说明 | 建议 |
|------|------|------|
| CRITICAL | 严重安全问题或致命缺陷 | 必须立即修复 |
| HIGH | 高优先级问题 | 应尽快修复 |
| MEDIUM | 中等问题 | 建议修复 |
| LOW | 轻微问题 | 可以选择性修复 |
| INFO | 信息提示 | 参考性建议 |

## 技能识别

工具会自动识别以下类别:

### 编程语言

- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- C/C++

### 框架/库

- Web框架: Django, Flask, FastAPI, Express, NestJS
- 前端: React, Vue, Angular, Next.js
- 数据处理: Pandas, NumPy, TensorFlow, PyTorch
- 数据库: SQLAlchemy, Prisma, TypeORM, Mongoose

### 架构模式

- REST API
- GraphQL
- Microservices
- MVC/MVVM
- Clean Architecture
- Event-Driven

### DevOps技能

- Docker
- Kubernetes
- CI/CD (GitHub Actions, GitLab CI, Jenkins)
- Terraform
- AWS/Azure云服务

## 输出示例

### 控制台输出

```
============================================================
             📋 代码审核报告
============================================================
  项目: my-project
  日期: 2026-03-25 10:30:00
============================================================

  总体评分: 78.5/100  [C]
  文件数量: 15
  代码行数: 1234
  检查项数: 23
  发现问题: 8

  问题分类统计:
    🔴 CRITICAL: 1
    🟠 HIGH: 2
    🟡 MEDIUM: 3
    🟢 LOW: 2

  识别的技术栈:
    • Python (intermediate)
    • FastAPI (intermediate)
    • Docker (intermediate)

  ⚠️  关键问题 (3):
    • 使用危险函数: eval [src/eval_code.py:5]
      检测到使用eval()函数可能导致代码注入...
    • 潜在的SQL注入风险 [src/db.py:15]
      SQL查询使用字符串拼接...
    • 可能的N+1查询 [src/users.py:23]
      在循环中执行数据库查询...

============================================================
  审核完成 | 耗时: 2.35秒
============================================================
```

## 集成CI/CD

### GitHub Actions

```yaml
name: Code Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install code-auditor
        run: pip install code-auditor

      - name: Run audit
        run: |
          code-auditor . -o audit-report.html --format html

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: audit-report
          path: audit-report.html
```

## 常见问题

### Q: 如何忽略特定文件?
A: 使用 `--exclude-dirs` 参数排除目录，或在项目根目录创建 `.codeauditignore` 文件。

### Q: 如何自定义检查规则?
A: 可以通过继承 `BaseAnalyzer` 类创建自定义分析器。

### Q: 支持哪些编程语言?
A: 目前支持 Python, JavaScript, TypeScript, Java, Go, Rust, C, C++。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- GitHub: https://github.com/weixiaodai1/check-code
