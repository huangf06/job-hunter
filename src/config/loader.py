"""
配置加载器 - 支持分层配置和环境覆盖
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Config:
    """配置对象"""
    filters: Dict[str, Any]
    scoring: Dict[str, Any]
    resume: Dict[str, Any]
    pipeline: Dict[str, Any]
    crawler: Dict[str, Any]
    experiment: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Config":
        return cls(
            filters=data.get("filters", {}),
            scoring=data.get("scoring", {}),
            resume=data.get("resume", {}),
            pipeline=data.get("pipeline", {}),
            crawler=data.get("crawler", {}),
            experiment=data.get("experiment")
        )


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.base_dir = self.config_dir / "base"
        self.env_dir = self.config_dir / "environments"
        self.exp_dir = self.config_dir / "experiments"
    
    def load(self, 
             environment: str = None,
             experiment: str = None,
             overrides: Dict[str, Any] = None) -> Config:
        """
        加载配置
        
        Args:
            environment: 环境名称 (development, production)
            experiment: 实验配置文件名
            overrides: 命令行覆盖参数
        
        Returns:
            Config对象
        """
        # 1. 加载基础配置
        config = self._load_base_config()
        
        # 2. 加载环境配置 (覆盖基础配置)
        if environment:
            env_config = self._load_environment_config(environment)
            config = self._merge_configs(config, env_config)
        
        # 3. 加载实验配置 (覆盖环境配置)
        if experiment:
            exp_config = self._load_experiment_config(experiment)
            config = self._merge_configs(config, exp_config)
        
        # 4. 应用环境变量覆盖
        config = self._apply_env_overrides(config)
        
        # 5. 应用命令行覆盖
        if overrides:
            config = self._apply_overrides(config, overrides)
        
        return Config.from_dict(config)
    
    def _load_base_config(self) -> Dict[str, Any]:
        """加载基础配置"""
        config = {}
        
        for config_file in ["filters.yaml", "scoring.yaml", "resume.yaml", "pipeline.yaml", "crawler.yaml"]:
            filepath = self.base_dir / config_file
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        key = config_file.replace('.yaml', '')
                        config[key] = data
        
        return config
    
    def _load_environment_config(self, environment: str) -> Dict[str, Any]:
        """加载环境特定配置"""
        filepath = self.env_dir / f"{environment}.yaml"
        if not filepath.exists():
            raise FileNotFoundError(f"Environment config not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _load_experiment_config(self, experiment: str) -> Dict[str, Any]:
        """加载实验配置"""
        # 支持带或不带.yaml后缀
        if not experiment.endswith('.yaml'):
            experiment = f"{experiment}.yaml"
        
        filepath = self.exp_dir / experiment
        if not filepath.exists():
            raise FileNotFoundError(f"Experiment config not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data and 'experiment' in data:
                return {"experiment": data["experiment"]}
            return {}
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """递归合并配置"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """应用环境变量覆盖"""
        # 支持 JOB_HUNTER_* 格式的环境变量
        prefix = "JOB_HUNTER_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 将 JOB_HUNTER_SCORING_THRESHOLD 转换为 scoring.threshold
                path = key[len(prefix):].lower().replace('_', '.')
                config = self._set_nested_value(config, path, self._parse_value(value))
        
        return config
    
    def _apply_overrides(self, config: Dict, overrides: Dict[str, Any]) -> Dict:
        """应用命令行覆盖参数"""
        for path, value in overrides.items():
            config = self._set_nested_value(config, path, value)
        return config
    
    def _set_nested_value(self, config: Dict, path: str, value: Any) -> Dict:
        """设置嵌套值"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return config
    
    def _parse_value(self, value: str) -> Any:
        """解析字符串值为合适类型"""
        # 尝试解析为bool
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # 尝试解析为int
        try:
            return int(value)
        except ValueError:
            pass
        
        # 尝试解析为float
        try:
            return float(value)
        except ValueError:
            pass
        
        # 尝试解析为list (逗号分隔)
        if ',' in value:
            return [v.strip() for v in value.split(',')]
        
        # 默认返回字符串
        return value
    
    def list_experiments(self) -> list:
        """列出所有可用的实验配置"""
        experiments = []
        if self.exp_dir.exists():
            for f in self.exp_dir.glob("*.yaml"):
                with open(f, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    if data and 'experiment' in data:
                        exp = data['experiment']
                        experiments.append({
                            'id': exp.get('id'),
                            'name': exp.get('name'),
                            'file': f.name,
                            'status': exp.get('status', 'unknown'),
                            'description': exp.get('description', '')
                        })
        return experiments


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 初始化加载器
    loader = ConfigLoader("config")
    
    # 加载基础配置
    config = loader.load()
    print("基础配置加载完成")
    print(f"筛选规则数: {len(config.filters.get('hard_reject_rules', {}))}")
    print(f"评分阈值: {config.scoring.get('thresholds', {}).get('generate_resume')}")
    
    # 加载带实验的配置
    # config = loader.load(experiment="exp_001_summary_length")
    
    # 加载带环境覆盖的配置
    # config = loader.load(environment="production")
    
    # 加载带命令行覆盖的配置
    # config = loader.load(overrides={"scoring.thresholds.generate_resume": 7.0})
    
    # 列出所有实验
    experiments = loader.list_experiments()
    print(f"\n可用实验: {len(experiments)}")
    for exp in experiments:
        print(f"  - {exp['id']}: {exp['name']} ({exp['status']})")
