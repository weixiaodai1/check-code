"""
技能识别分析器
识别代码中使用的技术栈、框架、库和开发技能
"""

from typing import List, Dict, Set, Tuple, Optional
import re
from pathlib import Path
from .base_analyzer import BaseAnalyzer
from ..models import (
    CheckResult, CheckCategory, SeverityLevel, Skill, SkillLevel, Location
)


class SkillsAnalyzer(BaseAnalyzer):
    """技能识别分析器"""

    # 编程语言特征
    LANGUAGES = {
        'Python': {
            'extensions': ['.py'],
            'patterns': [
                (r'\bimport\s+\w+', 0.7),
                (r'\bfrom\s+\w+\s+import', 0.7),
                (r'def\s+\w+\s*\(', 0.5),
                (r'class\s+\w+:', 0.5),
                (r'if\s+__name__\s*==', 0.8),
                (r'print\s*\(', 0.3),
                (r'self\.', 0.6),
                (r'@decorator', 0.5),
            ],
            'level_indicators': {
                'async def': SkillLevel.ADVANCED,
                'yield': SkillLevel.INTERMEDIATE,
                'typing.Optional': SkillLevel.INTERMEDIATE,
                'dataclass': SkillLevel.INTERMEDIATE,
                'abc.ABC': SkillLevel.ADVANCED,
                'metaclass': SkillLevel.EXPERT,
            }
        },
        'JavaScript': {
            'extensions': ['.js', '.jsx', '.mjs'],
            'patterns': [
                (r'\bconst\s+\w+\s*=', 0.6),
                (r'\blet\s+\w+\s*=', 0.6),
                (r'function\s+\w+\s*\(', 0.5),
                (r'=>', 0.5),
                (r'console\.log', 0.4),
                (r'require\s*\(', 0.6),
                (r'module\.exports', 0.7),
                (r'async\s+function', 0.5),
                (r'\.then\s*\(', 0.4),
            ],
            'level_indicators': {
                'async/await': SkillLevel.INTERMEDIATE,
                'Promise': SkillLevel.INTERMEDIATE,
                'generator': SkillLevel.ADVANCED,
                'Proxy': SkillLevel.ADVANCED,
                'Symbol': SkillLevel.ADVANCED,
            }
        },
        'TypeScript': {
            'extensions': ['.ts', '.tsx'],
            'patterns': [
                (r':\s*(?:string|number|boolean|any)\b', 0.7),
                (r'interface\s+\w+', 0.7),
                (r'type\s+\w+\s*=', 0.7),
                (r'<\w+>', 0.5),  # Generics
                (r'as\s+\w+', 0.5),
                (r'\benum\s+\w+', 0.6),
                (r'readonly\s+\w+', 0.6),
            ],
            'level_indicators': {
                'Generic<>': SkillLevel.INTERMEDIATE,
                'keyof': SkillLevel.ADVANCED,
                'Partial<': SkillLevel.ADVANCED,
                'readonly': SkillLevel.INTERMEDIATE,
                'strict': SkillLevel.ADVANCED,
            }
        },
        'Java': {
            'extensions': ['.java'],
            'patterns': [
                (r'public\s+class\s+\w+', 0.8),
                (r'public\s+static\s+void\s+main', 0.9),
                (r'System\.out\.println', 0.7),
                (r'@Override', 0.6),
                (r'extends\s+\w+', 0.5),
                (r'implements\s+\w+', 0.5),
                (r'new\s+\w+\[\]', 0.4),
            ],
            'level_indicators': {
                'synchronized': SkillLevel.INTERMEDIATE,
                '@Entity': SkillLevel.ADVANCED,
                '@Transactional': SkillLevel.ADVANCED,
                'CompletableFuture': SkillLevel.ADVANCED,
                'Stream<>': SkillLevel.INTERMEDIATE,
            }
        },
        'Go': {
            'extensions': ['.go'],
            'patterns': [
                (r'package\s+\w+', 0.9),
                (r'func\s+\w+\s*\(', 0.7),
                (r'go\s+func', 0.8),
                (r'defer\s+', 0.6),
                (r'chan\s+\w+', 0.7),
                (r'goroutine', 0.8),
                (r'interface\s*\{', 0.5),
            ],
            'level_indicators': {
                'go func': SkillLevel.INTERMEDIATE,
                'chan': SkillLevel.ADVANCED,
                'select': SkillLevel.ADVANCED,
                'defer': SkillLevel.INTERMEDIATE,
                'goroutine': SkillLevel.ADVANCED,
            }
        },
        'Rust': {
            'extensions': ['.rs'],
            'patterns': [
                (r'fn\s+\w+\s*\(', 0.7),
                (r'let\s+mut\s+', 0.6),
                (r'impl\s+\w+', 0.6),
                (r'pub\s+fn', 0.5),
                (r'->.*\{', 0.5),
                (r'&\w+', 0.4),
                (r'Option<', 0.6),
                (r'Result<', 0.6),
            ],
            'level_indicators': {
                'unsafe': SkillLevel.ADVANCED,
                ' lifetimes': SkillLevel.EXPERT,
                'trait': SkillLevel.ADVANCED,
                'Box<>': SkillLevel.INTERMEDIATE,
                'Rc<>': SkillLevel.ADVANCED,
            }
        },
        'C': {
            'extensions': ['.c', '.h'],
            'patterns': [
                (r'#include\s*<', 0.8),
                (r'int\s+main\s*\(', 0.9),
                (r'printf\s*\(', 0.7),
                (r'scanf\s*\(', 0.7),
                (r'malloc\s*\(', 0.6),
                (r'free\s*\(', 0.6),
                (r'struct\s+\w+', 0.5),
            ],
            'level_indicators': {
                'malloc/free': SkillLevel.INTERMEDIATE,
                'pointer': SkillLevel.INTERMEDIATE,
                'bitwise': SkillLevel.INTERMEDIATE,
            }
        },
        'C++': {
            'extensions': ['.cpp', '.hpp', '.cc'],
            'patterns': [
                (r'#include\s*<iostream>', 0.7),
                (r'std::', 0.6),
                (r'class\s+\w+\s*:\s*public', 0.6),
                (r'template\s*<', 0.7),
                (r'virtual\s+', 0.5),
                (r'new\s+\w+\[', 0.5),
                (r'nullptr', 0.5),
            ],
            'level_indicators': {
                'template': SkillLevel.ADVANCED,
                'virtual': SkillLevel.INTERMEDIATE,
                'STL': SkillLevel.INTERMEDIATE,
                'move semantics': SkillLevel.ADVANCED,
            }
        },
    }

    # 框架和库
    FRAMEWORKS = {
        # Web框架
        'Django': {'imports': ['django'], 'files': ['urls.py', 'settings.py']},
        'Flask': {'imports': ['flask']},
        'FastAPI': {'imports': ['fastapi']},
        'Express': {'imports': ['express']},
        'NestJS': {'imports': ['@nestjs']},
        'Spring': {'imports': ['org.springframework']},
        'Spring Boot': {'imports': ['spring.boot']},
        'Gin': {'imports': ['github.com/gin-gonic']},
        'Echo': {'imports': ['github.com/labstack/echo']},
        'Axum': {'imports': ['tokio::sync']},

        # 前端框架
        'React': {'imports': ['react'], 'files': ['.jsx', '.tsx']},
        'Vue': {'imports': ['vue'], 'files': ['.vue']},
        'Angular': {'imports': ['@angular']},
        'Next.js': {'imports': ['next'], 'files': ['next.config']},
        'Nuxt': {'imports': ['nuxt']},
        'Svelte': {'imports': ['svelte']},

        # 数据处理
        'Pandas': {'imports': ['pandas', 'pd']},
        'NumPy': {'imports': ['numpy', 'np']},
        'TensorFlow': {'imports': ['tensorflow', 'tf']},
        'PyTorch': {'imports': ['torch']},
        'Scikit-learn': {'imports': ['sklearn']},

        # 数据库
        'SQLAlchemy': {'imports': ['sqlalchemy']},
        'Django ORM': {'imports': ['django.db']},
        'Prisma': {'imports': ['@prisma']},
        'TypeORM': {'imports': ['typeorm']},
        'Mongoose': {'imports': ['mongoose']},
        'Sequelize': {'imports': ['sequelize']},

        # 测试
        'pytest': {'imports': ['pytest']},
        'Jest': {'imports': ['jest']},
        'Mocha': {'imports': ['mocha']},
        'JUnit': {'imports': ['org.junit']},

        # 工具
        'Docker': {'files': ['Dockerfile', 'docker-compose.yml']},
        'Kubernetes': {'files': ['k8s', 'kubernetes']},
        'Git': {'files': ['.gitignore']},
        'CI/CD': {'files': ['.github/workflows', 'Jenkinsfile', '.gitlab-ci.yml']},
    }

    # 架构模式
    ARCHITECTURE_PATTERNS = {
        'REST API': ['GET', 'POST', 'PUT', 'DELETE', '@app.route', '@router', '@RequestMapping'],
        'GraphQL': ['graphql', 'schema', 'query', 'mutation', '@Query', '@Mutation'],
        'Microservices': ['docker', 'kubernetes', 'grpc', 'service mesh'],
        'MVC': ['Model', 'View', 'Controller', 'model', 'view', 'controller'],
        'MVVM': ['ViewModel', 'observable', '@observable'],
        'Clean Architecture': ['entity', 'usecase', 'repository', 'interface adapter'],
        'CQRS': ['Command', 'Query', 'EventHandler', 'CommandHandler'],
        'Event-Driven': ['Event', 'emit', 'on(', 'addEventListener', 'subscribe'],
        'Observer Pattern': ['Observer', 'Subject', 'notify', 'listener'],
        'Factory Pattern': ['Factory', 'create(', 'Builder', '@Builder'],
        'Singleton Pattern': ['getInstance', 'singleton', 'static instance'],
    }

    # DevOps 技能
    DEVOPS_SKILLS = {
        'Docker': {
            'files': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
            'content': ['FROM', 'RUN docker', 'docker build'],
        },
        'Kubernetes': {
            'files': ['k8s/', '.k8s/', 'deployment.yaml', 'service.yaml'],
            'content': ['apiVersion:', 'kind:', 'kubectl'],
        },
        'CI/CD': {
            'files': ['.github/workflows', 'Jenkinsfile', '.gitlab-ci.yml', '.circleci/config.yml'],
            'content': ['github_actions', 'workflow_dispatch', 'pipelines:'],
        },
        'Terraform': {
            'files': ['.tf', 'terraform.tfvars'],
            'content': ['resource "', 'provider "', 'terraform init'],
        },
        'AWS': {
            'imports': ['boto3', 'aws-sdk'],
            'content': ['aws_', 's3://', 'arn:aws:'],
        },
        'Azure': {
            'imports': ['azure', 'azure-mgmt'],
            'content': ['azure-', '@azure/'],
        },
    }

    # 云原生特征
    CLOUD_NATIVE = {
        'containers': ['docker', 'containerd', 'podman'],
        'orchestration': ['kubernetes', 'docker-swarm', 'nomad'],
        'service_mesh': ['istio', 'linkerd', 'envoy'],
        'serverless': ['lambda', 'cloudfunctions', 'azure-functions'],
        'cicd': ['github-actions', 'gitlab-ci', 'jenkins', 'travis', 'circleci'],
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._file_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.ts']

    @property
    def name(self) -> str:
        return "技能识别分析器"

    @property
    def description(self) -> str:
        return "识别代码中使用的技术栈、框架、库和开发技能"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.PROFESSIONAL_STANDARDS

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """
        分析并识别技能
        返回CheckResult列表，实际技能数据通过get_skills()获取
        """
        # 识别语言
        detected_language = self._detect_language(file_path, content)
        detected_frameworks = self._detect_frameworks(file_path, content)
        detected_patterns = self._detect_architecture_patterns(content)
        detected_devops = self._detect_devops_skills(file_path, content)

        # 生成信息性结果
        if detected_language:
            self.results.append(self._create_result(
                check_id="SKILL001",
                check_name="检测到编程语言",
                message=f"识别到语言: {', '.join(detected_language)}",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="",
                metadata={'languages': detected_language}
            ))

        if detected_frameworks:
            self.results.append(self._create_result(
                check_id="SKILL002",
                check_name="检测到框架/库",
                message=f"识别到框架: {', '.join(detected_frameworks)}",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="",
                metadata={'frameworks': detected_frameworks}
            ))

        if detected_patterns:
            self.results.append(self._create_result(
                check_id="SKILL003",
                check_name="检测到架构模式",
                message=f"识别到架构模式: {', '.join(detected_patterns)}",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="",
                metadata={'patterns': detected_patterns}
            ))

        if detected_devops:
            self.results.append(self._create_result(
                check_id="SKILL004",
                check_name="检测到DevOps技能",
                message=f"识别到DevOps技能: {', '.join(detected_devops)}",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="",
                metadata={'devops': detected_devops}
            ))

        return self.results

    def get_skills(self, file_path: str, content: str) -> List[Skill]:
        """获取识别到的技能列表"""
        skills = []

        # 识别编程语言
        languages = self._detect_language(file_path, content)
        for lang in languages:
            level = self._estimate_language_level(content, lang)
            skills.append(Skill(
                name=lang,
                category="编程语言",
                level=level,
                confidence=0.8,
                description=f"{lang}编程能力",
                evidence=[f"通过{file_path}识别"]
            ))

        # 识别框架和库
        frameworks = self._detect_frameworks(file_path, content)
        for fw in frameworks:
            skills.append(Skill(
                name=fw,
                category="框架/库",
                level=SkillLevel.INTERMEDIATE,
                confidence=0.7,
                description=f"使用{fw}框架/库进行开发",
                evidence=[f"检测到{fw}导入或配置"]
            ))

        # 识别架构模式
        patterns = self._detect_architecture_patterns(content)
        for pattern in patterns:
            skills.append(Skill(
                name=pattern,
                category="架构模式",
                level=SkillLevel.ADVANCED,
                confidence=0.6,
                description=f"应用{pattern}架构模式",
                evidence=[f"检测到{pattern}特征"]
            ))

        # 识别DevOps技能
        devops = self._detect_devops_skills(file_path, content)
        for do in devops:
            skills.append(Skill(
                name=do,
                category="DevOps工具",
                level=SkillLevel.INTERMEDIATE,
                confidence=0.7,
                description=f"使用{do}进行运维和部署",
                evidence=[f"检测到{do}配置文件"]
            ))

        # 识别云原生技能
        cloud_skills = self._detect_cloud_native(content)
        for skill in cloud_skills:
            skills.append(Skill(
                name=skill,
                category="云原生",
                level=SkillLevel.ADVANCED,
                confidence=0.6,
                description=f"具备{skill}云原生技术能力",
                evidence=["检测到云原生技术特征"]
            ))

        return skills

    def _detect_language(self, file_path: str, content: str) -> List[str]:
        """检测编程语言"""
        detected = []
        ext = Path(file_path).suffix.lower()

        # 首先通过扩展名判断
        for lang, info in self.LANGUAGES.items():
            if ext in info.get('extensions', []):
                detected.append(lang)

        # 然后通过内容模式验证
        for lang, info in self.LANGUAGES.items():
            score = 0
            for pattern, weight in info.get('patterns', []):
                if re.search(pattern, content):
                    score += weight

            if score >= 1.5:  # 阈值
                if lang not in detected:
                    detected.append(lang)

        return detected

    def _estimate_language_level(self, content: str, language: str) -> SkillLevel:
        """估计语言使用熟练度"""
        if language not in self.LANGUAGES:
            return SkillLevel.BEGINNER

        level_indicators = self.LANGUAGES[language].get('level_indicators', {})

        for indicator, level in level_indicators.items():
            if indicator in content:
                return level

        return SkillLevel.BEGINNER

    def _detect_frameworks(self, file_path: str, content: str) -> List[str]:
        """检测框架和库"""
        detected = []

        for framework, info in self.FRAMEWORKS.items():
            # 检查导入
            imports = info.get('imports', [])
            for imp in imports:
                if imp in content or f"from {imp}" in content or f"import {imp}" in content:
                    detected.append(framework)
                    break

            # 检查文件特征
            files = info.get('files', [])
            for f in files:
                if f in file_path:
                    detected.append(framework)
                    break

        return list(set(detected))  # 去重

    def _detect_architecture_patterns(self, content: str) -> List[str]:
        """检测架构模式"""
        detected = []

        for pattern, indicators in self.ARCHITECTURE_PATTERNS.items():
            matches = 0
            for indicator in indicators:
                if indicator in content:
                    matches += 1

            if matches >= 2:  # 至少匹配2个指标
                detected.append(pattern)

        return detected

    def _detect_devops_skills(self, file_path: str, content: str) -> List[str]:
        """检测DevOps技能"""
        detected = []

        for tool, info in self.DEVOPS_SKILLS.items():
            # 检查文件
            files = info.get('files', [])
            for f in files:
                if f in file_path:
                    detected.append(tool)
                    break

            # 检查内容
            content_patterns = info.get('content', [])
            for pattern in content_patterns:
                if pattern in content:
                    if tool not in detected:
                        detected.append(tool)
                    break

        return detected

    def _detect_cloud_native(self, content: str) -> List[str]:
        """检测云原生技能"""
        detected = []

        for skill, keywords in self.CLOUD_NATIVE.items():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    detected.append(skill)
                    break

        return detected

    def _analyze_code_structure(self, content: str) -> Dict[str, int]:
        """分析代码结构特征"""
        structure = {
            'classes': len(re.findall(r'\bclass\s+\w+', content)),
            'functions': len(re.findall(r'\b(?:def|fn|func|function)\s+\w+', content)),
            'imports': len(re.findall(r'\b(?:import|from|require)\b', content)),
            'comments': len(re.findall(r'#.*|//.*|/\*.*?\*/', content)),
            'async': len(re.findall(r'\basync\b|\bawait\b', content)),
            'types': len(re.findall(r':\s*\w+|\binterface\b|\btype\s+\w+', content)),
        }

        return structure
