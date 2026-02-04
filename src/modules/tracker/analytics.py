"""
数据分析模块 - 指标计算和可视化
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import statistics


class MetricsAnalyzer:
    """指标分析器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.results_dir = self.data_dir / "results"
        self.metrics_dir = self.data_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_funnel(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        计算漏斗指标
        
        Returns:
            {
                "discovery": {"count": N, "rate": 1.0},
                "filter_passed": {"count": N, "rate": 0.X},
                "scored_passed": {"count": N, "rate": 0.X},
                "resume_generated": {"count": N, "rate": 0.X},
                "applied": {"count": N, "rate": 0.X},
                "response_received": {"count": N, "rate": 0.X},
                "interview": {"count": N, "rate": 0.X},
                "offer": {"count": N, "rate": 0.X},
            }
        """
        results = self._load_results(start_date, end_date)
        
        if not results:
            return {}
        
        total = len(results)
        
        funnel = {
            "discovery": {"count": total, "rate": 1.0},
            "filter_passed": {"count": 0, "rate": 0.0},
            "scored_passed": {"count": 0, "rate": 0.0},
            "resume_generated": {"count": 0, "rate": 0.0},
            "applied": {"count": 0, "rate": 0.0},
            "response_received": {"count": 0, "rate": 0.0},
            "interview": {"count": 0, "rate": 0.0},
            "offer": {"count": 0, "rate": 0.0},
        }
        
        for r in results:
            status = r.get('status')
            
            if status in ['scored', 'generated', 'applied']:
                funnel['filter_passed']['count'] += 1
            
            if status in ['generated', 'applied']:
                funnel['scored_passed']['count'] += 1
            
            if status in ['generated', 'applied']:
                funnel['resume_generated']['count'] += 1
            
            if status == 'applied':
                funnel['applied']['count'] += 1
            
            # 检查反馈状态
            if r.get('response_received'):
                funnel['response_received']['count'] += 1
                
                response_type = r.get('response_type', '')
                if 'interview' in response_type.lower():
                    funnel['interview']['count'] += 1
                if 'offer' in response_type.lower():
                    funnel['offer']['count'] += 1
        
        # 计算转化率
        for key in ['filter_passed', 'scored_passed', 'resume_generated', 'applied']:
            if total > 0:
                funnel[key]['rate'] = round(funnel[key]['count'] / total, 3)
        
        # 后续转化率基于applied
        applied_count = funnel['applied']['count']
        if applied_count > 0:
            for key in ['response_received', 'interview', 'offer']:
                funnel[key]['rate'] = round(funnel[key]['count'] / applied_count, 3)
        
        return funnel
    
    def calculate_efficiency_metrics(self, days: int = 7) -> Dict:
        """计算效率指标"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = self._load_results(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        if not results:
            return {}
        
        # 处理时间
        processing_times = [
            r.get('processing_duration_ms', 0) 
            for r in results 
            if r.get('processing_duration_ms')
        ]
        
        # Token消耗 (需要记录)
        token_usage = [
            r.get('token_usage', 0) 
            for r in results 
            if r.get('token_usage')
        ]
        
        return {
            "period_days": days,
            "total_jobs": len(results),
            "avg_processing_time_ms": statistics.mean(processing_times) if processing_times else 0,
            "median_processing_time_ms": statistics.median(processing_times) if processing_times else 0,
            "total_token_usage": sum(token_usage) if token_usage else 0,
            "avg_token_per_job": statistics.mean(token_usage) if token_usage else 0,
            "jobs_per_day": len(results) / days,
        }
    
    def analyze_by_dimension(self, dimension: str, start_date: str = None, end_date: str = None) -> Dict:
        """
        按维度分析
        
        Args:
            dimension: company | source | variant | score_range
        """
        results = self._load_results(start_date, end_date)
        
        if not results:
            return {}
        
        # 按维度分组
        groups = defaultdict(list)
        
        for r in results:
            if dimension == "score_range":
                score = r.get('score', 0)
                if score >= 8:
                    key = "8-10"
                elif score >= 6:
                    key = "6-8"
                elif score >= 4:
                    key = "4-6"
                else:
                    key = "0-4"
            else:
                key = r.get(dimension, 'unknown')
            
            groups[key].append(r)
        
        # 计算每个组的指标
        analysis = {}
        for key, group in groups.items():
            total = len(group)
            applied = sum(1 for r in group if r.get('status') == 'applied')
            responded = sum(1 for r in group if r.get('response_received'))
            
            analysis[key] = {
                "count": total,
                "application_rate": round(applied / total, 3) if total > 0 else 0,
                "response_rate": round(responded / applied, 3) if applied > 0 else 0,
                "avg_score": statistics.mean([r.get('score', 0) for r in group]) if group else 0,
            }
        
        return dict(sorted(analysis.items(), key=lambda x: x[1]['count'], reverse=True))
    
    def generate_daily_report(self, date: str = None) -> Dict:
        """生成每日报告"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 加载当天的数据
        start = f"{date}T00:00:00"
        end = f"{date}T23:59:59"
        
        results = self._load_results(start, end)
        
        if not results:
            return {"date": date, "message": "No data for this date"}
        
        # 统计
        report = {
            "date": date,
            "summary": {
                "total_discovered": len(results),
                "passed_filter": sum(1 for r in results if r.get('status') in ['scored', 'generated', 'applied']),
                "passed_scoring": sum(1 for r in results if r.get('status') in ['generated', 'applied']),
                "resumes_generated": sum(1 for r in results if r.get('status') in ['generated', 'applied']),
                "applications": sum(1 for r in results if r.get('status') == 'applied'),
            },
            "top_companies": self._get_top_companies(results),
            "score_distribution": self._get_score_distribution(results),
            "reject_reasons": self._get_reject_reasons(results),
        }
        
        return report
    
    def compare_variants(self, experiment_id: str) -> Dict:
        """比较实验变体表现"""
        results = self._load_results()
        
        # 筛选属于该实验的结果
        exp_results = [
            r for r in results 
            if r.get('experiment_id') == experiment_id
        ]
        
        if not exp_results:
            return {"error": f"No data for experiment {experiment_id}"}
        
        # 按变体分组
        variants = defaultdict(list)
        for r in exp_results:
            variant = r.get('variant_id', 'unknown')
            variants[variant].append(r)
        
        # 计算每个变体的指标
        comparison = {}
        for variant_id, group in variants.items():
            total = len(group)
            applied = sum(1 for r in group if r.get('status') == 'applied')
            responded = sum(1 for r in group if r.get('response_received'))
            
            comparison[variant_id] = {
                "sample_size": total,
                "application_rate": round(applied / total, 3) if total > 0 else 0,
                "response_rate": round(responded / applied, 3) if applied > 0 else 0,
                "avg_score": statistics.mean([r.get('score', 0) for r in group]) if group else 0,
            }
        
        return comparison
    
    def _load_results(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """加载处理结果"""
        tracker_file = self.data_dir / "applications.json"
        
        if not tracker_file.exists():
            return []
        
        with open(tracker_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = data.get('applications', [])
        
        # 时间过滤
        if start_date or end_date:
            filtered = []
            for r in results:
                processed_at = r.get('processed_at', '')
                if start_date and processed_at < start_date:
                    continue
                if end_date and processed_at > end_date:
                    continue
                filtered.append(r)
            results = filtered
        
        return results
    
    def _get_top_companies(self, results: List[Dict], n: int = 5) -> List[Dict]:
        """获取Top公司"""
        companies = defaultdict(lambda: {"count": 0, "generated": 0, "applied": 0})
        
        for r in results:
            company = r.get('company', 'Unknown')
            companies[company]['count'] += 1
            if r.get('status') in ['generated', 'applied']:
                companies[company]['generated'] += 1
            if r.get('status') == 'applied':
                companies[company]['applied'] += 1
        
        sorted_companies = sorted(
            companies.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )[:n]
        
        return [
            {"company": name, **stats}
            for name, stats in sorted_companies
        ]
    
    def _get_score_distribution(self, results: List[Dict]) -> Dict:
        """获取分数分布"""
        distribution = {"0-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
        
        for r in results:
            score = r.get('score', 0)
            if score >= 8:
                distribution["8-10"] += 1
            elif score >= 6:
                distribution["6-8"] += 1
            elif score >= 4:
                distribution["4-6"] += 1
            else:
                distribution["0-4"] += 1
        
        return distribution
    
    def _get_reject_reasons(self, results: List[Dict]) -> Dict:
        """获取拒绝原因统计"""
        reasons = defaultdict(int)
        
        for r in results:
            if r.get('status') == 'rejected':
                reason = r.get('reject_reason', 'unknown')
                reasons[reason] += 1
        
        return dict(sorted(reasons.items(), key=lambda x: x[1], reverse=True))
    
    def save_metrics(self, metrics: Dict, name: str):
        """保存指标到文件"""
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        filepath = self.metrics_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"Metrics saved to: {filepath}")


# ============== 报告生成器 ==============

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, analyzer: MetricsAnalyzer = None):
        self.analyzer = analyzer or MetricsAnalyzer()
    
    def generate_console_report(self, days: int = 7):
        """生成控制台报告"""
        print("\n" + "="*70)
        print("JOB HUNTER ANALYTICS REPORT")
        print("="*70)
        
        # 漏斗指标
        print("\n📊 FUNNEL METRICS")
        print("-"*70)
        funnel = self.analyzer.calculate_funnel()
        for stage, data in funnel.items():
            bar = "█" * int(data['rate'] * 50)
            print(f"  {stage:20s}: {data['count']:4d} ({data['rate']:.1%}) {bar}")
        
        # 效率指标
        print("\n⚡ EFFICIENCY METRICS (Last {} days)".format(days))
        print("-"*70)
        efficiency = self.analyzer.calculate_efficiency_metrics(days)
        for key, value in efficiency.items():
            print(f"  {key:25s}: {value}")
        
        # 公司分析
        print("\n🏢 TOP COMPANIES")
        print("-"*70)
        by_company = self.analyzer.analyze_by_dimension("company")
        for company, stats in list(by_company.items())[:5]:
            print(f"  {company:20s}: {stats['count']:3d} jobs, "
                  f"{stats['application_rate']:.1%} apply rate, "
                  f"{stats['response_rate']:.1%} response rate")
        
        # 分数分布
        print("\n📈 SCORE DISTRIBUTION")
        print("-"*70)
        by_score = self.analyzer.analyze_by_dimension("score_range")
        for range_name, stats in by_score.items():
            bar = "█" * int(stats['count'] / 5)
            print(f"  {range_name:10s}: {stats['count']:4d} {bar}")
        
        print("\n" + "="*70 + "\n")
    
    def generate_html_report(self, output_path: str = "report.html"):
        """生成HTML报告"""
        # TODO: 实现HTML报告生成
        pass


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 初始化分析器
    analyzer = MetricsAnalyzer()
    
    # 生成控制台报告
    reporter = ReportGenerator(analyzer)
    reporter.generate_console_report(days=7)
    
    # 计算漏斗
    # funnel = analyzer.calculate_funnel()
    # print(json.dumps(funnel, indent=2))
    
    # 按公司分析
    # by_company = analyzer.analyze_by_dimension("company")
    # print(json.dumps(by_company, indent=2))
    
    # 比较实验变体
    # comparison = analyzer.compare_variants("exp_001")
    # print(json.dumps(comparison, indent=2))
