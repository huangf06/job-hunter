# Job Hunter v3.0 系统改进方案

> 目标：系统级保障批量简历生成质量，让每一份自动产出的简历都"可投递"
> 原则：适度包装（能突击准备应付面试即可），绝不编造

---

## 一、当前流程诊断

```
当前: Scrape → Hard Filter → Rule Score → AI Analysis → Render → PDF
                                              ↑ 质量黑洞
```

**核心问题：AI Analysis 是一个不受约束的黑盒。** 它同时承担评分和简历定制两个职责，但没有后置验证。产出的 bio、title、skills 全凭 AI 自觉遵守 prompt 规则，一旦 AI "创造性发挥"，错误会直接流入最终 PDF。

已发现的批量化质量隐患：
1. **Bio 失控**：AI 自由生成，出现"6+ years"等不可辩护声明
2. **技能无分层**：该写的不写，不该写的有时写了
3. **职位名称无约束**：AI 生成了 bullet library 中不存在的职位名
4. **硬性条件漏网**：7年Azure、Java-only 等应该在 Hard Filter 就拦截
5. **Bullet 虽有验证但 bio/skills 没有**：修了半个问题
6. **无回归检测**：重复生成同一职位简历时无 diff 对比

---

## 二、改进后流程

```
Scrape → Hard Filter v3 → Rule Score → AI Analysis → Validator → Render → QA → PDF
              ↑                              ↑            ↑                  ↑
        新增：特定技术          新增：技能分层     新增：5项       新增：格式
        硬性排除规则            输入 prompt      后置校验       完整性检查
```

### 阶段 0：数据层改进（基础设施）

#### 0.1 合并 Bullet Library（唯一真相源）

只保留 `job-hunter/assets/bullet_library.yaml`。`resume_project/bullet_library.yaml` 归档。

#### 0.2 Bullet Library 新增结构

在 bullet_library.yaml 中新增三个关键配置块：

