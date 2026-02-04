"""
筛选引擎 - 基于配置的硬性筛选
"""

import re
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class FilterResult:
    """筛选结果"""
    passed: bool
    reason: Optional[str] = None
    rules_triggered: List[str] = None
    
    def __post_init__(self):
        if self.rules_triggered is None:
            self.rules_triggered = []


class FilterEngine:
    """筛选引擎"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.hard_rules = config.get('hard_reject_rules', {})
        self.soft_rules = config.get('soft_filter_rules', {})
    
    def check(self, job: Dict) -> FilterResult:
        """
        执行硬性筛选
        
        Returns:
            FilterResult: 筛选结果
        """
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        triggered_rules = []
        
        # 按优先级排序规则
        sorted_rules = sorted(
            self.hard_rules.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        
        for rule_name, rule_config in sorted_rules:
            if not rule_config.get('enabled', True):
                continue
            
            # 检查例外
            exceptions = rule_config.get('exceptions', [])
            if self._check_exceptions(text, exceptions):
                continue
            
            # 检查规则
            patterns = rule_config.get('patterns', [])
            if self._match_patterns(text, patterns):
                triggered_rules.append(rule_name)
                return FilterResult(
                    passed=False,
                    reason=rule_name,
                    rules_triggered=triggered_rules
                )
        
        return FilterResult(passed=True, rules_triggered=triggered_rules)
    
    def score(self, job: Dict) -> float:
        """
        软性评分（用于加分/减分）
        
        Returns:
            分数调整值
        """
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        company = job.get('company', '').lower()
        score_adjustment = 0.0
        
        soft_rules = self.soft_rules
        
        # 正面指标
        positive = soft_rules.get('positive_indicators', {})
        
        # Visa sponsorship
        visa_config = positive.get('visa_sponsorship', {})
        if self._match_patterns(text, visa_config.get('patterns', [])):
            score_adjustment += visa_config.get('weight', 0)
        
        # Junior friendly
        junior_config = positive.get('junior_friendly', {})
        if self._match_patterns(text, junior_config.get('patterns', [])):
            score_adjustment += junior_config.get('weight', 0)
        
        # Target company
        target_config = positive.get('target_company', {})
        target_companies = target_config.get('companies', [])
        if any(tc in company for tc in target_companies):
            score_adjustment += target_config.get('weight', 0)
        
        # Relevant keywords
        keyword_config = positive.get('relevant_keywords', {})
        keyword_patterns = keyword_config.get('patterns', [])
        matches = sum(1 for p in keyword_patterns if re.search(p, text, re.IGNORECASE))
        score_adjustment += matches * keyword_config.get('weight', 0)
        
        # 负面指标
        negative = soft_rules.get('negative_indicators', {})
        
        # Mid-senior level
        senior_config = negative.get('mid_senior_level', {})
        if self._match_patterns(text, senior_config.get('patterns', [])):
            score_adjustment += senior_config.get('weight', 0)
        
        # Specific requirements
        specific_config = negative.get('specific_requirements', {})
        if self._match_patterns(text, specific_config.get('patterns', [])):
            score_adjustment += specific_config.get('weight', 0)
        
        return score_adjustment
    
    def _match_patterns(self, text: str, patterns: List[str]) -> bool:
        """检查文本是否匹配任一模式"""
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                # 如果正则错误，尝试简单字符串匹配
                if pattern.lower() in text:
                    return True
        return False
    
    def _check_exceptions(self, text: str, exceptions: List[str]) -> bool:
        """检查是否匹配例外情况"""
        for exception in exceptions:
            if exception.lower() in text:
                return True
        return False


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 测试配置
    test_config = {
        "hard_reject_rules": {
            "dutch_required": {
                "enabled": True,
                "priority": 1,
                "patterns": ["dutch\\s*required", "nederlands"],
            },
            "experience_too_high": {
                "enabled": True,
                "priority": 2,
                "patterns": ["10\\+\\s*years"],
            }
        },
        "soft_filter_rules": {
            "positive_indicators": {
                "visa_sponsorship": {
                    "patterns": ["visa\\s*sponsor"],
                    "weight": 2.0
                }
            }
        }
    }
    
    engine = FilterEngine(test_config)
    
    # 测试职位
    test_jobs = [
        {
            "title": "Data Scientist",
            "description": "Looking for data scientist. Visa sponsorship available.",
        },
        {
            "title": "Senior Role",
            "description": "Dutch required. 10+ years experience.",
        }
    ]
    
    for job in test_jobs:
        result = engine.check(job)
        score = engine.score(job)
        print(f"Job: {job['title']}")
        print(f"  Passed: {result.passed}, Reason: {result.reason}")
        print(f"  Score adjustment: {score}")
        print()
