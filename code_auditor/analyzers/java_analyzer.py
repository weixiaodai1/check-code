"""
Java/Maven专业技能分析器
专门用于识别Java项目和Maven配置中的专业技能
"""

from typing import List, Dict, Set, Tuple, Optional
import re
from pathlib import Path
from .base_analyzer import BaseAnalyzer
from ..models import (
    CheckResult, CheckCategory, SeverityLevel, Skill, SkillLevel, Location
)


class JavaMavenAnalyzer(BaseAnalyzer):
    """Java/Maven项目和技能分析器"""

    # Java专业技能特征库
    JAVA_SKILLS = {
        # 核心Java技能
        'Java SE': {
            'patterns': [
                (r'public\s+static\s+void\s+main', 0.9),  # 入口点
                (r'System\.out\.print', 0.6),
                (r'new\s+\w+\s*\(', 0.5),  # 对象创建
                (r'extends\s+\w+', 0.5),  # 继承
                (r'implements\s+\w+', 0.5),  # 接口实现
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Java EE / Jakarta EE': {
            'patterns': [
                (r'@Entity', 0.8),
                (r'@WebServlet', 0.8),
                (r'@EJB', 0.8),
                (r'@Resource', 0.7),
                (r'javax\.ejb', 0.7),
                (r'jakarta\.ee', 0.8),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Spring Framework': {
            'patterns': [
                (r'org\.springframework\.', 0.8),
                (r'@Controller', 0.7),
                (r'@RestController', 0.8),
                (r'@Service', 0.7),
                (r'@Repository', 0.7),
                (r'@Autowired', 0.7),
                (r'@Component', 0.6),
                (r'@Configuration', 0.7),
                (r'@Bean', 0.7),
                (r'@SpringBootApplication', 0.9),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Spring Boot': {
            'patterns': [
                (r'SpringBootApplication', 0.9),
                (r'SpringApplication\.run', 0.8),
                (r'application\.properties', 0.7),
                (r'application\.yml', 0.7),
                (r'@EnableAutoConfiguration', 0.7),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Spring MVC': {
            'patterns': [
                (r'@RequestMapping', 0.8),
                (r'@GetMapping', 0.7),
                (r'@PostMapping', 0.7),
                (r'@PutMapping', 0.7),
                (r'@DeleteMapping', 0.7),
                (r'@PathVariable', 0.7),
                (r'@RequestParam', 0.7),
                (r'@RequestBody', 0.7),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Spring Data JPA': {
            'patterns': [
                (r'extends\s+JpaRepository', 0.8),
                (r'extends\s+CrudRepository', 0.8),
                (r'extends\s+PagingAndSortingRepository', 0.8),
                (r'@Query', 0.7),
                (r'@Modifying', 0.7),
                (r'CrudRepository<', 0.7),
                (r'JpaRepository<', 0.8),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Spring Security': {
            'patterns': [
                (r'@EnableWebSecurity', 0.8),
                (r'WebSecurityConfigurerAdapter', 0.7),
                (r'SecurityFilterChain', 0.7),
                (r'@PreAuthorize', 0.7),
                (r'@Secured', 0.6),
                (r'AuthenticationManager', 0.7),
                (r'PasswordEncoder', 0.7),
            ],
            'level': SkillLevel.EXPERT
        },
        'Hibernate': {
            'patterns': [
                (r'org\.hibernate\.', 0.7),
                (r'@Table', 0.6),
                (r'@Column', 0.6),
                (r'@Id', 0.6),
                (r'@GeneratedValue', 0.6),
                (r'SessionFactory', 0.7),
                (r'@ManyToOne', 0.7),
                (r'@OneToMany', 0.7),
                (r'@JoinColumn', 0.6),
            ],
            'level': SkillLevel.ADVANCED
        },
        'MyBatis': {
            'patterns': [
                (r'org\.apache\.ibatis\.', 0.7),
                (r'@Mapper', 0.7),
                (r'@Select', 0.7),
                (r'@Insert', 0.7),
                (r'@Update', 0.7),
                (r'@Delete', 0.7),
                (r'SqlSessionFactory', 0.7),
                (r'\.xml\s*<mapper', 0.7),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Maven': {
            'patterns': [
                (r'<groupId>', 0.8),
                (r'<artifactId>', 0.8),
                (r'<version>', 0.7),
                (r'<dependency>', 0.8),
                (r'<scope>', 0.7),
                (r'<plugins>', 0.7),
                (r'mvnw', 0.6),  # Maven Wrapper
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'JUnit': {
            'patterns': [
                (r'import\s+org\.junit\.', 0.7),
                (r'@Test', 0.7),
                (r'@BeforeEach', 0.7),
                (r'@AfterEach', 0.7),
                (r'@BeforeAll', 0.7),
                (r'@AfterAll', 0.7),
                (r'@ParameterizedTest', 0.7),
                (r'@Disabled', 0.6),
                (r'Assertions\.assert', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'TestNG': {
            'patterns': [
                (r'import\s+org\.testng\.', 0.7),
                (r'@Test', 0.6),
                (r'@BeforeMethod', 0.7),
                (r'@AfterMethod', 0.7),
                (r'@BeforeClass', 0.7),
                (r'@DataProvider', 0.7),
                (r'@Listeners', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Mockito': {
            'patterns': [
                (r'import\s+org\.mockito\.', 0.7),
                (r'@Mock', 0.7),
                (r'@InjectMocks', 0.7),
                (r'when\(', 0.7),
                (r'thenReturn\(', 0.7),
                (r'verify\(', 0.6),
                (r'any\(\)', 0.6),
                (r'Mockito\.', 0.7),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'REST API Design': {
            'patterns': [
                (r'@GetMapping.*\/\{', 0.7),  # REST路径参数
                (r'@RequestParam', 0.6),
                (r'ResponseEntity<', 0.7),
                (r'HttpStatus\.', 0.6),
                (r'@JsonProperty', 0.6),
                (r'@Valid', 0.6),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Microservices': {
            'patterns': [
                (r'@FeignClient', 0.8),
                (r'@LoadBalanced', 0.7),
                (r'@RibbonClient', 0.7),
                (r'RestTemplate', 0.7),
                (r'WebClient', 0.6),
                (r'Retry', 0.6),
                (r'@CircuitBreaker', 0.7),
            ],
            'level': SkillLevel.EXPERT
        },
        'Docker': {
            'patterns': [
                (r'FROM\s+openjdk', 0.8),
                (r'FROM\s+maven', 0.8),
                (r'FROM\s+gradle', 0.7),
                (r'COPY\s+target/', 0.7),
                (r'ENTRYPOINT\s+\[', 0.6),
                (r'EXPOSE\s+\d+', 0.6),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Kubernetes': {
            'patterns': [
                (r'apiVersion:', 0.7),
                (r'kind:\s*Deployment', 0.7),
                (r'kind:\s*Service', 0.7),
                (r'kind:\s*ConfigMap', 0.6),
                (r'containerPort:', 0.6),
                (r'replicas:', 0.6),
            ],
            'level': SkillLevel.EXPERT
        },
        'AWS': {
            'patterns': [
                (r'com\.amazonaws\.', 0.7),
                (r'@DynamoDBTable', 0.7),
                (r'@S3Client', 0.7),
                (r'AmazonS3', 0.7),
                (r'AmazonDynamoDB', 0.7),
                (r'@Lambda', 0.7),
                (r'AWSLambda', 0.7),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Redis': {
            'patterns': [
                (r'@Cacheable', 0.7),
                (r'@CacheEvict', 0.7),
                (r'RedisTemplate<', 0.7),
                (r'StringRedisTemplate', 0.7),
                (r'opsForValue\(\)', 0.6),
            ],
            'level': SkillLevel.ADVANCED
        },
        'RabbitMQ': {
            'patterns': [
                (r'@RabbitListener', 0.7),
                (r'@RabbitHandler', 0.7),
                (r'AmqpTemplate', 0.7),
                (r'@EnableRabbit', 0.7),
                (r'Queue\b', 0.5),
                (r'Exchange\b', 0.5),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Kafka': {
            'patterns': [
                (r'@KafkaListener', 0.7),
                (r'@KafkaHandler', 0.7),
                (r'KafkaTemplate', 0.7),
                (r'ProducerRecord', 0.6),
                (r'ConsumerRecord', 0.6),
            ],
            'level': SkillLevel.ADVANCED
        },
        'MySQL': {
            'patterns': [
                (r'jdbc:mysql://', 0.7),
                (r'com\.mysql\.', 0.7),
                (r'mysql-connector', 0.7),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'PostgreSQL': {
            'patterns': [
                (r'jdbc:postgresql://', 0.7),
                (r'org\.postgresql\.', 0.7),
                (r'postgresql', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'MongoDB': {
            'patterns': [
                (r'@Document', 0.7),
                (r'@Id', 0.6),
                (r'MongoRepository', 0.7),
                (r'MongoTemplate', 0.7),
                (r'@Indexed', 0.6),
            ],
            'level': SkillLevel.ADVANCED
        },
        'Elasticsearch': {
            'patterns': [
                (r'@Document', 0.6),
                (r'ElasticsearchRestTemplate', 0.7),
                (r'@Field', 0.6),
                (r'@Autowired.*Elasticsearch', 0.6),
            ],
            'level': SkillLevel.ADVANCED
        },
        'GraphQL': {
            'patterns': [
                (r'@GraphQLQuery', 0.7),
                (r'@GraphQLMutation', 0.7),
                (r'GraphQLSchema', 0.6),
                (r'@SchemaMapping', 0.7),
            ],
            'level': SkillLevel.EXPERT
        },
        'WebSocket': {
            'patterns': [
                (r'@ServerEndpoint', 0.7),
                (r'@OnOpen', 0.6),
                (r'@OnMessage', 0.6),
                (r'@OnClose', 0.6),
                (r'SimpMessagingTemplate', 0.7),
                (r'@MessageMapping', 0.7),
            ],
            'level': SkillLevel.ADVANCED
        },
        'JPA/Hibernate ORM': {
            'patterns': [
                (r'@Entity', 0.7),
                (r'@Table', 0.6),
                (r'@Column', 0.6),
                (r'@Id', 0.6),
                (r'@GeneratedValue', 0.6),
                (r'@ManyToMany', 0.7),
                (r'@JoinTable', 0.6),
                (r'EntityManager', 0.7),
            ],
            'level': SkillLevel.ADVANCED
        },
        'JDBC': {
            'patterns': [
                (r'DriverManager\.getConnection', 0.7),
                (r'Connection\b', 0.6),
                (r'PreparedStatement', 0.7),
                (r'Statement\b', 0.6),
                (r'ResultSet', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Servlet': {
            'patterns': [
                (r'HttpServlet', 0.7),
                (r'@WebServlet', 0.7),
                (r'doGet\(', 0.6),
                (r'doPost\(', 0.6),
                (r'ServletContext', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'JSP': {
            'patterns': [
                (r'<%@', 0.7),
                (r'<%=', 0.6),
                (r'<%!', 0.6),
                (r'JSTL', 0.6),
                (r'EL\s+expression', 0.5),
            ],
            'level': SkillLevel.BEGINNER
        },
        'Thymeleaf': {
            'patterns': [
                (r'th:text=', 0.7),
                (r'th:each=', 0.7),
                (r'th:if=', 0.6),
                (r'th:fragment', 0.6),
                (r'th:replace', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Validation': {
            'patterns': [
                (r'@NotNull', 0.7),
                (r'@NotBlank', 0.7),
                (r'@NotEmpty', 0.7),
                (r'@Size', 0.6),
                (r'@Email', 0.6),
                (r'@Min', 0.6),
                (r'@Max', 0.6),
                (r'@Pattern', 0.6),
                (r'@Valid', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Lombok': {
            'patterns': [
                (r'@Data', 0.7),
                (r'@Getter', 0.6),
                (r'@Setter', 0.6),
                (r'@Builder', 0.7),
                (r'@NoArgsConstructor', 0.6),
                (r'@AllArgsConstructor', 0.6),
                (r'@Slf4j', 0.6),
                (r'@RequiredArgsConstructor', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Stream API': {
            'patterns': [
                (r'\.stream\(\)', 0.7),
                (r'\.filter\(', 0.6),
                (r'\.map\(', 0.6),
                (r'\.collect\(', 0.6),
                (r'\.forEach\(', 0.5),
                (r'\.sorted\(', 0.5),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Lambda表达式': {
            'patterns': [
                (r'\(\s*\w+\s*\)\s*->', 0.7),
                (r'\w+\s*->\s*\{', 0.6),
                (r'::\w+\b', 0.6),  # 方法引用
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Optional': {
            'patterns': [
                (r'Optional<', 0.7),
                (r'\.orElse\(', 0.6),
                (r'\.orElseGet\(', 0.6),
                (r'\.isPresent\(\)', 0.6),
                (r'\.ifPresent\(', 0.6),
            ],
            'level': SkillLevel.INTERMEDIATE
        },
        'Design Patterns': {
            'patterns': [
                (r'Singleton', 0.5),
                (r'Factory', 0.5),
                (r'Builder', 0.5),
                (r'Observer', 0.5),
                (r'Strategy', 0.5),
                (r'Adapter', 0.5),
            ],
            'level': SkillLevel.ADVANCED
        },
    }

    # Maven依赖特征库
    DEPENDENCY_SKILLS = {
        'spring-boot-starter-web': 'Spring Boot Web',
        'spring-boot-starter-data-jpa': 'Spring Data JPA',
        'spring-boot-starter-security': 'Spring Security',
        'spring-boot-starter-test': 'Spring Boot Testing',
        'spring-boot-starter-validation': 'Bean Validation',
        'spring-boot-starter-data-redis': 'Redis',
        'spring-boot-starter-amqp': 'RabbitMQ',
        'spring-kafka': 'Kafka',
        'spring-cloud-starter-netflix-eureka': 'Service Discovery',
        'mybatis-spring-boot-starter': 'MyBatis',
        'mysql-connector-java': 'MySQL',
        'postgresql': 'PostgreSQL',
        'lombok': 'Lombok',
        'junit-jupiter': 'JUnit 5',
        'mockito-core': 'Mockito',
        'logback-classic': 'SLF4J/Logback',
        'jackson-databind': 'Jackson JSON',
        'fastjson': 'FastJSON',
        'gson': 'Google Gson',
        'apache-poi': 'Excel Processing',
        'itextpdf': 'PDF Generation',
    }

    # Java最佳实践规则
    JAVA_PRACTICES = {
        'SOLID Principles': {
            'patterns': [
                (r'interface\s+\w+\s*\{', 0.5),  # Interface segregation
                (r'extends\s+\w+\s*(?!\.)', 0.4),  # Open/closed principle hint
            ],
            'severity': SeverityLevel.HIGH,
            'category': 'architecture'
        },
        'Thread Safety': {
            'patterns': [
                (r'synchronized\s*\(', 0.6),
                (r'volatile\s+', 0.5),
                (r'AtomicInteger', 0.6),
                (r'ConcurrentHashMap', 0.6),
                (r'ReentrantLock', 0.6),
            ],
            'severity': SeverityLevel.MEDIUM,
            'category': 'concurrency'
        },
        'Exception Handling': {
            'patterns': [
                (r'catch\s*\(\s*Exception\s+\w+\s*\)', 0.5),
                (r'catch\s*\(\s*Throwable\s+\w+\s*\)', 0.4),  # Too broad
                (r'throws\s+\w+', 0.5),
            ],
            'severity': SeverityLevel.MEDIUM,
            'category': 'error-handling'
        },
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._file_extensions = ['.java', '.xml', '.properties', '.yml', '.yaml', '.gradle']
        self._detected_skills: List[Skill] = []
        self._maven_deps: List[str] = []

    @property
    def name(self) -> str:
        return "Java/Maven技能分析器"

    @property
    def description(self) -> str:
        return "识别Java项目和Maven配置中的专业技能、技术栈和最佳实践"

    @property
    def category(self) -> CheckCategory:
        return CheckCategory.PROFESSIONAL_STANDARDS

    def analyze(self, file_path: str, content: str) -> List[CheckResult]:
        """执行Java/Maven项目分析"""
        self.results = []
        self._detected_skills = []
        self._maven_deps = []

        # 检测文件类型并执行相应分析
        if file_path.endswith('.xml') and 'pom.xml' in file_path:
            return self._analyze_pom_xml(file_path, content)
        elif file_path.endswith('.java'):
            return self._analyze_java_file(file_path, content)
        elif file_path.endswith('.properties'):
            return self._analyze_properties(file_path, content)
        elif file_path.endswith(('.yml', '.yaml')):
            return self._analyze_yaml(file_path, content)

        return self.results

    def _analyze_pom_xml(self, file_path: str, content: str) -> List[CheckResult]:
        """分析pom.xml文件"""
        # 提取所有依赖
        dep_pattern = r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>'
        deps = re.findall(dep_pattern, content, re.MULTILINE | re.DOTALL)

        for group_id, artifact_id in deps:
            dep_str = f"{group_id}:{artifact_id}"
            self._maven_deps.append(dep_str)

            # 检查是否在已知技能库中
            for key, skill_name in self.DEPENDENCY_SKILLS.items():
                if key in artifact_id or key in dep_str:
                    skill = Skill(
                        name=skill_name,
                        category="Maven依赖",
                        level=SkillLevel.INTERMEDIATE,
                        confidence=0.8,
                        evidence=[f"Maven依赖: {artifact_id}"]
                    )
                    self._detected_skills.append(skill)

        # 检查插件
        plugin_pattern = r'<plugin>\s*<artifactId>([^<]+)</artifactId>'
        plugins = re.findall(plugin_pattern, content, re.MULTILINE | re.DOTALL)
        for plugin in plugins:
            if 'maven-compiler' in plugin:
                self._detected_skills.append(Skill(
                    name='Maven构建',
                    category='构建工具',
                    level=SkillLevel.INTERMEDIATE,
                    confidence=0.7,
                    evidence=['Maven编译插件']
                ))
            if 'maven-surefire' in plugin:
                self._detected_skills.append(Skill(
                    name='单元测试',
                    category='测试',
                    level=SkillLevel.INTERMEDIATE,
                    confidence=0.7,
                    evidence=['Maven测试插件']
                ))

        # 检查Spring Boot特征
        if 'spring-boot' in content:
            self._detected_skills.append(Skill(
                name='Spring Boot',
                category='框架',
                level=SkillLevel.ADVANCED,
                confidence=0.9,
                evidence=['Spring Boot依赖检测']
            ))

        # 生成检查结果
        self.results.append(self._create_result(
            check_id="JAVA001",
            check_name="Maven项目分析",
            message=f"检测到 {len(deps)} 个Maven依赖",
            severity=SeverityLevel.INFO,
            file_path=file_path,
            suggestion="",
            metadata={'dependencies': [f"{g}:{a}" for g, a in deps]}
        ))

        return self.results

    def _analyze_java_file(self, file_path: str, content: str) -> List[CheckResult]:
        """分析Java源文件"""
        # 检测包名
        package_match = re.search(r'package\s+([\w.]+);', content)
        package_name = package_match.group(1) if package_match else ""

        # 检测导入语句
        imports = re.findall(r'import\s+([^;]+);', content)

        # 检测类和接口
        classes = re.findall(r'(?:public|private|protected)?\s*class\s+(\w+)', content)
        interfaces = re.findall(r'(?:public|private|protected)?\s*interface\s+(\w+)', content)
        enums = re.findall(r'(?:public|private|protected)?\s*enum\s+(\w+)', content)

        # 检测方法
        methods = re.findall(r'(?:public|private|protected)?\s*(?:static)?\s*(?:\w+)\s+(\w+)\s*\(', content)

        # 检测注解使用
        annotations = re.findall(r'@(\w+)', content)

        # 识别技能
        self._detect_skills_from_content(content, imports, annotations)

        # 检测最佳实践
        self._check_java_best_practices(file_path, content, package_name)

        # 生成结果
        if package_name:
            self.results.append(self._create_result(
                check_id="JAVA010",
                check_name="Java包结构",
                message=f"包名: {package_name}",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                metadata={'package': package_name, 'classes': classes}
            ))

        return self.results

    def _detect_skills_from_content(
        self, content: str, imports: List[str], annotations: List[str]
    ):
        """从内容中检测技能"""
        for skill_name, info in self.JAVA_SKILLS.items():
            score = 0
            matched_patterns = []

            for pattern, weight in info['patterns']:
                if re.search(pattern, content):
                    score += weight
                    matched_patterns.append(pattern)

            # 检查导入语句
            for imp in imports:
                if any(p.replace(r'\.', '.').replace(r'\w+', '') in imp for p in [pattern for pattern, _ in info['patterns']]):
                    score += 0.3

            if score >= 0.8:
                skill = Skill(
                    name=skill_name,
                    category=self._categorize_skill(skill_name),
                    level=info['level'],
                    confidence=min(score / 2, 1.0),
                    evidence=matched_patterns[:3]
                )
                self._detected_skills.append(skill)

        # 从注解推断技能
        annotation_skills = {
            'Controller': 'Spring MVC',
            'RestController': 'REST API',
            'Service': 'Spring Service',
            'Repository': 'Spring Data',
            'Entity': 'JPA/Hibernate ORM',
            'Table': 'JPA/Hibernate ORM',
            'Configuration': 'Spring Configuration',
            'Bean': 'Spring IoC',
            'Test': '单元测试',
            'Mock': 'Mockito',
            'Autowired': 'Spring DI',
            'Value': 'Spring Properties',
        }

        for annotation in annotations:
            if annotation in annotation_skills:
                self._detected_skills.append(Skill(
                    name=annotation_skills[annotation],
                    category='框架组件',
                    level=SkillLevel.INTERMEDIATE,
                    confidence=0.7,
                    evidence=[f'@{annotation}注解']
                ))

    def _categorize_skill(self, skill_name: str) -> str:
        """分类技能"""
        categories = {
            'Spring': 'Java框架',
            'Hibernate': 'ORM框架',
            'JPA': 'ORM框架',
            'MyBatis': '持久层框架',
            'Maven': '构建工具',
            'JUnit': '测试框架',
            'Mockito': '测试框架',
            'Docker': 'DevOps',
            'Kubernetes': 'DevOps',
            'AWS': '云服务',
            'Redis': '缓存',
            'RabbitMQ': '消息队列',
            'Kafka': '消息队列',
            'MySQL': '数据库',
            'PostgreSQL': '数据库',
            'MongoDB': '数据库',
            'Elasticsearch': '搜索引擎',
            'GraphQL': 'API设计',
            'WebSocket': '通信',
            'Design Patterns': '架构设计',
        }

        for key, category in categories.items():
            if key in skill_name:
                return category
        return 'Java技能'

    def _check_java_best_practices(
        self, file_path: str, content: str, package_name: str
    ):
        """检查Java最佳实践"""
        # 检查Thread Safety
        if re.search(r'synchronized\s*\(', content):
            self.results.append(self._create_result(
                check_id="JAVA020",
                check_name="线程同步检测",
                message="代码中使用了synchronized关键字",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="确保正确使用并发控制，考虑使用java.util.concurrent包中的高级工具",
                rule_id="thread-safety"
            ))

        # 检查Stream API使用
        if '.stream()' in content:
            self.results.append(self._create_result(
                check_id="JAVA021",
                check_name="Stream API使用",
                message="检测到使用Java Stream API",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="Stream API可以提高代码可读性，但注意不要过度使用",
                rule_id="stream-api"
            ))

        # 检查Optional使用
        if 'Optional<' in content:
            self.results.append(self._create_result(
                check_id="JAVA022",
                check_name="Optional使用",
                message="检测到使用Optional避免空指针",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="Good! 使用Optional是处理空值的现代方式",
                rule_id="optional-usage"
            ))

        # 检查异常处理
        if re.search(r'catch\s*\(\s*Exception\s+\w+\s*\)', content):
            self.results.append(self._create_result(
                check_id="JAVA023",
                check_name="异常处理",
                message="检测到捕获Exception",
                severity=SeverityLevel.MEDIUM,
                file_path=file_path,
                suggestion="尽可能捕获具体异常类型，避免捕获过于宽泛的Exception",
                rule_id="exception-handling"
            ))

        # 检查Lombok使用
        if re.search(r'@Data|@Getter|@Setter|@Builder', content):
            self.results.append(self._create_result(
                check_id="JAVA024",
                check_name="Lombok使用",
                message="检测到使用Lombok简化代码",
                severity=SeverityLevel.INFO,
                file_path=file_path,
                suggestion="Lombok可以减少样板代码，但注意IDE支持",
                rule_id="lombok-usage"
            ))

    def _analyze_properties(self, file_path: str, content: str) -> List[CheckResult]:
        """分析properties文件"""
        # 检测Spring配置
        if 'spring.' in content or 'application.' in content:
            self._detected_skills.append(Skill(
                name='Spring Boot配置',
                category='框架配置',
                level=SkillLevel.INTERMEDIATE,
                confidence=0.7,
                evidence=['Spring配置文件']
            ))

        # 检测数据库配置
        if 'jdbc.' in content or 'datasource.' in content:
            self._detected_skills.append(Skill(
                name='数据库配置',
                category='数据访问',
                level=SkillLevel.INTERMEDIATE,
                confidence=0.6,
                evidence=['数据库连接配置']
            ))

        return self.results

    def _analyze_yaml(self, file_path: str, content: str) -> List[CheckResult]:
        """分析YAML配置"""
        # 检测Spring Boot配置
        if 'server:' in content or 'spring:' in content:
            self._detected_skills.append(Skill(
                name='Spring Boot配置',
                category='框架配置',
                level=SkillLevel.INTERMEDIATE,
                confidence=0.8,
                evidence=['YAML配置文件']
            ))

        # 检测数据库配置
        if 'datasource:' in content or 'jpa:' in content:
            self._detected_skills.append(Skill(
                name='Spring Data JPA',
                category='数据访问',
                level=SkillLevel.ADVANCED,
                confidence=0.7,
                evidence=['JPA配置']
            ))

        # 检测Redis配置
        if 'redis:' in content:
            self._detected_skills.append(Skill(
                name='Redis缓存',
                category='缓存',
                level=SkillLevel.ADVANCED,
                confidence=0.7,
                evidence=['Redis配置']
            ))

        return self.results

    def get_skills(self, file_path: str = None, content: str = None) -> List[Skill]:
        """获取识别到的技能列表"""
        return self._detected_skills

    def get_skills_summary(self) -> Dict[str, int]:
        """获取技能统计摘要"""
        summary = {}
        for skill in self._detected_skills:
            summary[skill.name] = summary.get(skill.name, 0) + 1
        return summary

    def get_maven_dependencies(self) -> List[str]:
        """获取Maven依赖列表"""
        return self._maven_deps
