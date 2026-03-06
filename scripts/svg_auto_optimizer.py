"""
SVG Resume Auto-Optimizer

Iteratively generates and optimizes SVG resumes using Claude Vision API.

Architecture:
- SVGResumeGenerator: Generate SVG from structured data
- VisualQualityChecker: Analyze visual quality with Claude Vision
- SVGFixer: Apply automated fixes
- IterationController: Orchestrate optimization loop
"""

import sys
from pathlib import Path
import yaml
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SVGResumeGenerator:
    """Generate SVG resume from structured data"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "iterations"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data = None
        self._current_svg = None  # Store current SVG for iterative fixes

    def load_data_from_yaml(self) -> Dict[str, Any]:
        """Load resume data from bullet_library.yaml"""
        yaml_path = PROJECT_ROOT / "assets" / "bullet_library.yaml"

        with open(yaml_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)

        return self.data

    def generate_svg(self, iteration: int = 0) -> Path:
        """Generate SVG file for given iteration"""
        if self.data is None:
            self.load_data_from_yaml()

        # Create iteration directory
        iteration_dir = self.output_dir / f"iteration_{iteration}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        svg_path = iteration_dir / "resume.svg"

        # Use current SVG if available (from fixes), otherwise generate fresh
        if self._current_svg:
            svg_content = self._current_svg
        else:
            svg_content = self._generate_svg_content()

        svg_path.write_text(svg_content, encoding='utf-8')
        return svg_path

    def _generate_svg_content(self) -> str:
        """Generate complete SVG resume with dual-column layout"""
        # Load config for personal info
        config_path = PROJECT_ROOT / "config" / "ai_config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        candidate = config.get('resume', {}).get('candidate', {})
        name = candidate.get('name', 'Fei Huang')
        email = candidate.get('email', '')
        phone = candidate.get('phone', '')
        location = candidate.get('location', '')

        # Build SVG with dual-column layout
        svg_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1100" viewBox="0 0 800 1100">',
            '  <defs>',
            '    <style>',
            '      text { font-family: Arial, sans-serif; }',
            '      .header-name { font-size: 24px; font-weight: bold; fill: #1a1a1a; }',
            '      .header-contact { font-size: 11px; fill: #555; }',
            '      .section-title { font-size: 14px; font-weight: bold; fill: #2c5aa0; text-transform: uppercase; }',
            '      .company-name { font-size: 13px; font-weight: bold; fill: #1a1a1a; }',
            '      .job-title { font-size: 11px; font-weight: 600; fill: #333; }',
            '      .period { font-size: 10px; fill: #666; }',
            '      .bullet { font-size: 10px; fill: #333; }',
            '      .skill-category { font-size: 10px; font-weight: bold; fill: #2c5aa0; }',
            '      .skill-item { font-size: 9px; fill: #333; }',
            '      .cert-box { fill: #e8f0f8; stroke: #2c5aa0; stroke-width: 1.5; }',
            '      .cert-text { font-size: 10px; font-weight: bold; fill: #2c5aa0; }',
            '    </style>',
            '  </defs>',
            '',
            '  <!-- Header -->',
            f'  <text x="40" y="40" class="header-name">{name}</text>',
            f'  <text x="40" y="58" class="header-contact">{email} • {phone} • {location}</text>',
            '  <line x1="40" y1="68" x2="760" y2="68" stroke="#ccc" stroke-width="1"/>',
            '',
        ]

        # Left column (work experience) - 65% width
        left_x = 40
        left_width = 480
        y_pos = 95

        svg_parts.append('  <!-- Left Column: Work Experience -->')
        svg_parts.append(f'  <text x="{left_x}" y="{y_pos}" class="section-title">Work Experience</text>')
        svg_parts.append(f'  <line x1="{left_x}" y1="{y_pos + 3}" x2="{left_x + 150}" y2="{y_pos + 3}" stroke="#2c5aa0" stroke-width="2"/>')
        y_pos += 20

        # Work experience entries
        work_exp = self.data.get('work_experience', {})

        # Order: GLP, Independent, Baiquan, Henan, Aoshen, Eleme
        company_order = ['glp_technology', 'independent_investor', 'baiquan_investment',
                        'henan_energy', 'aoshen_business', 'eleme']

        for company_key in company_order:
            if company_key not in work_exp:
                continue

            company_data = work_exp[company_key]
            if not isinstance(company_data, dict):
                continue

            # Company name
            company_name = company_data.get('company', company_data.get('display_name', ''))
            svg_parts.append(f'  <text x="{left_x}" y="{y_pos}" class="company-name">{self._escape_xml(company_name)}</text>')

            # Period (right-aligned)
            period = company_data.get('period', '')
            svg_parts.append(f'  <text x="{left_x + left_width - 10}" y="{y_pos}" class="period" text-anchor="end">{period}</text>')
            y_pos += 15

            # Job title
            titles = company_data.get('titles', {})
            title = titles.get('default', '')
            if title:
                svg_parts.append(f'  <text x="{left_x}" y="{y_pos}" class="job-title">{self._escape_xml(title)}</text>')
                y_pos += 14

            # Bullets (max 2, prioritize quality over quantity)
            bullets = company_data.get('verified_bullets', [])
            bullet_count = 2  # Limit to 2 bullets per company for better spacing
            for bullet in bullets[:bullet_count]:
                if isinstance(bullet, dict):
                    content = bullet.get('content', '')
                    # Wrap long text
                    wrapped_lines = self._wrap_text(content, 68)  # Slightly shorter lines
                    for i, line in enumerate(wrapped_lines):
                        if i == 0:
                            # First line with bullet
                            svg_parts.append(f'  <text x="{left_x + 5}" y="{y_pos}" class="bullet">• {self._escape_xml(line)}</text>')
                        else:
                            # Continuation lines without bullet, indented
                            svg_parts.append(f'  <text x="{left_x + 15}" y="{y_pos}" class="bullet">{self._escape_xml(line)}</text>')
                        y_pos += 14  # Increased line spacing

                    y_pos += 5  # Extra space after each bullet

            y_pos += 22  # Increased space between companies

        # Right column (skills, certifications, education) - 35% width
        right_x = 540
        right_width = 220
        right_y = 95

        svg_parts.append('')
        svg_parts.append('  <!-- Right Column: Skills & Education -->')

        # Certification box
        cert_data = self.data.get('certifications', [])
        if cert_data:
            cert = cert_data[0]
            cert_name = cert.get('name', '')
            cert_date = cert.get('date', '')

            svg_parts.append(f'  <rect x="{right_x}" y="{right_y - 12}" width="{right_width}" height="42" class="cert-box" rx="3"/>')
            svg_parts.append(f'  <text x="{right_x + 10}" y="{right_y + 2}" class="cert-text">CERTIFIED</text>')
            svg_parts.append(f'  <text x="{right_x + 10}" y="{right_y + 16}" class="skill-item">{self._wrap_text(cert_name, 28)[0]}</text>')
            if len(self._wrap_text(cert_name, 28)) > 1:
                svg_parts.append(f'  <text x="{right_x + 10}" y="{right_y + 26}" class="skill-item">{self._wrap_text(cert_name, 28)[1]}</text>')
            right_y += 50  # Increased spacing

        # Skills section
        svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="section-title">Skills</text>')
        svg_parts.append(f'  <line x1="{right_x}" y1="{right_y + 3}" x2="{right_x + 60}" y2="{right_y + 3}" stroke="#2c5aa0" stroke-width="2"/>')
        right_y += 15

        skill_tiers = self.data.get('skill_tiers', {}).get('verified', {})

        # Key skill categories for resume
        skill_display = [
            ('Languages & Core', skill_tiers.get('languages', [])),
            ('Data Engineering', skill_tiers.get('data_engineering', [])[:6]),
            ('ML/AI Frameworks', skill_tiers.get('ml', [])[:6]),
            ('Cloud & DevOps', skill_tiers.get('cloud', [])),
            ('Databases', skill_tiers.get('databases', [])),
        ]

        for category, skills in skill_display:
            if not skills:
                continue
            svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="skill-category">{self._escape_xml(category)}</text>')
            right_y += 12  # Increased from 11

            # Display skills as comma-separated
            skills_text = ', '.join(skills[:8])  # Max 8 skills per category
            wrapped = self._wrap_text(skills_text, 28)
            for line in wrapped[:2]:  # Max 2 lines per category
                svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="skill-item">{self._escape_xml(line)}</text>')
                right_y += 11  # Increased from 10
            right_y += 6  # Increased from 5

        # Education section
        right_y += 10
        svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="section-title">Education</text>')
        svg_parts.append(f'  <line x1="{right_x}" y1="{right_y + 3}" x2="{right_x + 80}" y2="{right_y + 3}" stroke="#2c5aa0" stroke-width="2"/>')
        right_y += 15

        education = self.data.get('education', {})

        # VU Amsterdam
        vu = education.get('vu_amsterdam', {})
        if vu:
            svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="company-name">VU Amsterdam</text>')
            right_y += 13  # Increased from 12
            svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="skill-item">{vu.get("degree", "")}</text>')
            right_y += 11  # Increased from 10
            svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="period">{vu.get("period", "")} • GPA: {vu.get("gpa", "")}</text>')
            right_y += 20  # Increased from 15

        # Tsinghua
        tsinghua = education.get('tsinghua', {})
        if tsinghua:
            svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="company-name">Tsinghua University</text>')
            right_y += 13  # Increased from 12
            svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="skill-item">{tsinghua.get("degree", "")}</text>')
            right_y += 11  # Increased from 10
            svg_parts.append(f'  <text x="{right_x}" y="{right_y}" class="period">{tsinghua.get("period", "")}</text>')

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        # Order matters: & must be escaped first!
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))

    def _wrap_text(self, text: str, max_length: int) -> List[str]:
        """Wrap text to multiple lines"""
        if len(text) <= max_length:
            return [text]

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + (1 if current_line else 0)
            if current_length + word_length <= max_length:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def apply_fixes(self, svg_content: str, fixes: List[Dict]) -> str:
        """Apply fixes to SVG content"""
        modified = svg_content

        for fix in fixes:
            action = fix.get('suggested_fix', {}).get('action')

            if action == 'adjust_position':
                details = fix['suggested_fix'].get('details', '')
                # Simple regex-based position adjustment
                if 'y=100' in details and 'y=120' in details:
                    modified = modified.replace('y="100"', 'y="120"')

        return modified


class VisualQualityChecker:
    """Check visual quality using Claude Vision API"""

    # Vision prompt v2.0 from design doc
    VISION_PROMPT = """你是一个专业的简历设计质检员，专门审查技术岗位简历的视觉质量。

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

    def __init__(self):
        # Load API config
        import os
        from dotenv import load_dotenv

        load_dotenv()

        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')

    def render_screenshot(self, svg_path: Path) -> Path:
        """Render SVG to PNG screenshot"""
        from playwright.sync_api import sync_playwright

        screenshot_path = svg_path.parent / "preview.png"

        # Create HTML wrapper to avoid font loading issues
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ margin: 0; padding: 0; }}
        svg {{ font-family: Arial, sans-serif; }}
    </style>
