# Block B + C Unified Design

**Date**: 2026-03-28
**Status**: Approved
**Decision**: Block B whitelist-only simplification + Block C split into C1 (Evaluate) + C2 (Tailor)

---

## 设计原则

> **Block B 只做客观、二元、正则可 100% 判定的过滤。所有需要"理解 JD 语义"的判断交给 Block C (AI)。**

- Block B 是粗筛，宁可放过，不可误杀
- Block C 分两步: 评分和简历定制是不同认知模式 (判断题 vs 创作题)，分开避免互相干扰
- Cover Letter 不做全文生成，改为 Application Brief (素材包)
- AI 调用唯一路径: Claude Code CLI (`claude -p`)，砍掉 Anthropic SDK

---

## Block B: Hard Filter (简化版)

### 规则表 (8 条)

| # | 规则名 | 类型 | 逻辑 | vs 旧版 |
|---|--------|------|------|---------|
| 0 | 荷兰语 JD | word_count | ≥8 个荷兰语指示词 → reject | 不变 |
| 1 | 荷兰语要求 | regex | "dutch required/native/fluent" → reject | 不变 |
| 2 | 非目标角色 | title_check | **仅白名单** (`title_must_contain_one_of`) | 删除 hard_reject_patterns, reject_patterns, reject_exceptions |
| 3 | 错误技术栈 | tech_stack | **仅标题模式** (Flutter/iOS/.NET/Java Developer 等) | 删除 body_irrelevant_keywords + threshold |
| 4 | 自由职业/ZZP | regex | "zzp", "freelance only", day rate 等 | 不变 |
| 5 | 极低薪酬 | regex | "$1000-2500/month" 等 | 不变 |
| 6 | 高管角色 | title_check | director/vp/cto 等，保留 senior data/ml/ai 例外 | 不变 |
| 7 | 数据不足 | built-in | title 空 / desc 空 / desc < 50 字符 | 不变 |

**额外过滤** (不编号): 公司黑名单、头衔黑名单 (intern/trainee/student)

### 删除清单

| 删除项 | 原规则 | 理由 | 接管方 |
|--------|--------|------|--------|
| title_hard_reject_patterns (13 个) | 规则 2 | recruiter/hr/policy/security engineer 等需语义判断 | Block C1 AI |
| title_reject_patterns (5 个) | 规则 2 | marketing/embedded/legal + data 需语义判断 | Block C1 AI |
| reject_exceptions | 规则 2 | 消除 soft reject 后无需 exceptions | — |
| body_irrelevant_keywords | 规则 3 | JD body 提到前端技术 ≠ 前端岗 | Block C1 AI |
| body_irrelevant_threshold | 规则 3 | 同上 | — |
| specific_tech_experience (规则 5.5) | 规则 5.5 | "5+ years Java" 可能是 nice-to-have | Block C1 AI |
| location_restricted (规则 8) | 规则 8 | "no visa" 可能有上下文例外 | Block C1 AI |
| experience_too_high (规则 6) | 规则 6 | 已 disabled，正式删除 | Block C1 AI |

### 白名单维护

换目标角色时**只需改 `title_must_contain_one_of`**，其他规则不需要动。

---

## Block C: AI Evaluate + Tailor (两步设计)

### 总览

```
Block B passed jobs
       │
       ▼
  ┌─────────────────────────────┐
  │  C1: Evaluate               │  claude -p (~2K 字 prompt, ~300 字输出, ~3-5 秒)
  │  - 评分 (0-10 四维度)       │
  │  - Application Brief        │
  │  - Hard Reject Signals      │
  └─────────────────────────────┘
       │
       │  ai_score >= 4.0?
       │
   no  │  yes
   ▼   ▼
 STOP  ┌─────────────────────────────┐
       │  C2: Tailor Resume          │  claude -p (~8K 字 prompt, ~2K 字输出, ~15-20 秒)
       │  - Bio + Experiences        │
       │  - Projects + Skills        │
       │  - Bullet selection         │
       └─────────────────────────────┘
       │
       ▼
  job_analysis 表 (完整记录)
```

### C1: Evaluate

**输入**: JD + 候选人简介 (短版 ~500 字，不含 bullet library)

**Prompt 结构** (~2000 字):
1. Candidate Profile (短版: name, education, key skills, years)
2. Hard Reject Signals (从 Block B 移交的语义判断)
3. Scoring Guidelines (1-10 分布目标)
4. Target Job (title, company, JD 全文)
5. Output format (JSON)

