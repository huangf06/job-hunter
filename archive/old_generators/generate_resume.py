#!/usr/bin/env python3
"""
简历生成器 CLI - 快速生成 Toni 风格简历

用法:
    python generate_resume.py --role data_engineer --company "Picnic" --jd "job_description.txt"
    python generate_resume.py --role quant --company "Optiver" --title "Quantitative Researcher"
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from resume_generator_v41 import ConfigDrivenGenerator, ResumeConfig, JobDescription


def main():
    parser = argparse.ArgumentParser(
        description='Generate Toni-style resume tailored for specific job',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Data Engineer role
    python generate_resume.py --role data_engineer --company "Picnic" \\
        --jd "Python, PySpark, Databricks, SQL, AWS"
    
    # ML Engineer role  
    python generate_resume.py --role ml_engineer --company "Booking.com" \\
        --jd "machine learning, PyTorch, model deployment"
    
    # Quant role
    python generate_resume.py --role quant --company "Optiver" \\
        --jd "quantitative trading, alpha research, backtesting"
    
    # Data Scientist role
    python generate_resume.py --role data_scientist --company "Adyen" \\
        --jd "statistics, A/B testing, Python, SQL"
        """
    )
    
    parser.add_argument('--role', '-r', required=True,
                       choices=['data_engineer', 'ml_engineer', 'data_scientist', 'quant', 'data_analyst'],
                       help='Target role type')
    
    parser.add_argument('--company', '-c', required=True,
                       help='Company name')
    
    parser.add_argument('--title', '-t', default=None,
                       help='Job title (optional, defaults to role)')
    
    parser.add_argument('--jd', '-j', required=True,
                       help='Job description or keywords (text or file path)')
    
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory (default: output)')
    
    parser.add_argument('--max-bullets', '-b', type=int, default=3,
                       help='Max bullets per experience (default: 3)')
    
    parser.add_argument('--no-projects', action='store_true',
                       help='Exclude projects section')
    
    parser.add_argument('--no-career-note', action='store_true',
                       help='Exclude career note')
    
    args = parser.parse_args()
    
    # 读取 JD
    jd_text = args.jd
    if Path(args.jd).exists():
        with open(args.jd, 'r', encoding='utf-8') as f:
            jd_text = f.read()
    
    # 创建职位描述
    job = JobDescription(
        title=args.title or args.role,
        company=args.company,
        description=jd_text
    )
    
    # 创建配置
    config = ResumeConfig(
        target_role=args.role,
        company=args.company,
        job_description=job,
        max_bullets_per_exp=args.max_bullets,
        include_projects=not args.no_projects,
        include_career_note=not args.no_career_note
    )
    
    # 生成简历
    print(f"[GENERATE] Resume for {args.role} at {args.company}...")
    
    generator = ConfigDrivenGenerator()
    html = generator.generate(config)
    
    # 保存 HTML
    safe_role = args.role.replace(' ', '_').lower()
    safe_company = args.company.replace(' ', '_').lower()[:20]
    
    html_path = generator.save(html, args.company, safe_role, args.output)
    
    # 生成 PDF
    print(f"[PDF] Converting to PDF...")
    pdf_path = asyncio.run(generator.to_pdf(html_path))
    
    print(f"\n[DONE] Resume generated successfully!")
    print(f"   HTML: {html_path}")
    print(f"   PDF:  {pdf_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
