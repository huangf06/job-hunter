"""
A/B测试框架 - 实验管理和分析
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import yaml


@dataclass
class Variant:
    """实验变体"""
    id: str
    name: str
    description: str
    weight: float
    config: Dict
    sample_size: int = 0
    metrics: Dict = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class Experiment:
    """实验定义"""
    id: str
    name: str
    description: str
    hypothesis: str
    status: str  # draft | running | paused | completed
    variants: List[Variant]
    metrics: Dict
    parameters: Dict
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def get_variant(self, variant_id: str) -> Optional[Variant]:
        """获取指定变体"""
        for v in self.variants:
            if v.id == variant_id:
                return v
        return None
    
    def assign_variant(self, job_id: str) -> Variant:
        """
        为职位分配变体
        
        使用hash-based分流，确保同一职位始终进入同一组
        """
        # 计算hash
        hash_value = int(hashlib.md5(f"{self.id}:{job_id}".encode()).hexdigest(), 16)
        
        # 根据权重分配
        total_weight = sum(v.weight for v in self.variants)
        normalized_hash = (hash_value % 10000) / 10000
        
        cumulative_weight = 0
        for variant in self.variants:
            cumulative_weight += variant.weight / total_weight
            if normalized_hash <= cumulative_weight:
                return variant
        
        # 默认返回最后一个
        return self.variants[-1]


class ExperimentManager:
    """实验管理器"""
    
    def __init__(self, experiments_dir: str = "config/experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.data_dir = Path("data/experiments")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.experiments: Dict[str, Experiment] = {}
        self.active_experiment: Optional[Experiment] = None
        
        self._load_experiments()
    
    def _load_experiments(self):
        """加载所有实验配置"""
        if not self.experiments_dir.exists():
            return
        
        for exp_file in self.experiments_dir.glob("*.yaml"):
            try:
                with open(exp_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'experiment' in data:
                        exp_data = data['experiment']
                        experiment = self._parse_experiment(exp_data)
                        self.experiments[experiment.id] = experiment
                        
                        # 如果有正在运行的实验，设为active
                        if experiment.status == "running":
                            self.active_experiment = experiment
            except Exception as e:
                print(f"Warning: Failed to load experiment {exp_file}: {e}")
    
    def _parse_experiment(self, data: Dict) -> Experiment:
        """解析实验配置"""
        variants = []
        for v_data in data.get('variants', []):
            variants.append(Variant(
                id=v_data['id'],
                name=v_data['name'],
                description=v_data.get('description', ''),
                weight=v_data['weight'],
                config=v_data.get('config', {}),
                sample_size=v_data.get('sample_size', 0),
                metrics=v_data.get('metrics', {})
            ))
        
        return Experiment(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            hypothesis=data.get('hypothesis', ''),
            status=data.get('status', 'draft'),
            variants=variants,
            metrics=data.get('metrics', {}),
            parameters=data.get('parameters', {}),
            created_at=data.get('created_at', datetime.now().isoformat()),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at')
        )
    
    def start_experiment(self, experiment_id: str) -> bool:
        """启动实验"""
        if experiment_id not in self.experiments:
            print(f"Error: Experiment {experiment_id} not found")
            return False
        
        exp = self.experiments[experiment_id]
        
        if exp.status == "running":
            print(f"Experiment {experiment_id} is already running")
            return True
        
        if exp.status == "completed":
            print(f"Error: Experiment {experiment_id} is already completed")
            return False
        
        # 停止当前运行的实验
        if self.active_experiment:
            self.pause_experiment(self.active_experiment.id)
        
        # 启动新实验
        exp.status = "running"
        exp.started_at = datetime.now().isoformat()
        self.active_experiment = exp
        
        self._save_experiment_config(exp)
        print(f"Started experiment: {exp.name} ({exp.id})")
        return True
    
    def pause_experiment(self, experiment_id: str) -> bool:
        """暂停实验"""
        if experiment_id not in self.experiments:
            return False
        
        exp = self.experiments[experiment_id]
        exp.status = "paused"
        
        if self.active_experiment and self.active_experiment.id == experiment_id:
            self.active_experiment = None
        
        self._save_experiment_config(exp)
        print(f"Paused experiment: {exp.name}")
        return True
    
    def complete_experiment(self, experiment_id: str) -> bool:
        """完成实验"""
        if experiment_id not in self.experiments:
            return False
        
        exp = self.experiments[experiment_id]
        exp.status = "completed"
        exp.completed_at = datetime.now().isoformat()
        
        if self.active_experiment and self.active_experiment.id == experiment_id:
            self.active_experiment = None
        
        self._save_experiment_config(exp)
        
        # 生成最终报告
        self._generate_final_report(exp)
        
        print(f"Completed experiment: {exp.name}")
        return True
    
    def assign_job(self, job_id: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        为职位分配实验组
        
        Returns:
            (variant_id, variant_config)
        """
        if not self.active_experiment:
            return None, None
        
        variant = self.active_experiment.assign_variant(job_id)
        return variant.id, variant.config
    
    def record_event(self, job_id: str, event_type: str, data: Dict = None):
        """记录实验事件"""
        if not self.active_experiment:
            return
        
        # 确定职位属于哪个变体
        variant = self.active_experiment.assign_variant(job_id)
        
        # 记录事件
        event = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": self.active_experiment.id,
            "variant_id": variant.id,
            "job_id": job_id,
            "event_type": event_type,
            "data": data or {}
        }
        
        # 保存到文件
        events_file = self.data_dir / f"{self.active_experiment.id}_events.jsonl"
        with open(events_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')
        
        # 更新变体统计
        if event_type == "job_processed":
            variant.sample_size += 1
        
        # 检查是否达到停止条件
        self._check_stop_conditions()
    
    def get_stats(self, experiment_id: str = None) -> Dict:
        """获取实验统计"""
        if experiment_id:
            exp = self.experiments.get(experiment_id)
            if not exp:
                return {}
            return self._calculate_stats(exp)
        
        # 返回所有实验统计
        return {exp_id: self._calculate_stats(exp) for exp_id, exp in self.experiments.items()}
    
    def _calculate_stats(self, exp: Experiment) -> Dict:
        """计算实验统计"""
        stats = {
            "experiment_id": exp.id,
            "name": exp.name,
            "status": exp.status,
            "variants": {}
        }
        
        for variant in exp.variants:
            stats["variants"][variant.id] = {
                "name": variant.name,
                "sample_size": variant.sample_size,
                "weight": variant.weight,
                "metrics": variant.metrics
            }
        
        # 如果有足够数据，计算统计显著性
        if all(v.sample_size >= 30 for v in exp.variants):
            stats["significance"] = self._calculate_significance(exp)
        
        return stats
    
    def _calculate_significance(self, exp: Experiment) -> Dict:
        """计算统计显著性 (简化版)"""
        # TODO: 实现完整的统计检验
        return {
            "p_value": None,
            "confidence_interval": None,
            "is_significant": False,
            "winner": None
        }
    
    def _check_stop_conditions(self):
        """检查是否达到停止条件"""
        if not self.active_experiment:
            return
        
        exp = self.active_experiment
        params = exp.parameters
        
        # 检查样本量
        total_samples = sum(v.sample_size for v in exp.variants)
        if total_samples >= params.get('min_sample_size', 100):
            print(f"Experiment {exp.id} reached min sample size")
            # 可以选择自动停止或继续
        
        # 检查运行时间
        if exp.started_at:
            start = datetime.fromisoformat(exp.started_at)
            max_days = params.get('max_duration_days', 30)
            if datetime.now() - start > timedelta(days=max_days):
                print(f"Experiment {exp.id} reached max duration")
                self.complete_experiment(exp.id)
    
    def _save_experiment_config(self, exp: Experiment):
        """保存实验配置"""
        exp_file = self.experiments_dir / f"{exp.id}.yaml"
        
        # 读取原文件
        with open(exp_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 更新状态
        data['experiment']['status'] = exp.status
        data['experiment']['started_at'] = exp.started_at
        data['experiment']['completed_at'] = exp.completed_at
        
        # 更新变体统计
        for v_data in data['experiment'].get('variants', []):
            variant = exp.get_variant(v_data['id'])
            if variant:
                v_data['sample_size'] = variant.sample_size
                v_data['metrics'] = variant.metrics
        
        # 保存
        with open(exp_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    
    def _generate_final_report(self, exp: Experiment):
        """生成最终实验报告"""
        report = {
            "experiment": {
                "id": exp.id,
                "name": exp.name,
                "description": exp.description,
                "hypothesis": exp.hypothesis,
                "status": exp.status,
                "started_at": exp.started_at,
                "completed_at": exp.completed_at,
            },
            "results": self._calculate_stats(exp),
            "recommendation": self._generate_recommendation(exp)
        }
        
        report_file = self.data_dir / f"{exp.id}_final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Final report saved to: {report_file}")
    
    def _generate_recommendation(self, exp: Experiment) -> str:
        """生成实验建议"""
        # TODO: 基于统计结果生成建议
        return "Based on the experiment results, ..."
    
    def list_experiments(self) -> List[Dict]:
        """列出所有实验"""
        return [
            {
                "id": exp.id,
                "name": exp.name,
                "status": exp.status,
                "variants": len(exp.variants),
                "is_active": self.active_experiment and self.active_experiment.id == exp.id
            }
            for exp in self.experiments.values()
        ]


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 初始化实验管理器
    manager = ExperimentManager()
    
    # 列出所有实验
    experiments = manager.list_experiments()
    print(f"Found {len(experiments)} experiments:")
    for exp in experiments:
        status = "🟢" if exp['is_active'] else "⚪"
        print(f"  {status} {exp['id']}: {exp['name']} ({exp['status']})")
    
    # 启动实验
    # manager.start_experiment("exp_001")
    
    # 为职位分配变体
    # variant_id, config = manager.assign_job("job_123")
    # print(f"Assigned to variant: {variant_id}")
    
    # 记录事件
    # manager.record_event("job_123", "resume_generated")
    # manager.record_event("job_123", "application_sent")
    
    # 获取统计
    # stats = manager.get_stats()
    # print(json.dumps(stats, indent=2))
