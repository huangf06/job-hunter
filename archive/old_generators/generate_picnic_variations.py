#!/usr/bin/env python3
"""
批量生成 Picnic 简历 - 多版本对比
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from resume_generator_v41 import ConfigDrivenGenerator, ResumeConfig, JobDescription


async def generate_variations():
    """生成多个版本的 Picnic 简历"""
    
    generator = ConfigDrivenGenerator()
    
    # Picnic JD 的不同侧重点
    variations = [
        {
            "name": "v1_data_engineer_focus",
            "role": "data_engineer",
            "jd": "Python, PySpark, Databricks, SQL, AWS, data pipelines, ETL, Delta Lake",
            "desc": "Standard Data Engineer - Focus on data engineering"
        },
        {
            "name": "v2_ml_engineer_focus", 
            "role": "ml_engineer",
            "jd": "Python, machine learning, PyTorch, model deployment, MLOps, feature engineering",
            "desc": "ML Engineer - Focus on machine learning"
        },
        {
            "name": "v3_data_scientist_focus",
            "role": "data_scientist", 
            "jd": "Python, statistics, A/B testing, data analysis, insights, experimentation",
            "desc": "Data Scientist - Focus on analytics & insights"
        },
        {
            "name": "v4_quant_focus",
            "role": "quant",
            "jd": "Python, quantitative analysis, backtesting, statistical modeling, risk management",
            "desc": "Quant - Focus on quantitative analysis"
        },
        {
            "name": "v5_data_analyst_focus",
            "role": "data_analyst",
            "jd": "SQL, Python, data visualization, Tableau, business intelligence, reporting",
            "desc": "Data Analyst - Focus on visualization"
        },
        {
            "name": "v6_fullstack_data",
            "role": "data_engineer",
            "jd": "Python, PySpark, Databricks, SQL, AWS, machine learning, statistics, A/B testing, data pipelines",
            "desc": "Full-stack Data - Comprehensive skills"
        },
    ]
    
    print("=" * 70)
    print("Batch Generating Picnic Resumes - Multiple Versions")
    print("=" * 70)
    
    generated = []
    
    for i, var in enumerate(variations, 1):
        print(f"\n[{i}/{len(variations)}] Generating: {var['name']}")
        print(f"    Role: {var['role']}")
        print(f"    Desc: {var['desc']}")
        print(f"    JD: {var['jd'][:60]}...")
        
        job = JobDescription(
            title=var['role'].replace('_', ' ').title(),
            company="Picnic",
            description=var['jd']
        )
        
        config = ResumeConfig(
            target_role=var['role'],
            company="Picnic",
            job_description=job,
            max_bullets_per_exp=3,
        )
        
        try:
            html = generator.generate(config)
            html_path = generator.save(html, "Picnic", var['name'], 'output/picnic_variations')
            pdf_path = await generator.to_pdf(html_path)
            
            generated.append({
                'name': var['name'],
                'role': var['role'],
                'desc': var['desc'],
                'pdf': pdf_path
            })
            print(f"    [OK] Generated: {pdf_path.name}")
        except Exception as e:
            print(f"    [ERROR] {e}")
    
    # 打印总结
    print("\n" + "=" * 70)
    print("Generation Complete! All versions:")
    print("=" * 70)
    
    for i, g in enumerate(generated, 1):
        print(f"\n{i}. {g['name']}")
        print(f"   Role: {g['role']}")
        print(f"   Desc: {g['desc']}")
        print(f"   File: {g['pdf']}")
    
    print("\n" + "=" * 70)
    print("Check output/picnic_variations/ for PDF files")
    print("Pick the best one!")
    print("=" * 70)
    
    return generated


if __name__ == '__main__':
    asyncio.run(generate_variations())
