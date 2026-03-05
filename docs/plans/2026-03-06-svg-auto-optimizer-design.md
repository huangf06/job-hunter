# SVG Resume Auto-Optimizer Design

**Date:** 2026-03-06
**Author:** Claude Opus 4.6
**Status:** Approved

## Overview

An automated system that iteratively generates and optimizes SVG resumes using Claude Vision API for quality assessment, eliminating manual trial-and-error in design refinement.

## Problem Statement

Current SVG resume generation suffers from:
- Text overlap issues requiring manual coordinate adjustment
- No automated quality validation
- Time-consuming iterative design process
- Inconsistent visual quality

## Solution

Single-script iterative optimizer that:
1. Generates SVG from structured data
2. Renders screenshot for visual inspection
3. Uses Claude Vision API to detect issues
4. Automatically applies fixes
5. Repeats until quality threshold met (max 10 iterations)

## Architecture

### Components

```
svg_auto_optimizer.py (~400 lines)
├── SVGResumeGenerator
│   ├── load_data_from_yaml()          # Load from bullet_library.yaml
│   ├── generate_svg(iteration=0)       # Generate SVG file
│   └── apply_fixes(svg_content, fixes) # Apply Vision-suggested fixes
│
├── VisualQualityChecker
│   ├── render_screenshot(svg_path)     # Playwright screenshot
│   ├── analyze_with_vision(image)      # Claude Vision API analysis
│   └── parse_feedback(response)        # Parse JSON feedback
│
├── SVGFixer
│   ├── apply_fixes(svg, issues)        # Apply all fixes
│   ├── _increase_spacing()             # Increase line spacing
│   ├── _adjust_position()              # Adjust element position
│   └── _reduce_font_size()             # Reduce font size
│
└── IterationController
    ├── run_optimization_loop()         # Main loop
    ├── save_iteration(n, svg, issues)  # Save intermediate results
    └── is_approved(feedback)           # Check if approved
```

### Data Flow

```
bullet_library.yaml
    ↓
[Generate Initial SVG] → iteration_0.svg
    ↓
[Playwright Screenshot] → iteration_0.png
    ↓
[Claude Vision Analysis] → issues.json
    ↓
[Parse + Apply Fixes] → iteration_1.svg
    ↓
[Loop, max 10 times]
    ↓
[Vision Returns APPROVED] → final.svg + final.pdf
```

## Vision API Prompt Design (v2.0)

### Key Features

1. **Reference Standards** - Defines "good resume" characteristics
2. **Priority Levels** - P0 (blocking), P1 (severe), P2 (optional)
3. **Structured Location** - Section + element + y-range for precise targeting
4. **Actionable Fixes** - Executable repair instructions
5. **Clear Approval Criteria** - 4 boolean checks + score threshold

### Prompt Structure

```python
VISION_PROMPT_V2 = """
你是一个专业的简历设计质检员，专门审查技术岗位简历的视觉质量。

## 评审标准（参考 Toni Kendel 的 Data Engineer 简历设计）

**优秀简历的特征：**
- 双栏布局清晰（左侧主内容 65%，右侧技能/认证 35%）
- 无文字重叠，所有文本清晰可读
- 视觉层次分明：标题 > 公司名 > 职位 > 正文
- 认证/学历突出显示（用色块或边框）
- 行间距充足（bullet points 之间至少 12-15px）
- 留白适度（不拥挤，不稀疏）
- 专业配色（1-2 种强调色，黑白灰为主）

## 检查清单（按优先级排序）

### P0 - 阻断性问题（必须修复）
1. **文字重叠** - 任何文字互相覆盖、难以阅读
2. **元素溢出** - 内容超出页面边界
3. **关键信息缺失** - 姓名、联系方式、学历、工作经历

### P1 - 严重问题（强烈建议修复）
4. **行间距过小** - bullet points 之间 < 10px
5. **对齐错误** - 左右栏不对齐，日期位置不一致
6. **视觉层次混乱** - 标题不突出，重要信息不明显

### P2 - 优化建议（可选）
7. **留白不足** - 整体过于拥挤
8. **配色单调** - 缺少视觉重点
9. **字体大小** - 正文 < 9px 或标题 < 12px

## 输出格式

{
  "status": "NEEDS_FIX" | "APPROVED",
  "overall_quality_score": 0-10,
  "issues": [
    {
      "priority": "P0" | "P1" | "P2",
      "type": "text_overlap" | "layout" | "spacing" | "visual_hierarchy" | "overflow",
      "location": {
        "section": "WORK EXPERIENCE" | "EDUCATION" | "HEADER" | "RIGHT_COLUMN",
        "element": "GLP Technology 第二个 bullet",
        "approximate_y_range": "350-370px"
      },
      "description": "具体问题：两行文字的 y 坐标差距只有 8px，导致重叠",
      "suggested_fix": {
        "action": "increase_spacing" | "adjust_position" | "reduce_font_size" | "reflow_text",
        "details": "将 y=360 的行移动到 y=375（增加 15px 间距）",
        "affected_elements": ["text 元素 #23", "text 元素 #24"]
      }
    }
  ],
  "positive_aspects": ["认证框设计醒目", "双栏布局清晰"],
  "approval_criteria_met": {
    "no_text_overlap": true/false,
    "proper_spacing": true/false,
    "visual_hierarchy_clear": true/false,
    "professional_appearance": true/false
  },
  "comments": "整体评价和建议"
}

## 审批标准

**APPROVED 条件（必须全部满足）：**
1. overall_quality_score >= 8
2. 无 P0 问题
3. P1 问题 <= 1 个
4. approval_criteria_met 中至少 3/4 为 true
"""
```