```yaml
# ============================================================
# 技能分层策略
# ============================================================
skill_tiers:
  # 第一层：已验证技能（任何情况都可以写）
  verified:
    languages: ["Python (Expert)", "SQL (Expert)", "Bash"]
    data_engineering: ["PySpark", "Delta Lake", "Databricks", "ETL/ELT",
                       "Auto Loader", "Structured Streaming", "Schema Evolution",
                       "Medallion Architecture"]
    cloud: ["AWS (EMR, Glue, S3, Lambda)", "Docker", "Airflow", "CI/CD", "Git"]
    databases: ["PostgreSQL", "MySQL", "Hadoop", "Hive"]
    ml: ["Pandas", "NumPy", "PyTorch", "XGBoost", "LightGBM",
         "scikit-learn", "Statistics", "A/B Testing", "Time-Series Analysis"]
    certifications: ["Databricks Certified Data Engineer Professional (2026)"]

  # 第二层：可转移技能（JD 要求时才写，可短期突击）
  # 这些技能和已有技能高度相似，或已有一定基础
  transferable:
    - skill: "Azure (Data Factory, Synapse, ADLS)"
      basis: "AWS 经验可转移，Azure 有接触"
      ramp_up: "1-2 weeks"
      write_when: "JD mentions Azure"
    - skill: "Kafka"
      basis: "理解消息队列概念，Structured Streaming 经验"
      ramp_up: "1 week"
      write_when: "JD mentions Kafka or event streaming"
    - skill: "Terraform"
      basis: "IaC 概念了解，Docker/CI/CD 经验"
      ramp_up: "1-2 weeks"
      write_when: "JD mentions IaC or Terraform"
    - skill: "TypeScript"
      basis: "Python 强，JS 基础概念了解"
      ramp_up: "2 weeks"
      write_when: "JD mentions TypeScript but not as primary"
    - skill: "Scala"
      basis: "PySpark 经验，Spark 原生语言"
      ramp_up: "2-3 weeks"
      write_when: "JD mentions Scala for Spark"
    - skill: "GCP (BigQuery, Dataflow)"
      basis: "有 GCP 使用经验"
      ramp_up: "1 week"
      write_when: "JD mentions GCP"
    - skill: "Kubernetes"
      basis: "有使用经验"
      ramp_up: "1 week"
      write_when: "JD mentions K8s"
    - skill: "dbt"
      basis: "理解数据转换，SQL 熟练"
      ramp_up: "3 days"
      write_when: "JD mentions dbt or analytics engineering"
    - skill: "MLflow"
      basis: "Databricks 认证涵盖"
      ramp_up: "3 days"
      write_when: "JD mentions experiment tracking"

  # 第三层：硬排除（绝不写）
  excluded: ["C/C++", "Java", "Ruby", "Swift", "Kotlin", ".NET/C#",
             "React", "Angular", "Vue", "Flutter"]

# ============================================================
# 职位名称约束表
# ============================================================
# 每个实际工作经历允许使用的职位名，按目标角色选择
# 原则：可适度包装，但必须基于实际职责
title_options:
  glp_technology:
    # 实际职位：Data Scientist / Senior Data Modeling Engineer
    default: "Data Scientist & Team Lead"
    data_engineer: "Data Engineer & Team Lead"
    data_scientist: "Data Scientist & Team Lead"
    ml_engineer: "ML Engineer & Team Lead"
    risk_analyst: "Credit Risk Analyst & Team Lead"

  baiquan_investment:
    # 实际职位：Quantitative Researcher
    default: "Quantitative Researcher"
    data_engineer: "Quantitative Developer"
    data_scientist: "Quantitative Analyst"
    quant: "Quantitative Researcher"

  eleme:
    # 实际职位：Data Analyst（固定不变）
    default: "Data Analyst"

  henan_energy:
    # 实际职位：Business Supervisor
    default: "Business Supervisor"
    data_analyst: "Business Analyst"
    supply_chain: "Supply Chain & Operations Supervisor"

# ============================================================
# Bio 构建约束
# ============================================================
bio_constraints:
  # 允许声明的最大年数（基于实际数据经历计算）
  # GLP 2y + Baiquan 2y + Ele.me 2y(简历) + Henan 部分 = ~6y 和数据打交道
  max_years_claim: 6
  years_claim_scope: "working with data systems"  # 不是 "production data pipelines"

  # 禁止出现的措辞（这些 AI 容易自由发挥）
  banned_phrases:
    - "deep expertise"        # 用 "hands-on experience" 替代
    - "extensive experience"  # 用 "experience" 替代
    - "proven track record"   # 过于市场化
    - "cutting-edge"          # 空洞
    - "world-class"           # 空洞
    - "industry-leading"      # 空洞

  # 必须出现的元素（按角色类型）
  required_elements:
    data_engineer: ["Databricks", "data pipeline"]
    ml_engineer: ["M.Sc. in AI", "VU Amsterdam"]
    data_scientist: ["statistical", "machine learning"]
    quant: ["quantitative", "trading"]

  # 可选元素（AI 根据 JD 决定是否加入）
  optional_elements:
    - "Databricks Certified Data Engineer Professional"
    - "Tsinghua University"
    - "credit risk"
    - "fintech"
```

---

### 阶段 1：Hard Filter v3.0

在 `config/base/filters.yaml` 新增规则：

```yaml
# 新增规则：特定技术硬性经验要求
specific_tech_experience:
  enabled: true
  priority: 2.5  # 在 non_target_role 之后
  type: "regex"
  description: "JD requires years of specific tech we can't claim"
  patterns:
    # N 年某特定技术（而非通用经验年限）
    - "(5|6|7|8|9|10)\\+?\\s*years?.*\\b(java|c\\+\\+|scala|\.net|ruby)\\b"
    - "\\b(java|c\\+\\+|scala|\.net|ruby)\\b.*(5|6|7|8|9|10)\\+?\\s*years?"
    # 7+ 年特定云平台（Azure 可以降到 5 年再排除）
    - "(7|8|9|10)\\+?\\s*years?.*\\bazure\\b"
    - "\\bazure\\b.*(7|8|9|10)\\+?\\s*years?"
  exceptions:
    - "python"  # "7+ years Python" 我们反而能声称
    - "data"    # 通用数据经验不排除
```

**设计考量：**
- 只排除不可能短期突击的硬性技术年限要求
- Python/SQL/data 的经验年限要求不排除（实际有这么多年）
- Azure 的阈值设为 7 年（5 年以下可以靠 AWS 可转移经验 + 突击）

---

### 阶段 2：AI Analysis 改进