**Hard Reject Signals** (AI 评分指引):
```
If ANY of the following is true, score overall 1-2 and recommend SKIP:
- Title indicates non-target role: recruiter, HR, policy, accountant,
  finance manager, pure marketing/sales/legal (without data/ML qualifier)
- Primary tech stack is clearly wrong: embedded systems, kernel, PLC,
  SIEM, network engineering, release engineering
- JD requires visa/residency candidate cannot provide:
  "no visa sponsorship", "must be located in [non-NL country]"
- JD requires 5+ years of specific tech candidate lacks
  (Java, C++, Scala, Ruby, .NET, Azure)
- Role is too senior: Director, VP, CTO, Head of, Principal
  (exception: "Senior Data/ML/AI Engineer/Scientist" is fine)
```

**输出**:
```json
{
  "scoring": {
    "overall_score": 7.5,
    "skill_match": 8.0,
    "experience_fit": 7.0,
    "growth_potential": 7.5,
    "recommendation": "APPLY",
    "reasoning": "Strong Python/ML match..."
  },
  "application_brief": {
    "hook": "Financial Data Lakehouse 项目和他们的 data platform 方向直接对口",
    "key_angle": "Databricks certified + PySpark pipeline 经验匹配 JD 核心要求",
    "gap_mitigation": "JD 要求 Kafka，但 Spark Structured Streaming 是同类技术",
    "company_connection": null
  }
}
```

### C2: Tailor Resume

**运行条件**: C1 output ai_score >= 4.0

**输入**: JD + bullet library 全文 + C1 的 reasoning

**Prompt 结构** (~8000 字):
1. Context (job title, company, C1 reasoning)
2. Bullet Library 全文 (含 narrative_role 标签)
3. Selection Rules (bio, bullet selection, narrative composition, skills)
4. Output format (JSON)

**输出**:
```json
{
  "tailored_resume": {
    "bio": { "role_title": "...", "years": 6, ... },
    "experiences": [ { "company": "...", "bullets": ["id1", "id2"] } ],
    "projects": [ { "name": "...", "bullets": ["id1"] } ],
    "skills": [ { "category": "...", "skills_list": "..." } ]
  }
}
```

### Cover Letter → Application Brief

**不做 CL 全文生成。** 理由:
1. 大多数申请场景 (LinkedIn Easy Apply, ATS) 不需要 CL
2. AI 生成的 CL 容易被 HR 识别，比不发更糟
3. 真正需要 CL 时，用 Application Brief 素材手写 5 分钟，质量远高于 AI 全文

Application Brief 合并在 C1 输出中，零额外 AI 调用。

### DB 写入策略

**C1 写入 `job_analysis`** (INSERT):
- ai_score, skill_match, experience_fit, growth_potential
- recommendation, reasoning
- application_brief JSON (存入 reasoning 或新字段)
- tailored_resume = `'{}'`

**C2 更新 `job_analysis`** (UPDATE WHERE job_id = ?):
- tailored_resume JSON

两步写同一张表，C2 是 UPDATE 不是 INSERT。

### 推荐阈值

| 档位 | overall_score | C2 运行? | 动作 |
|------|--------------|---------|------|
| APPLY_NOW | >= 7.0 | 是 | 高优先级 |
| APPLY | >= 5.0 | 是 | 正常申请 |
| MAYBE | >= 4.0 | 是 | 生成简历备用 |
| MAYBE_LOW | 3.0-3.9 | 否 | 仅存评分 |
| SKIP | < 3.0 | 否 | 跳过 |

---

## AI 调用方式

**唯一路径**: `claude -p --output-format text --max-turns 1`

砍掉 Anthropic SDK 路径 (`_init_client`, API key, bearer auth, rate limit retry)。

### ai_config.yaml 清理

| 删除 | 理由 |
|------|------|
| `models.opus` | SDK 路径 |
| `models.kimi` | SDK 路径 |
| `budget` section | flat subscription |
| `cost_per_1k_tokens` | flat subscription |
| `thresholds.rule_score_for_ai` | 无 rule score |

| 新增/修改 | 用途 |
|-----------|------|
| `prompts.evaluator` | C1 prompt template |
| `prompts.tailor` | C2 prompt template (原 `prompts.analyzer` 拆分) |
| `thresholds.ai_score_generate_resume: 4.0` | C1→C2 门槛 |