### Output Format

Structured JSON with:
- **Priority-based issues** - P0/P1/P2 classification
- **Precise location** - Section + element + y-range
- **Actionable fixes** - Executable repair instructions
- **Approval criteria** - 4 boolean checks + score

## Auto-Fix Logic

### Fix Strategy Mapping

```python
class SVGFixer:
    def apply_fixes(self, svg_content: str, issues: list) -> str:
        """Apply all fixes, P0 and P1 only"""
        for issue in sorted(issues, key=lambda x: priority_order(x['priority'])):
            if issue['priority'] in ['P0', 'P1']:
                svg_content = self._apply_single_fix(svg_content, issue)
        return svg_content

    def _apply_single_fix(self, svg: str, issue: dict) -> str:
        action = issue['suggested_fix']['action']

        if action == 'increase_spacing':
            return self._increase_spacing(svg, issue)
        elif action == 'adjust_position':
            return self._adjust_position(svg, issue)
        elif action == 'reduce_font_size':
            return self._reduce_font_size(svg, issue)
        elif action == 'reflow_text':
            return self._reflow_text(svg, issue)

        return svg
```

### Key Design Decisions

1. **Only fix P0 + P1** - P2 issues may introduce new problems
2. **Incremental fixes** - Move only affected elements, don't rewrite entire SVG
3. **Regex-based** - Precise coordinate targeting and modification
4. **Defensive programming** - Fix failures don't crash, log and continue

## Iteration Control

### Main Loop

```python
class IterationController:
    def run_optimization_loop(self) -> Path:
        for i in range(max_iterations):
            # 1. Generate SVG
            svg_path = generator.generate_svg(iteration=i)

            # 2. Screenshot
            screenshot = checker.render_screenshot(svg_path)

            # 3. Vision analysis
            feedback = checker.analyze_with_vision(screenshot)

            # 4. Save iteration
            self._save_iteration(i, svg_path, screenshot, feedback)

            # 5. Check approval
            if feedback['status'] == 'APPROVED':
                return self._finalize(svg_path)

            # 6. Apply fixes
            fixed_svg = fixer.apply_fixes(svg_content, feedback['issues'])
            generator.update_template(fixed_svg)

        return self._finalize_best_attempt()
```

### Termination Conditions

1. Vision returns `APPROVED` (ideal case)
2. Reaches max iterations (10)
3. Score plateaus for 3 consecutive iterations (local optimum)

## Error Handling

```python
# Vision API failure
try:
    feedback = checker.analyze_with_vision(screenshot)
except Exception as e:
    feedback = fallback_rule_based_check(screenshot)

# Fix failure
try:
    fixed_svg = fixer.apply_fixes(svg_content, issues)
except Exception as e:
    continue  # Skip this fix

# Playwright crash
try:
    screenshot = render_screenshot(svg_path)
except Exception as e:
    screenshot = render_screenshot(svg_path)  # Retry once
```

## File Structure

```
scripts/
├── svg_auto_optimizer.py      # Main script (~400 lines)
└── svg_optimizer_config.yaml  # Configuration

iterations/                     # Iteration history
├── iteration_0/
│   ├── resume.svg
│   ├── preview.png
│   └── feedback.json
├── iteration_1/
└── ...

output/
└── Fei_Huang_Resume_Final.pdf  # Final output
```

## Usage

```bash
python scripts/svg_auto_optimizer.py

# Output:
# === Iteration 0 ===
#   Found 3 issues
# === Iteration 1 ===
#   Found 2 issues
# ...
# === Iteration 5 ===
# ✓ Approved at iteration 5!
#   Quality score: 9/10
# Final resume: output/Fei_Huang_Resume_Final.pdf
```

## Expected Performance

- **Convergence**: 5-8 iterations
- **Total time**: 3-5 minutes
- **Vision API cost**: $0.02-0.03
- **Final quality**: 8-10/10

## Trade-offs

### Chosen Approach: Single-Script Iterative Optimizer

**Pros:**
- Simple to understand and debug
- All logic centralized
- Suitable for one-time design tasks
- Predictable API costs

**Cons:**
- Code may be lengthy (~400 lines)
- Not easily reusable for other design tasks

### Rejected Alternatives

**Agent-Driven Architecture:**
- Too complex for single resume design
- Harder to debug (multiple component interactions)

**Prompt Engineering + Self-Repair:**
- Cannot truly "see" rendered output
- Prone to hallucination (thinks it's fixed when it's not)

## Success Criteria

1. **No text overlap** - All text clearly readable
2. **Professional appearance** - Quality score >= 8/10
3. **Automated convergence** - Reaches approval within 10 iterations
4. **Cost effective** - Total API cost < $0.05

## Next Steps

1. Implement `svg_auto_optimizer.py` following this design
2. Test with current resume data
3. Validate Vision API prompt effectiveness
4. Iterate on fix logic based on real feedback

## References

- Current SVG implementation: `templates/resume_svg_final.svg`
- Preview generator: `scripts/generate_svg_preview.py`
- Data source: `assets/bullet_library.yaml`
- Reference design: `templates/Toni_CV_highres.png`
