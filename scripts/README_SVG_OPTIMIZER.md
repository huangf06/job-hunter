# SVG Resume Auto-Optimizer

自动化 SVG 简历生成和优化系统，使用 Claude Vision API 进行质量评估和迭代改进。

## 功能特性

- **自动生成**: 从 `bullet_library.yaml` 生成 SVG 简历
- **视觉质量检查**: 使用 Claude Vision API 检测文字重叠、间距问题等
- **自动修复**: 根据 Vision API 反馈自动调整布局
- **迭代优化**: 最多 10 次迭代，直到达到质量标准
- **PDF 导出**: 自动生成最终 PDF 文件

## 架构

```
SVGResumeGenerator    → 生成 SVG
    ↓
VisualQualityChecker  → Playwright 截图 + Claude Vision 分析
    ↓
SVGFixer              → 应用自动修复
    ↓
IterationController   → 控制优化循环
```

## 使用方法

### 基本用法

```bash
python scripts/svg_auto_optimizer.py
```

### 高级选项

```bash
# 限制最大迭代次数
python scripts/svg_auto_optimizer.py --max-iterations 5

# 指定输出目录
python scripts/svg_auto_optimizer.py --output-dir ./my_iterations
```

## 输出文件

```
iterations/
├── iteration_0/
│   ├── resume.svg       # 生成的 SVG
│   ├── preview.png      # 截图
│   └── feedback.json    # Vision API 反馈
├── iteration_1/
│   └── ...
└── ...

output/
├── Fei_Huang_Resume_Final.svg  # 最终 SVG
└── Fei_Huang_Resume_Final.pdf  # 最终 PDF
```

## 审批标准

Vision API 会检查以下内容：

### P0 - 阻断性问题（必须修复）
- 文字重叠
- 元素溢出
- 关键信息缺失

### P1 - 严重问题（强烈建议修复）
- 行间距过小
- 对齐错误
- 视觉层次混乱

### P2 - 优化建议（可选）
- 留白不足
- 配色单调
- 字体大小

**APPROVED 条件：**
1. 质量评分 >= 8/10
2. 无 P0 问题
3. P1 问题 <= 1 个
4. 至少 3/4 审批标准满足

## 配置

编辑 `scripts/svg_optimizer_config.yaml` 调整：
- 迭代次数
- 字体大小
- 间距设置
- 审批阈值

## 环境要求

```bash
# 安装依赖
pip install anthropic playwright pyyaml python-dotenv

# 安装 Playwright 浏览器
playwright install chromium
```

## 环境变量

在 `.env` 文件中设置：

```bash
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选
```

## 预期性能

- **收敛时间**: 5-8 次迭代
- **总耗时**: 3-5 分钟
- **API 成本**: $0.02-0.03
- **最终质量**: 8-10/10

## 测试

```bash
# 运行所有测试
pytest tests/test_svg_auto_optimizer.py -v

# 运行特定测试
pytest tests/test_svg_auto_optimizer.py::TestSVGResumeGenerator -v
```

## 故障排除

### Playwright 超时
如果截图超时，检查：
- SVG 文件是否有效
- 字体是否可用
- 增加 `screenshot.timeout_ms` 配置

### Vision API 错误
检查：
- API key 是否正确
- 网络连接
- API 配额

### 质量评分低
- 检查 `bullet_library.yaml` 数据
- 调整字体大小和间距配置
- 查看 `feedback.json` 了解具体问题

## 开发

遵循 TDD 原则：
1. 先写测试
2. 验证测试失败
3. 写最小实现
4. 重构

## 参考

- 设计文档: `docs/plans/2026-03-06-svg-auto-optimizer-design.md`
- 数据源: `assets/bullet_library.yaml`
- 配置: `config/ai_config.yaml`
