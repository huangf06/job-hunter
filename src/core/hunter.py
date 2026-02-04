"""
Job Hunter - 主控模块
=====================

整合所有模块，提供统一的求职流程控制
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.loader import ConfigLoader, Config
from src.modules.filter.engine import FilterEngine, FilterResult
from src.modules.scorer.engine import HybridScorer, ScoreResult
from src.modules.resume.generator import ResumeGenerator
from src.core.experiment import ExperimentManager


@dataclass
class ProcessingResult:
    """处理结果"""
    job_id: str
    title: str
    company: str
    url: str
    status: str
    
    # 筛选阶段
    filter_passed: bool = False
    filter_reason: Optional[str] = None
    
    # 评分阶段
    score: Optional[float] = None
    score_breakdown: Optional[Dict] = None
    ai_analysis: Optional[str] = None
    
    # 实验信息
    experiment_id: Optional[str] = None
    variant_id: Optional[str] = None
    
    # 简历生成
    resume_generated: bool = False
    resume_path: Optional[str] = None
    
    # 元数据
    processed_at: str = None
    processing_time_ms: int = 0
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now().isoformat()


class JobHunter:
    """求职主控"""
    
    def __init__(self, config: Config = None, config_path: str = "config"):
        """
        初始化
        
        Args:
            config: 配置对象（如果提供则直接使用）
            config_path: 配置目录路径（如果config未提供）
        """
        # 加载配置
        if config is None:
            loader = ConfigLoader(config_path)
            config = loader.load()
        
        self.config = config
        
        # 初始化各模块
        self.filter_engine = FilterEngine(config.filters)
        self.scorer = HybridScorer(config.scoring)
        self.resume_generator = ResumeGenerator(config.resume)
        
        # 实验管理
        self.experiment_manager = ExperimentManager()
        self.active_experiment = self.experiment_manager.active_experiment
        
        # 数据存储
        self.data_dir = Path("data")
        self.output_dir = Path("output")
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # 加载已有记录
        self.processed_ids = self._load_processed_ids()
    
    def _load_processed_ids(self) -> set:
        """加载已处理的职位ID"""
        tracker_file = self.data_dir / "applications.json"
        if not tracker_file.exists():
            return set()
        
        try:
            with open(tracker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return set(a.get('job_id') for a in data.get('applications', []))
        except:
            return set()
    
    def _generate_job_id(self, job: Dict) -> str:
        """生成职位唯一ID"""
        import hashlib
        key = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('url', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    async def process_job(self, job: Dict, ai_scorer_func: Callable = None) -> ProcessingResult:
        """
        处理单个职位
        
        Args:
            job: 职位信息
            ai_scorer_func: AI评分函数（可选）
        
        Returns:
            ProcessingResult
        """
        import time
        start_time = time.time()
        
        job_id = self._generate_job_id(job)
        
        # 检查是否已处理
        if job_id in self.processed_ids:
            return ProcessingResult(
                job_id=job_id,
                title=job.get('title', ''),
                company=job.get('company', ''),
                url=job.get('url', ''),
                status="skipped",
                filter_reason="already_processed"
            )
        
        result = ProcessingResult(
            job_id=job_id,
            title=job.get('title', ''),
            company=job.get('company', ''),
            url=job.get('url', ''),
            status="pending"
        )
        
        try:
            # ========== 1. 硬性筛选 ==========
            filter_result = self.filter_engine.check(job)
            result.filter_passed = filter_result.passed
            result.filter_reason = filter_result.reason
            
            if not filter_result.passed:
                result.status = "rejected"
                self._save_result(result)
                return result
            
            # ========== 2. 软性评分（加分）==========
            soft_score = self.filter_engine.score(job)
            
            # ========== 3. 实验分组 ==========
            variant_id = None
            variant_config = None
            if self.active_experiment:
                variant_id, variant_config = self.experiment_manager.assign_job(job_id)
                result.experiment_id = self.active_experiment.id
                result.variant_id = variant_id
            
            # ========== 4. 评分 ==========
            if ai_scorer_func:
                # 使用外部AI评分
                score_result = await self.scorer.hybrid_score(job, ai_scorer_func)
            else:
                # 仅规则评分
                score_result = self.scorer.rule_score(job)
            
            # 加上软性评分
            final_score = score_result.score + soft_score
            result.score = round(final_score, 2)
            result.score_breakdown = score_result.breakdown
            result.ai_analysis = score_result.analysis
            
            # 检查阈值
            threshold = self.config.scoring.get('thresholds', {}).get('generate_resume', 6.0)
            if final_score < threshold:
                result.status = "low_score"
                self._save_result(result)
                return result
            
            # ========== 5. 生成简历 ==========
            html = self.resume_generator.generate(job, variant_config)
            html_path = self.resume_generator.save(html, job, str(self.output_dir))
            
            # 生成PDF
            pdf_path = await self.resume_generator.to_pdf(html_path)
            
            result.resume_generated = True
            result.resume_path = str(pdf_path)
            result.status = "generated"
            
            # 记录实验事件
            if self.active_experiment:
                self.experiment_manager.record_event(job_id, "resume_generated")
            
            self._save_result(result)
            
        except Exception as e:
            result.status = "error"
            result.filter_reason = str(e)
            self._save_result(result)
        
        finally:
            result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    async def process_jobs(self, jobs: List[Dict], ai_scorer_func: Callable = None) -> List[ProcessingResult]:
        """
        批量处理职位
        
        Args:
            jobs: 职位列表
            ai_scorer_func: AI评分函数（可选）
        
        Returns:
            处理结果列表
        """
        results = []
        
        print(f"\n{'='*70}")
        print(f"Processing {len(jobs)} jobs...")
        if self.active_experiment:
            print(f"Active experiment: {self.active_experiment.name}")
        print(f"{'='*70}\n")
        
        for i, job in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {job.get('company', 'Unknown')[:30]:30s} - {job.get('title', 'Unknown')[:40]}...")
            
            result = await self.process_job(job, ai_scorer_func)
            results.append(result)
            
            # 打印结果
            if result.status == "rejected":
                print(f"  [REJECTED] {result.filter_reason}")
            elif result.status == "low_score":
                print(f"  [LOW SCORE] {result.score} < threshold")
            elif result.status == "generated":
                print(f"  [GENERATED] Score {result.score} - {Path(result.resume_path).name}")
            elif result.status == "skipped":
                print(f"  [SKIPPED] Already processed")
            elif result.status == "error":
                print(f"  [ERROR] {result.filter_reason}")
        
        self._print_summary(results)
        return results
    
    def _save_result(self, result: ProcessingResult):
        """保存处理结果"""
        tracker_file = self.data_dir / "applications.json"
        
        # 加载现有数据
        if tracker_file.exists():
            with open(tracker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"applications": [], "stats": {}}
        
        # 检查是否已存在
        existing = [a for a in data["applications"] if a.get('job_id') == result.job_id]
        if existing:
            # 更新
            for i, app in enumerate(data["applications"]):
                if app.get('job_id') == result.job_id:
                    data["applications"][i] = asdict(result)
                    break
        else:
            # 添加新记录
            data["applications"].append(asdict(result))
        
        # 保存
        with open(tracker_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 更新已处理ID集合
        self.processed_ids.add(result.job_id)
    
    def _print_summary(self, results: List[ProcessingResult]):
        """打印汇总"""
        total = len(results)
        generated = sum(1 for r in results if r.status == "generated")
        rejected = sum(1 for r in results if r.status == "rejected")
        low_score = sum(1 for r in results if r.status == "low_score")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")
        
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total:     {total}")
        print(f"Generated: {generated}")
        print(f"Rejected:  {rejected}")
        print(f"Low score: {low_score}")
        print(f"Skipped:   {skipped}")
        print(f"Errors:    {errors}")
        print(f"{'='*70}\n")
        
        if generated > 0:
            print(f"Generated {generated} resumes in: {self.output_dir}")
            print(f"Results saved to: {self.data_dir / 'applications.json'}")
            print(f"\nNext: Review PDFs and apply manually\n")


# ============== CLI入口 ==============

def load_jobs_from_json(filepath: str) -> List[Dict]:
    """从JSON文件加载职位"""
    path = Path(filepath)
    if not path.exists():
        # 尝试在data目录查找
        path = Path("data/leads") / filepath
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('jobs', [])


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Hunter')
    parser.add_argument('--config', default='config', help='Config directory')
    parser.add_argument('--experiment', help='Experiment to run')
    parser.add_argument('--jobs', help='Jobs JSON file to process')
    parser.add_argument('--env', help='Environment (development/production)')
    
    args = parser.parse_args()
    
    # 加载配置
    loader = ConfigLoader(args.config)
    config = loader.load(environment=args.env, experiment=args.experiment)
    
    # 初始化
    hunter = JobHunter(config)
    
    if args.jobs:
        # 处理指定文件
        jobs = load_jobs_from_json(args.jobs)
        await hunter.process_jobs(jobs)
    else:
        print("Usage:")
        print("  python -m src.core.hunter --jobs data/leads/linkedin_jobs_xxx.json")
        print("  python -m src.core.hunter --experiment exp_001 --jobs ...")


if __name__ == "__main__":
    asyncio.run(main())