#### 2.1 Prompt 重构

当前 prompt 有两个问题：
1. 技能规则是"禁止列表"（告诉 AI 不该做什么），应改为"允许列表"（告诉 AI 能做什么）
2. Bio 没有约束规则

**改进方案：将 skill_tiers 注入 prompt**

```python
# ai_analyzer.py 新增方法
def _build_skill_context(self, job_description: str) -> str:
    """根据 JD 动态构建技能上下文"""
    tiers = self._parsed_bullets.get('skill_tiers', {})
    verified = tiers.get('verified', {})
    transferable = tiers.get('transferable', [])
    excluded = tiers.get('excluded', [])

    # 检查 JD 中提到了哪些可转移技能
    jd_lower = job_description.lower()
    active_transferable = []
    for t in transferable:
        skill_name = t['skill'].split('(')[0].strip().lower()
        if skill_name in jd_lower or any(
            kw in jd_lower for kw in t.get('write_when', '').lower().split()
        ):
            active_transferable.append(t['skill'])

    lines = []
    lines.append("## VERIFIED SKILLS (always safe to list)")
    for category, skills in verified.items():
        lines.append(f"  {category}: {', '.join(skills)}")

    if active_transferable:
        lines.append("\n## TRANSFERABLE SKILLS (JD requests these, candidate can ramp up)")
        lines.append(f"  {', '.join(active_transferable)}")

    lines.append(f"\n## EXCLUDED SKILLS (NEVER list): {', '.join(excluded)}")

    return '\n'.join(lines)
```

#### 2.2 Title 约束注入

将 `title_options` 从 bullet library 传入 prompt：

```
### TITLE SELECTION (MUST use exactly one of these options)
GLP Technology:
  - For Data Engineer roles: "Data Engineer & Team Lead"
  - For ML Engineer roles: "ML Engineer & Team Lead"
  - For Data Scientist roles: "Data Scientist & Team Lead"
  - For Risk roles: "Credit Risk Analyst & Team Lead"
Baiquan Investment:
  - For Data Engineer roles: "Quantitative Developer"
  - For Data Scientist roles: "Quantitative Analyst"
  - For Quant roles: "Quantitative Researcher"
Ele.me: ALWAYS "Data Analyst" (no variation)
```

#### 2.3 Bio 约束注入

在 prompt 中追加：

```
### BIO CONSTRAINTS (ABSOLUTE)
- Maximum years claim: "6+ years working with data systems" (NOT "production data pipelines")
- BANNED phrases: "deep expertise", "extensive experience", "proven track record", "cutting-edge"
- REPLACE "deep expertise" with "hands-on experience"
- For Data Engineer roles: MUST mention Databricks certification
- For ML roles: MUST mention M.Sc. AI from VU Amsterdam
- Keep to 2 sentences maximum
```

---

### 阶段 3：后置验证器（新组件）

**这是整个改进的核心。** 在 AI 产出 JSON 和 Render 之间插入验证器。

