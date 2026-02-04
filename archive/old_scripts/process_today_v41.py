#!/usr/bin/env python3
"""
使用 v4.1 配置驱动版本重新处理今日职位
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入 v4.1 生成器
from resume_generator_v41 import ConfigDrivenGenerator, ResumeConfig, JobDescription

# 项目路径
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_today_scrape():
    """加载今天抓取的数据"""
    today = datetime.now().strftime("%Y%m%d")
    all_jobs = []
    
    for file in DATA_DIR.glob(f"*_{today}_*.json"):
        if file.name.startswith(("linkedin_", "iamexpat_", "indeed_")):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    jobs = data.get('jobs', [])
                    print(f"[LOAD] {file.name}: {len(jobs)} jobs")
                    all_jobs.extend(jobs)
            except Exception as e:
                print(f"[ERROR] Failed to load {file}: {e}")
    
    return all_jobs


def detect_role(title: str) -> str:
    """根据职位标题检测目标角色"""
    title_lower = title.lower()
    
    if any(k in title_lower for k in ['machine learning', 'ml engineer', 'ai engineer']):
        return 'ml_engineer'
    elif 'data engineer' in title_lower:
        return 'data_engineer'
    elif 'data scientist' in title_lower:
        return 'data_scientist'
    elif any(k in title_lower for k in ['quant', 'quantitative']):
        return 'quant'
    elif 'data analyst' in title_lower:
        return 'data_analyst'
    else:
        return 'data_engineer'  # 默认


async def process_jobs():
    """处理职位并生成简历"""
    print("="*70)
    print("[V4.1] Processing today's jobs with Config-Driven Generator")
    print("="*70)
    
    # 加载今日抓取
    jobs = load_today_scrape()
    print(f"\n[TOTAL] {len(jobs)} jobs to process\n")
    
    if not jobs:
        print("[EXIT] No jobs found")
        return
    
    # 初始化 v4.1 生成器 (使用 Jinja2 模板)
    generator = ConfigDrivenGenerator(
        template_path="templates/resume_toni_v4.html",
        library_path="assets/bullet_library_simple.yaml",
        config_path="config/resume_generation.yaml"
    )
    
    generated = []
    
    for job_data in jobs:
        title = job_data.get('title', '')
        company = job_data.get('company', '')
        description = job_data.get('description', '')
        
        print(f"[PROCESS] {title} @ {company}")
        
        # 检测角色
        role = detect_role(title)
        print(f"  [ROLE] {role}")
        
        # 创建职位描述
        job_desc = JobDescription(
            title=title,
            company=company,
            description=description
        )
        
        # 创建配置
        config = ResumeConfig(
            target_role=role,
            company=company,
            job_description=job_desc,
            max_bullets_per_exp=3,
            include_projects=True,
            include_career_note=True
        )
        
        try:
            # 生成简历
            html = generator.generate(config)
            
            # 保存 HTML - 清理特殊字符
            import re
            safe_title = re.sub(r'[^\w\-]', '_', title)[:30]
            safe_company = re.sub(r'[^\w\-]', '_', company)[:20]
            html_path = OUTPUT_DIR / f"Fei_Huang_{safe_title}_{safe_company}.html"
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # 生成 PDF
            pdf_path = await generator.to_pdf(html_path)
            
            print(f"  [OK] {pdf_path.name}\n")
            generated.append({
                'title': title,
                'company': company,
                'role': role,
                'pdf': str(pdf_path)
            })
            
        except Exception as e:
            print(f"  [ERROR] {e}\n")
    
    # 汇总
    print("="*70)
    print(f"[SUMMARY] Generated {len(generated)} resumes")
    print("="*70)
    for g in generated:
        print(f"  [{g['role']}] {g['title']} @ {g['company']}")


if __name__ == '__main__':
    asyncio.run(process_jobs())
