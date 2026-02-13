# 简历质量审查 Prompt (for Claude Opus 4.6)

## 任务目标
作为资深简历顾问和招聘专家，深度审查自动生成的简历，识别所有质量问题并提供具体改进方案。

---

## 输入信息

### 1. 简历文件路径
```
C:\Users\huang\github\job-hunter\output\Fei_Huang_ABN_AMRO_Bank_N_V_20260206_1333.html
```

### 2. 目标职位信息
- **公司**: ABN AMRO Bank N.V.
- **职位**: Data Engineer (根据文件名推断)
- **职位描述**: [请提供具体JD]

### 3. 候选人背景档案
```yaml
name: Fei Huang
education:
  - VU Amsterdam, M.Sc. AI (2023-2025)
  - Tsinghua University, B.S. (2010-2013)
  
work_experience:
  - GLP Technology: Jul 2017 - Aug 2019 (Data Analyst / Risk Operations Lead)
  - Independent Investor: Sep 2019 - Aug 2023 (Career transition period)
  - Baiquan Investment: Jul 2015 - Jun 2017 (Quantitative Researcher)
  - Ele.me: Sep 2013 - Jul 2015 (Early career)

core_goal: 找到可以 sponsor visa 的荷兰职位 → 2.5年后获得永居/护照
target_roles: [ML Engineer, Data Engineer, Data Scientist, Quant Researcher]
```

### 4. Bullet Library 路径
```
C:\Users\huang\github\resume_project\bullet_library.yaml
```

### 5. 角色模板配置路径
```
C:\Users\huang\github\job-hunter\config\role_templates.yaml
```

---

## 审查维度 (按优先级排序)

### 🔴 P0 - 致命问题 (必须修复)

1. **事实准确性验证**
   - [ ] 所有日期是否与 Profile2.0.pdf 一致
   - [ ] 职位头衔是否合理（不能过度包装）
   - [ ] 技术栈声明是否能在面试中辩护
   - [ ] 量化数据是否有依据

2. **单一真实来源验证**
   - [ ] 所有 bullets 是否来自 bullet_library.yaml
   - [ ] 是否有 AI 擅自改写/编造的内容
   - [ ] 是否使用了未经验证的 claims

3. **一页纸硬性约束**
   - [ ] 渲染后是否严格一页
   - [ ] 是否有溢出或截断
   - [ ] 页边距是否正确 (0.5in 四边)

### 🟠 P1 - 严重问题 (强烈建议修复)

4. **角色匹配度**
   - [ ] 简历定位是否与目标职位一致
   - [ ] 经历顺序是否针对该角色优化
   - [ ] 技能展示是否符合该角色期望

5. **关键词优化**
   - [ ] JD 中的 must-have 技能是否都在简历中
   - [ ] 关键词是否自然融入（非堆砌）
   - [ ] 是否包含荷兰/欧洲市场的偏好术语

6. **叙事一致性**
   - [ ] 整体故事是否连贯
   - [ ] 职业轨迹是否合理
   - [ ] 空窗期 (2019-2023) 处理是否恰当

### 🟡 P2 - 中等问题 (建议改进)

7. **表达质量**
   - [ ] 动词是否强有力 (Built, Developed, Led, Improved)
   - [ ] 量化指标是否具体可信
   - [ ] 是否避免空洞形容词

8. **格式规范**
   - [ ] 时间格式是否统一
   - [ ] 标点符号是否一致
   - [ ] 字体/字号是否合适

9. **冗余与精简**
   - [ ] 是否有重复信息
   - [ ] 是否有无关内容
   - [ ] 每行是否信息密度最大化

### 🟢 P3 - 优化建议 (锦上添花)

10. **差异化亮点**
    - [ ] 是否有独特的卖点
    - [ ] 是否突出清华+VU 的顶级学历
    - [ ] 是否体现 quant + ML 的复合背景

11. **ATS 友好性**
    - [ ] 是否避免表格/图表
    - [ ] 是否使用标准 section headers
    - [ ] 文件名是否规范

---

## 输出格式

### 执行摘要
```
总体评分: X/100
是否可用: ✅ 可直接使用 / ⚠️ 需修改后使用 / ❌ 需重写
预计修复时间: X 分钟
```

### 问题清单 (按优先级分组)

#### 🔴 P0 - 致命问题
| # | 问题描述 | 具体位置 | 修复建议 | 验证方法 |
|---|---------|---------|---------|---------|
| 1 | ... | ... | ... | 对照 bullet_library.yaml |
| 2 | ... | ... | ... | 检查 Profile2.0.pdf |

#### 🟠 P1 - 严重问题
| # | 问题描述 | 影响 | 修复建议 |
|---|---------|------|---------|
| 1 | ... | ... | ... |

#### 🟡 P2 - 中等问题
...

#### 🟢 P3 - 优化建议
...

### 改进后的简历代码
```html
<!-- 提供完整的修复后 HTML -->
```

### 流程改进建议
基于本次审查，提出自动化流程的系统性改进建议：
1. ...
2. ...
3. ...

---

## 特殊审查规则

### 1. Bullet 来源验证
对于每个 bullet point，必须确认：
- ✅ 直接复制自 bullet_library.yaml
- ✅ 使用了 library 中的 role-specific variants
- ❌ AI 自行改写或创作

### 2. 时间线验证
对照 Profile2.0.pdf 验证：
```
- Henan Energy: Jul 2010 - Aug 2013 (3 years 2 months)
- Ele.me: Sep 2013 - Jul 2015 (1 year 11 months)
- Baiquan Investment: Jul 2015 - Jun 2017 (2 years)
- GLP Technology: Jul 2017 - Aug 2019 (2 years 2 months)
- Proprietary Trading: Sep 2019 - Aug 2023 (4 years)
- VU Amsterdam MSc AI: Sep 2023 - Aug 2025
```

### 3. 职位头衔规范
根据目标角色使用正确的头衔变体：
- **Data Engineer**: "Data Engineer & Risk Lead"
- **ML Engineer**: "ML Engineer / Data Scientist"
- **Quant**: "Quantitative Developer"
- **Data Analyst**: "Data Analyst"

### 4. 禁止事项清单
- ❌ 不要 Professional Summary section
- ❌ 不要 "15% accuracy improvement" 等无基准的量化
- ❌ 不要 "Led 5-person team" (实际只有 1 个 report)
- ❌ 不要 XGBoost/Random Forest (实际用 logistic regression)
- ❌ 不要 Deep Spark experience (只学了基础)

---

## 执行指令

1. **读取简历文件** - 加载 HTML 内容
2. **读取 bullet_library.yaml** - 验证所有 bullets 来源
3. **读取 role_templates.yaml** - 确认模板配置正确应用
4. **逐项审查** - 按 P0/P1/P2/P3 维度检查
5. **生成报告** - 按输出格式提供完整分析
6. **提供修复版本** - 给出可直接使用的改进后 HTML
7. **流程建议** - 提出系统性改进方案

请开始审查。