```python
# scripts/resume_validator.py (新文件)

class ResumeValidator:
    """AI 简历 JSON 的后置验证器"""

    def __init__(self):
        self.bullet_lib = self._load_bullet_library()
        self.config = self.bullet_lib  # 技能分层、title 约束等都在这里

    def validate(self, tailored: dict, job: dict) -> ValidationResult:
        """
        运行所有验证规则，返回结果。

        Returns:
            ValidationResult:
                passed: bool
                errors: list[str]    # 阻断性错误（不渲染）
                warnings: list[str]  # 警告（渲染但日志记录）
                fixes: dict          # 自动修复的内容
        """
        errors = []
        warnings = []
        fixes = {}

        # === 校验 1: Bio 禁词检查 ===
        bio = tailored.get('bio', '')
        if bio:
            bio_fixed, bio_warnings = self._validate_bio(bio)
            if bio_fixed != bio:
                fixes['bio'] = bio_fixed
                tailored['bio'] = bio_fixed
            warnings.extend(bio_warnings)

        # === 校验 2: Title 合法性 ===
        title_errors = self._validate_titles(tailored.get('experiences', []))
        errors.extend(title_errors)

        # === 校验 3: 技能合法性 ===
        jd_text = job.get('description', '')
        skill_errors, skill_warns = self._validate_skills(
            tailored.get('skills', []), jd_text)
        errors.extend(skill_errors)
        warnings.extend(skill_warns)

        # === 校验 4: 重复内容检测 ===
        dup_warnings = self._check_duplicates(tailored)
        warnings.extend(dup_warnings)

        # === 校验 5: 结构完整性 ===
        struct_errors = self._validate_structure(tailored)
        errors.extend(struct_errors)

        passed = len(errors) == 0
        return ValidationResult(passed, errors, warnings, fixes)

    def _validate_bio(self, bio: str) -> tuple[str, list[str]]:
        """校验并自动修复 bio"""
        warnings = []
        constraints = self.config.get('bio_constraints', {})
        banned = constraints.get('banned_phrases', [])

        # 替换禁词
        replacements = {
            "deep expertise": "hands-on experience",
            "extensive experience": "experience",
            "proven track record": "track record",
            "cutting-edge": "modern",
        }

        fixed = bio
        for phrase, replacement in replacements.items():
            if phrase.lower() in fixed.lower():
                # 大小写保留替换
                import re
                fixed = re.sub(re.escape(phrase), replacement, fixed, flags=re.IGNORECASE)
                warnings.append(f"Bio: replaced '{phrase}' with '{replacement}'")

        # 检查年数声明
        import re
        year_claims = re.findall(r'(\d+)\+?\s*years?', fixed)
        max_years = constraints.get('max_years_claim', 6)
        for years_str in year_claims:
            years = int(years_str)
            if years > max_years:
                warnings.append(
                    f"Bio claims {years}+ years, max allowed is {max_years}")

        return fixed, warnings

    def _validate_titles(self, experiences: list) -> list[str]:
        """校验职位名称是否在允许范围内"""
        errors = []
        title_options = self.config.get('title_options', {})

        # 公司名到 key 的映射
        company_map = {
            'glp technology': 'glp_technology',
            'baiquan investment': 'baiquan_investment',
            'ele.me': 'eleme',
            'henan energy': 'henan_energy',
        }

        for exp in experiences:
            company = exp.get('company', '').lower()
            title = exp.get('title', '')

            for company_pattern, config_key in company_map.items():
                if company_pattern in company:
                    allowed = title_options.get(config_key, {})
                    all_titles = set(allowed.values())
                    if title not in all_titles:
                        errors.append(
                            f"Title '{title}' for {exp['company']} not in allowed list: "
                            f"{all_titles}")
                    break

        return errors

    def _validate_skills(self, skills: list, jd_text: str) -> tuple:
        """校验技能列表合法性"""
        errors = []
        warnings = []
        tiers = self.config.get('skill_tiers', {})
        excluded = [s.lower() for s in tiers.get('excluded', [])]

        for skill_group in skills:
            items = skill_group.get('skills_list', '')
            for excluded_skill in excluded:
                if excluded_skill in items.lower():
                    errors.append(
                        f"Excluded skill '{excluded_skill}' found in "
                        f"category '{skill_group.get('category')}'")

        return errors, warnings

    def _check_duplicates(self, tailored: dict) -> list[str]:
        """检测重复出现的技能/内容"""
        warnings = []

        # 检查技能是否跨类别重复
        all_skills = []
        for skill_group in tailored.get('skills', []):
            items = [s.strip().lower()
                     for s in skill_group.get('skills_list', '').split(',')]
            for item in items:
                if item in all_skills:
                    warnings.append(f"Duplicate skill across categories: '{item}'")
                all_skills.append(item)

        return warnings

    def _validate_structure(self, tailored: dict) -> list[str]:
        """结构完整性校验"""
        errors = []

        exps = tailored.get('experiences', [])
        if len(exps) < 2:
            errors.append(f"Only {len(exps)} experience(s), minimum is 2")

        for exp in exps:
            if not exp.get('bullets') or len(exp['bullets']) == 0:
                errors.append(f"No bullets for {exp.get('company', '?')}")
            if not exp.get('location'):
                errors.append(f"Missing location for {exp.get('company', '?')}")

        skills = tailored.get('skills', [])
        if len(skills) < 3:
            errors.append(f"Only {len(skills)} skill categories, minimum is 3")

        return errors
```

**验证器集成到流水线：**