---

## AIAnalyzer 重构

```python
class AIAnalyzer:
    """Block C: AI 评估 + 简历定制 (Claude Code CLI only)"""

    def __init__(self):
        self.config = load ai_config.yaml
        self.bullet_library = load bullet_library.yaml
        self.validator = ResumeValidator()

    # ── C1: Evaluate ──
    def evaluate_job(self, job) -> AnalysisResult:
        prompt = self._build_evaluate_prompt(job)
        response = self._call_claude(prompt)
        return self._parse_evaluate_response(job, response)

    # ── C2: Tailor ──
    def tailor_resume(self, job, analysis) -> dict:
        prompt = self._build_tailor_prompt(job, analysis)
        response = self._call_claude(prompt)
        return self._parse_tailor_response(job, response)

    # ── 统一调用 ──
    def _call_claude(self, prompt) -> str:
        """claude -p --output-format text --max-turns 1"""
```

### 砍掉的代码

| 删除 | 行数估计 |
|------|---------|
| `_init_client()` | ~15 行 |
| bearer auth 逻辑 | ~10 行 |
| API key 环境变量处理 | ~15 行 |
| `analyze_job()` 中 SDK 调用分支 | ~50 行 |
| `_build_prompt()` 单一大 prompt | ~80 行 (拆成两个 builder) |

---

## CLI 接口

```bash
python scripts/job_pipeline.py --process          # Block B only
python scripts/job_pipeline.py --ai-analyze       # C1 + C2 串行
python scripts/job_pipeline.py --ai-evaluate      # 只跑 C1
python scripts/job_pipeline.py --ai-tailor        # 只跑 C2 (补跑)
python scripts/job_pipeline.py --analyze-job ID   # 单条 C1+C2 调试
```

## CI 流程

```yaml
Step 1: Scrape
Step 2: Import + Hard Filter (--process)
Step 3: AI Evaluate (--ai-evaluate --limit 30)     # C1: 全部，快
Step 4: AI Tailor (--ai-tailor --limit 30)          # C2: 仅高分，慢
Step 5: Notify
```

C1 和 C2 拆成两个 CI step: C1 失败不影响已有评分，C2 超时可用 `--ai-tailor` 补跑。

### 吞吐估算

- 日均 ~15-20 通过 Block B
- C1: 20 × 5 秒 = ~100 秒
- C2: ~8-10 个 (score ≥ 4.0) × 20 秒 = ~160-200 秒
- 总计: ~5 分钟，在 90 分钟 CI timeout 内安全

---

## 测试策略

### Block B (~40-45 tests)

每条规则: 1 命中 + 1 豁免 + 1 边界

| 规则 | 命中 | 豁免 | 边界 |
|------|------|------|------|
| 荷兰语 JD | ≥8 词 | 7 词 | — |
| 荷兰语要求 | "dutch required" | — | — |
| 非目标角色 (白名单) | "Account Manager" | "Data Engineer" | "BI Analyst" (短词) |
| 错误技术栈 (标题) | "Flutter Developer" | "Data Engineer" 例外 | `.NET`/`C#` 边界 |
| 自由职业 | "zzp" | "full-time" 例外 | — |
| 极低薪酬 | "$1400/month" | — | — |
| 高管角色 | "VP Engineering" | "Senior Data Scientist" | — |
| 数据不足 | desc 空 | — | 49 vs 50 字 |
| 黑名单 | 命中 | — | — |
| 优先级 | 荷兰语先于白名单 | — | — |

### Block C (解析 + 验证)

| 测试 | 内容 |
|------|------|
| C1 正常 JSON | scoring + brief 全字段解析 |
| C1 缺字段 | recommendation 缺失 → 默认 SKIP |
| C1 score 边界 | 3.9 不触发 C2, 4.0 触发 C2 |
| C1 malformed | 返回 REJECTED |
| C2 bullet 解析 | 已知 ID → 文本, 未知 → 跳过 |
| C2 bio 组装 | structured spec → 文本 |
| C2 validator | 标题白名单, 技能排除, 最少 2 经历 |
| C2 UPDATE | 不覆盖 C1 scoring 字段 |

不做 AI 端到端测试，prompt 质量靠 `--analyze-job JOB_ID` 人工抽查。