</head>
<body>
{svg_path.read_text(encoding='utf-8')}
</body>
</html>"""

        html_path = svg_path.parent / "preview.html"
        html_path.write_text(html_content, encoding='utf-8')

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 800, 'height': 1100})

            # Load HTML wrapper instead of raw SVG
            page.goto(f'file:///{html_path.as_posix()}')

            # Wait for rendering
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(500)

            # Take screenshot
            page.screenshot(
                path=str(screenshot_path),
                full_page=True
            )

            browser.close()

        return screenshot_path

    def analyze_with_vision(self, image_path: Path) -> Dict[str, Any]:
        """Analyze image with Claude Vision API"""
        import anthropic
        import base64

        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # Determine media type
        media_type = "image/png" if image_path.suffix == '.png' else "image/jpeg"

        # Create client
        client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Call Vision API
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": self.VISION_PROMPT
                            }
                        ]
                    }
                ]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON from response
            feedback = self._extract_json(response_text)

            return feedback

        except Exception as e:
            print(f"Vision API error: {e}")
            # Return fallback feedback
            return {
                'status': 'NEEDS_FIX',
                'overall_quality_score': 5,
                'issues': [],
                'error': str(e)
            }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Claude's response"""
        # Try to find JSON block
        import re

        # Look for JSON in code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback
                return {
                    'status': 'NEEDS_FIX',
                    'overall_quality_score': 5,
                    'issues': []
                }

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                'status': 'NEEDS_FIX',
                'overall_quality_score': 5,
                'issues': []
            }

    def parse_feedback(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Vision API response"""
        # Minimal implementation - just return as-is
        return response


class SVGFixer:
    """Apply automated fixes to SVG"""

    def apply_fixes(self, svg_content: str, issues: List[Dict]) -> str:
        """Apply P0 and P1 fixes only"""
        modified = svg_content

        # Filter to P0 and P1 only
        priority_issues = [
            issue for issue in issues
            if issue.get('priority') in ['P0', 'P1']
        ]

        for issue in priority_issues:
            action = issue.get('suggested_fix', {}).get('action')

            if action == 'increase_spacing':
                modified = self._increase_spacing(modified, issue)
            elif action == 'adjust_position':
                modified = self._adjust_position(modified, issue)
            elif action == 'reduce_font_size':
                modified = self._reduce_font_size(modified, issue)

        return modified

    def _increase_spacing(self, svg: str, issue: Dict) -> str:
        """Increase spacing by adjusting y coordinates"""
        # Minimal implementation - modify first y coordinate found
        match = re.search(r'y="(\d+)"', svg)
        if match:
            old_y = match.group(1)
            new_y = str(int(old_y) + 10)
            svg = svg.replace(f'y="{old_y}"', f'y="{new_y}"', 1)

        return svg

    def _adjust_position(self, svg: str, issue: Dict) -> str:
        """Adjust element position"""
        details = issue.get('suggested_fix', {}).get('details', '')

        # Parse details like "Move y=100 to y=120"
        match = re.search(r'y=(\d+).*y=(\d+)', details)
        if match:
            old_y = match.group(1)
            new_y = match.group(2)
            svg = svg.replace(f'y="{old_y}"', f'y="{new_y}"')

        return svg

    def _reduce_font_size(self, svg: str, issue: Dict) -> str:
        """Reduce font-size"""
        details = issue.get('suggested_fix', {}).get('details', '')

        # Parse details like "Reduce font-size from 14 to 12"
        match = re.search(r'from (\d+) to (\d+)', details)
        if match:
            old_size = match.group(1)
            new_size = match.group(2)
            svg = svg.replace(f'font-size="{old_size}"', f'font-size="{new_size}"')

        return svg


class IterationController:
    """Control optimization iteration loop"""

    def __init__(self, output_dir: Optional[str] = None, max_iterations: int = 10):
        self.output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "iterations"
        self.max_iterations = max_iterations

    def save_iteration(
        self,
        iteration: int,
        svg_path: Path,
        screenshot_path: Path,
        feedback: Dict[str, Any]
    ):
        """Save iteration artifacts"""
        iteration_dir = self.output_dir / f"iteration_{iteration}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        # Copy files to iteration directory (skip if already there)
        import shutil

        target_svg = iteration_dir / "resume.svg"
        target_png = iteration_dir / "preview.png"
        target_json = iteration_dir / "feedback.json"

        if svg_path != target_svg:
            shutil.copy(svg_path, target_svg)
        if screenshot_path != target_png:
            shutil.copy(screenshot_path, target_png)

        with open(target_json, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, indent=2, ensure_ascii=False)

    def is_approved(self, feedback: Dict[str, Any]) -> bool:
        """Check if feedback meets approval criteria"""
        return feedback.get('status') == 'APPROVED'

    def run_optimization_loop(self) -> Path:
        """Run optimization loop"""
        generator = SVGResumeGenerator(output_dir=str(self.output_dir))
        checker = VisualQualityChecker()
        fixer = SVGFixer()

        print(f"\n{'='*60}")
        print("SVG Resume Auto-Optimizer")
        print(f"{'='*60}\n")

        best_score = 0
        best_svg_path = None
        plateau_count = 0

        for i in range(self.max_iterations):
            print(f"=== Iteration {i} ===")

            # 1. Generate SVG
            svg_path = generator.generate_svg(iteration=i)
            print(f"  Generated: {svg_path}")

            # 2. Render screenshot
            try:
                screenshot_path = checker.render_screenshot(svg_path)
                print(f"  Screenshot: {screenshot_path}")
            except Exception as e:
                print(f"  Screenshot failed: {e}")
                continue

            # 3. Analyze with Vision API
            try:
                feedback = checker.analyze_with_vision(screenshot_path)
                print(f"  Quality score: {feedback.get('overall_quality_score', 0)}/10")
                print(f"  Issues found: {len(feedback.get('issues', []))}")
            except Exception as e:
                print(f"  Vision analysis failed: {e}")
                continue

            # 4. Save iteration
            self.save_iteration(i, svg_path, screenshot_path, feedback)

            # 5. Check approval
            if self.is_approved(feedback):
                print(f"\n[APPROVED] at iteration {i}!")
                print(f"  Quality score: {feedback.get('overall_quality_score')}/10")
                return self._finalize(svg_path)

            # 6. Check for plateau
            current_score = feedback.get('overall_quality_score', 0)
            if current_score <= best_score:
                plateau_count += 1
                if plateau_count >= 3:
                    print(f"\n[WARNING] Score plateaued for 3 iterations. Stopping.")
                    return self._finalize_best_attempt(best_svg_path or svg_path)
            else:
                plateau_count = 0
                best_score = current_score
                best_svg_path = svg_path

            # 7. Apply fixes
            issues = feedback.get('issues', [])
            if issues:
                print(f"  Applying {len([i for i in issues if i.get('priority') in ['P0', 'P1']])} P0/P1 fixes...")

                svg_content = svg_path.read_text(encoding='utf-8')
                fixed_svg = fixer.apply_fixes(svg_content, issues)

                # Update generator's template for next iteration
                generator._current_svg = fixed_svg

            print()

        # Max iterations reached
        print(f"\n[WARNING] Max iterations ({self.max_iterations}) reached.")
        return self._finalize_best_attempt(best_svg_path or svg_path)

    def _finalize(self, svg_path: Path) -> Path:
        """Finalize approved resume"""
        output_dir = PROJECT_ROOT / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        final_svg = output_dir / "Fei_Huang_Resume_Final.svg"
        final_pdf = output_dir / "Fei_Huang_Resume_Final.pdf"

        # Copy SVG
        import shutil
        shutil.copy(svg_path, final_svg)

        # Convert to PDF using Playwright
        self._svg_to_pdf(final_svg, final_pdf)

        print(f"\n[OK] Final resume saved:")
        print(f"  SVG: {final_svg}")
        print(f"  PDF: {final_pdf}")

        return final_pdf

    def _finalize_best_attempt(self, svg_path: Path) -> Path:
        """Finalize best attempt even if not approved"""
        print(f"  Using best attempt from: {svg_path}")
        return self._finalize(svg_path)

    def _svg_to_pdf(self, svg_path: Path, pdf_path: Path):
        """Convert SVG to PDF"""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 800, 'height': 1100})

            page.goto(f'file:///{svg_path.as_posix()}')
            page.wait_for_timeout(500)

            page.pdf(
                path=str(pdf_path),
                format='A4',
                print_background=True
            )

            browser.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='SVG Resume Auto-Optimizer')
    parser.add_argument('--max-iterations', type=int, default=10,
                        help='Maximum optimization iterations (default: 10)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for iterations')

    args = parser.parse_args()

    controller = IterationController(
        output_dir=args.output_dir,
        max_iterations=args.max_iterations
    )

    try:
        final_path = controller.run_optimization_loop()
        print(f"\n{'='*60}")
        print("[OK] Optimization complete!")
        print(f"{'='*60}")
        return 0
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] by user")
        return 1
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