```python
# resume_renderer.py 修改
def render_resume(self, job_id):
    ...
    tailored = json.loads(tailored_json)

    # 新增：后置验证
    validator = ResumeValidator()
    result = validator.validate(tailored, job)

    if not result.passed:
        print(f"  [BLOCKED] {len(result.errors)} validation errors:")
        for err in result.errors:
            print(f"    ✗ {err}")
        return None  # 不渲染，阻断

    if result.warnings:
        print(f"  [WARN] {len(result.warnings)} warnings:")
        for warn in result.warnings:
            print(f"    ⚠ {warn}")

    if result.fixes:
        print(f"  [AUTO-FIX] Applied {len(result.fixes)} fixes")
        # fixes 已在 validate() 中直接修改了 tailored
    ...
```

---

### 阶段 4：角色模板系统评估

#### 现状

`config/role_templates.yaml` 定义了 4 种角色的：
- 关键词权重（分类器）
- 经历排序
- 职位名称映射
- 项目选择
- 技能结构
- Bio 模板

#### 评估

**结论：当前形态不需要保留。**

原因：
1. AI Analyzer 已经根据 JD 动态做了所有这些决策（选哪些经历、什么顺序、什么技能）
2. role_templates.yaml 的角色分类逻辑和 scoring.yaml 的关键词权重有大量重复
3. 模板中的 `file: "templates/ml_engineer.html"` 等指向不存在的文件
4. AI 做 JD-specific 定制比固定模板更灵活、更精准

**但有价值的部分应迁移：**
- `keyword_weights` → 合并到 `scoring.yaml`
- `company_override` → 保留（量化公司强制覆盖有用）
- `title_mapping` → 迁移到 bullet library 的 `title_options`
- `skills_structure` → 迁移到 bullet library 的 `skill_tiers`

**行动：** 将 `role_templates.yaml` 中的有效配置迁移到其他配置文件后，标记为 deprecated。不删除，但不再在主流程中使用。

---

### 阶段 5：Post-Render QA（渲染后质检）

在 PDF 生成后增加最终检查：

```python
class PostRenderQA:
    """渲染后质量检查"""

    def check(self, html_content: str, tailored: dict) -> list[str]:
        issues = []

        # 1. URL 一致性
        if 'feithink.substack.com' in html_content and \
           'huangf06.github.io/FeiThink' in html_content:
            issues.append("两个不同的博客 URL 同时出现")

        # 2. 认证重复出现次数
        cert_count = html_content.lower().count('databricks certified')
        if cert_count > 2:
            issues.append(f"Databricks 认证出现 {cert_count} 次（建议不超过 2 次）")

        # 3. 页面长度估算（A4 约 3500 字符/页）
        text_only = re.sub(r'<[^>]+>', '', html_content)
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        estimated_pages = len(text_only) / 3500
        if estimated_pages > 2.5:
            issues.append(f"预估 {estimated_pages:.1f} 页，可能过长")
        if estimated_pages < 0.8:
            issues.append(f"预估 {estimated_pages:.1f} 页，内容可能过少")

        # 4. 空 bullet 检测
        if '<li></li>' in html_content or '<li> </li>' in html_content:
            issues.append("检测到空的 bullet point")

        # 5. HTML 实体转义检查
        if '&amp;amp;' in html_content:
            issues.append("双重 HTML 转义（&amp;amp;）")

        return issues
```

---

## 三、新增 Bullet 建议

### 3.1 Databricks / Data Governance Bullet（GLP）

```yaml
# 新增到 glp_technology.verified_bullets
- id: glp_data_compliance
  content: "Managed credit scoring data workflows involving sensitive customer data
    (credit bureau records, personal financial data); implemented access controls
    and data validation checks to ensure compliance with internal data governance
    policies."
  verified: true
  can_defend:
    - "处理过大量客户征信数据"
    - "有数据合规意识和实操"
    - "实现过权限控制"
  tags:
    role_fit: [data_engineer, risk_analyst]
    tech_stack: [python, sql]
    domain: [fintech, data_governance]
```

### 3.2 百泉数据质量 Bullet

