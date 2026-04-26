# DocBridge - 中欧贸易文档智能处理平台

## 设计文档 (2026-04-26)

## 背景与动机

三重目标驱动的项目：
1. **Portfolio** — 展示端到端 ML 系统设计能力，覆盖 ML Engineer 面试要求的全部 P0 skill gaps（model fine-tuning, FastAPI serving, Docker, MLflow, monitoring, CI/CD）
2. **IND 自雇签证** — 注册 KVK，提交可信商业计划，保持在荷合法居留
3. **商业验证** — 探索中欧贸易文档处理的真实市场需求

## 市场调研结论

### 贸易规模
- 2024 年中国对荷兰出口 $912 亿美元，荷兰是中国在欧盟前三大贸易伙伴
- 鹿特丹港是中国货物进入欧洲的最大门户（COSCO、菜鸟、京东物流均有仓储）

### 文档痛点
- 中欧贸易涉及大量跨语言单据：商业发票、装箱单、提单、报关单、原产地证明、CE 认证、CBAM 申报
- 中文供应商文档需与英文/荷兰文报关单据人工对齐
- EU ICS2 于 2026-02 全面强制电子申报，不合规罚款 €5000/单

### 竞品空白
- 中国端有合合信息/TextIn（服务中国出海企业），但**欧洲端没有专门处理中文贸易文档的产品**
- 荷兰货代/报关行处理中文文档仍依赖人工或通用 OCR（对中文效果差）

### 获客渠道
- NCBC (Netherlands China Business Council)、NCHK (Dutch Chinese Chamber of Commerce)、ACIEN (在荷中资企业协会)
- 冷启动策略：先从荷兰华人贸易圈切入，用中文沟通

## 产品定位

帮助荷兰/欧洲端的进口商、货代和报关行，把中文贸易文档自动转成欧盟海关申报所需的结构化数据。

核心用户：
- 鹿特丹货代公司（每天处理中文发票/装箱单）
- 荷兰中小进口商（从中国供应商收到中文 PDF）
- 报关行（多客户中国进口单据）

## 技术架构

```
Web UI / API (上传文档 → 查看结果)
         │
         ▼
FastAPI Service Layer
  - POST /extract  (上传图片/PDF)
  - GET  /result/{id}
  - GET  /health
         │
         ▼
Document Processing Pipeline
  1. 预处理 (去噪、纠偏、分页)
  2. OCR (PaddleOCR 中文 + EasyOCR 欧洲语言)
  3. Layout Analysis (LiLT / LayoutLMv3)
  4. Field Extraction (token classification)
  5. 后处理 (字段校验、HS 编码映射、金额标准化)
         │
         ▼
Output: Structured JSON
  {
    "seller": "深圳XX贸易有限公司",
    "buyer": "Import BV, Rotterdam",
    "items": [...],
    "total_amount": {"value": 45200, "currency": "USD"},
    "hs_codes": ["8471.30", "8473.30"],
    "confidence": 0.94
  }
```

### 技术选型

| 层 | 技术 | 理由 |
|---|---|---|
| 模型训练 | PyTorch + HuggingFace Transformers | 生态成熟，LiLT/LayoutLMv3 预训练模型可直接 fine-tune |
| OCR | PaddleOCR | 中文识别精度远超 Tesseract |
| Layout Model | LiLT (优先) / LayoutLMv3 | LiLT 设计上 language-independent，中英混合场景无需重新预训练 |
| 实验管理 | MLflow | 业界标准，面试加分 |
| Serving | FastAPI + Docker | 轻量、高性能 |
| 监控 | Prometheus + Grafana | API latency、OCR 准确率 drift、处理量 |
| CI/CD | GitHub Actions | lint + test + model validation gate |

### 训练数据

| 数据集 | 内容 | 规模 | 用途 |
|--------|------|------|------|
| SCID | 6 类中文发票 | 有标注 | 中文发票字段提取 |
| VATI | 增值税发票，16 实体 | 3000 张 | 中国标准发票 |
| FATURA | 多布局发票 | 10,000 张 | 欧洲端发票理解 |
| Customs Declaration Dataset | 海关进口申报 | 54,000 条 | HS 编码分类 |
| FUNSD / CORD / SROIE | 表单、收据 | LayoutLM benchmark | 预训练 baseline |

## 项目结构

```
docbridge/
├── src/
│   ├── api/                    # FastAPI 服务
│   ├── pipeline/               # 文档处理 pipeline
│   │   ├── preprocessor.py
│   │   ├── ocr_engine.py
│   │   ├── layout_analyzer.py
│   │   ├── field_extractor.py
│   │   └── pipeline.py
│   ├── training/               # 模型训练
│   │   ├── dataset.py
│   │   ├── train.py
│   │   └── evaluate.py
│   └── monitoring/
├── models/                     # 模型 artifacts
├── data/                       # 数据集 (gitignore)
├── notebooks/                  # 实验记录
├── tests/
├── docker-compose.yml
├── Dockerfile
├── mlflow/
├── .github/workflows/
└── docs/
    └── business_plan/          # IND 商业计划书
```

## 时间线 (12 周)

| 周 | 里程碑 | 产出 |
|---|---|---|
| 1 | 环境搭建 + 数据准备 | 仓库初始化，数据下载清洗，PaddleOCR baseline |
| 2-3 | 模型训练 | LiLT fine-tune 中文发票，MLflow 实验记录 |
| 4 | API + 部署 | FastAPI 服务，Docker 容器化，在线 demo |
| 5-6 | 客户验证 | 联系 NCBC/NCHK，带 demo 访谈 3-5 家公司 |
| 7-8 | 基于反馈迭代 | 真实文档样本迭代模型，加监控 |
| 9-10 | 产品化 | Web UI，用户注册，API key 管理 |
| 11-12 | 收尾 | IND 商业计划书，KVK 注册，简历更新 |

## 交付物

1. **Portfolio**: GitHub 仓库 + README + 在线 demo + MLflow 实验截图
2. **IND 商业计划书**: KVK eenmanszaak 注册 + 商业计划 + 定价模型 (€0.50/页 或 €99/月/200 页)
3. **客户验证**: 至少 3 家公司访谈记录 + 真实文档样本 + 需求确认

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 客户验证发现需求不存在 | Step 1 先做技术 demo，零客户投入；pivot 到其他文档类型成本低 |
| 训练数据不足 | 公开数据集 + 真实样本 + 合成数据 |
| 模型精度不够 | MVP 接受 "AI 提取 + 人工校验" hybrid 模式 |
| 12 周做不完 | 每个 phase 只聚焦 1 种文档类型 |

## 决策记录

- **为什么不包装 job-hunter**: job-hunter 的 AI 部分是 LLM API 调用，不展示 ML 训练能力；LinkedIn 爬虫有法律风险；求职者是差客户群
- **为什么选中欧贸易文档**: 荷兰作为中欧贸易门户有真实场景；竞品空白在欧洲端；IND 叙事天然强；多语言是个人差异化优势
- **为什么先做 demo 再做客户验证**: 带着能跑的产品聊天比空手套白狼有效；客户看到效果才能给出真实反馈
- **为什么 LiLT 优先于 LayoutLMv3**: language-independent 设计，中英混合场景不需要重新预训练