```yaml
# 新增到 baiquan_investment.verified_bullets
- id: bq_data_quality
  content: "Designed data validation pipelines to verify market data integrity
    (price adjustments, corporate actions, trading suspensions); ensured clean
    inputs for quantitative models across 3000+ securities."
  verified: true
  can_defend:
    - "确实做了大量数据校验工作"
    - "处理复权、停牌、分红等数据"
  tags:
    role_fit: [data_engineer, quant_developer]
    tech_stack: [python, pandas]
    domain: [finance, data_quality]
```

### 3.3 修正 GLP PySpark Bullet

```yaml
# 修改 glp_pyspark
- id: glp_pyspark
  content: "Utilized PySpark for batch processing of risk datasets, supporting
    daily reporting workflows; mentored junior analyst on data processing best
    practices."
  # 注意：从 "Led PySpark batch processing workflows to process large-scale
  # datasets" 降级为更诚实的表述
  verified: true
  can_defend:
    - "Did work with PySpark"
    - "Did mentor junior analyst"
```

---

## 四、配置变更清单

| 文件 | 变更 | 优先级 |
|------|------|--------|
| `assets/bullet_library.yaml` | 新增 `skill_tiers`, `title_options`, `bio_constraints` | P0 |
| `assets/bullet_library.yaml` | 新增 `glp_data_compliance`, `bq_data_quality` bullets | P0 |
| `assets/bullet_library.yaml` | 修正 `glp_pyspark` bullet 措辞 | P0 |
| `config/base/filters.yaml` | 新增 `specific_tech_experience` 硬排除规则 | P0 |
| `config/ai_config.yaml` | Prompt 中注入技能分层、title 约束、bio 约束 | P0 |
| `scripts/resume_validator.py` | 新建后置验证器 | P1 |
| `scripts/ai_analyzer.py` | 重构 `_build_prompt()` 以注入新约束 | P1 |
| `scripts/resume_renderer.py` | 集成验证器 + QA | P1 |
| `templates/base_template.html` | 统一博客 URL 为变量 | P2 |
| `config/role_templates.yaml` | 有效配置迁出后标记 deprecated | P2 |

---

## 五、实施顺序

```
Phase 1 (立即): 数据层
  ├── bullet_library 新增 skill_tiers / title_options / bio_constraints
  ├── 新增 GLP + 百泉 bullets
  ├── 修正 glp_pyspark
  └── filters.yaml 新增硬排除规则

Phase 2 (核心): AI + 验证
  ├── 重构 AI prompt（注入约束）
  ├── 实现 ResumeValidator
  ├── 集成到 resume_renderer
  └── 实现 PostRenderQA

Phase 3 (优化): 清理
  ├── 迁移 role_templates 有效配置
  ├── 统一模板 URL
  └── 清理两个 bullet library
```

---

## 六、验收标准

改进完成后，对以下场景做回归测试：

1. **ABN AMRO (7y Azure)** → 应被 Hard Filter v3 拦截，不进入 AI
2. **一个 Data Engineer JD** → Bio 不应出现 "deep expertise"、年数不超限、Delta Lake 不重复出现
3. **一个 ML Engineer JD** → GLP 职位名应为 "ML Engineer & Team Lead"，不是 "Data Engineer"
4. **一个 Java-heavy JD** → Hard Filter 拦截
5. **一个要求 Kafka 的 DE JD** → Kafka 出现在 skills 中（可转移技能被激活）
6. **一个要求 React 的 Full Stack JD** → 被 Hard Filter 或 scoring 拦截
7. **批量生成 10 份简历** → 验证器 0 errors，warnings 合理

---

## 七、与当前审计发现的对应关系

| 审计发现 | 改进措施 | 阶段 |
|---------|---------|------|
| Bio "6+ years" 不可辩护 | bio_constraints + Validator 自动校验 | Phase 1+2 |
| PySpark bullet 矛盾 | 修正 bullet 措辞 | Phase 1 |
| GLP 职位名虚高 | title_options 约束表 | Phase 1 |
| Delta Lake 技能重复 | Validator 重复检测 | Phase 2 |
| 7y Azure 应硬排除 | filters.yaml 新规则 | Phase 1 |
| 技能无分层策略 | skill_tiers 三层体系 | Phase 1 |
| 两个 bullet library | 合并为唯一真相源 | Phase 3 |
| 博客 URL 不一致 | 模板变量化 | Phase 3 |
| role_templates 死代码 | 迁移有效配置后 deprecate | Phase 3 |
