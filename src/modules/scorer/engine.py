"""
评分引擎 - 规则评分 + AI评分
"""

import re
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ScoreResult:
    """评分结果"""
    score: float
    breakdown: Dict[str, float]
    analysis: str
    recommendations: list


class RuleBasedScorer:
    """基于规则的评分器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_score = config.get('base_score', {}).get('starting_score', 5.0)
        self.keyword_weights = config.get('rule_based_scoring', {}).get('keyword_weights', {})
        self.target_companies = config.get('target_companies', {})
    
    def score(self, job: Dict) -> Tuple[float, Dict]:
        """
        规则评分
        
        Returns:
            (总分, 分项得分)
        """
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        company = job.get('company', '').lower()
        
        breakdown = {
            "base": self.base_score,
            "keywords": 0.0,
            "company": 0.0,
            "total": self.base_score
        }
        
        # 关键词匹配
        keyword_score = 0.0
        matched_keywords = []
        for keyword, weight in self.keyword_weights.items():
            if keyword in text:
                keyword_score += weight
                matched_keywords.append(keyword)
        
        breakdown["keywords"] = keyword_score
        breakdown["matched_keywords"] = matched_keywords
        
        # 目标公司
        company_bonus = 0.0
        for tier, companies in self.target_companies.items():
            if isinstance(companies, list):
                for target in companies:
                    if target in company:
                        bonus = self.target_companies.get(f"{tier}_bonus", 0)
                        company_bonus += bonus
                        breakdown["company_tier"] = tier
                        break
        
        breakdown["company"] = company_bonus
        
        # 计算总分
        total = self.base_score + keyword_score + company_bonus
        
        # 限制范围
        min_score = self.config.get('base_score', {}).get('min_score', 0.0)
        max_score = self.config.get('base_score', {}).get('max_score', 10.0)
        total = max(min_score, min(max_score, total))
        
        breakdown["total"] = round(total, 2)
        
        return total, breakdown


class AIScorer:
    """AI评分器 (接口，实际调用外部AI)"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.dimensions = config.get('ai_scoring', {}).get('dimensions', [])
        self.prompt_template = config.get('ai_scoring', {}).get('prompt_template', '')
    
    async def score(self, job: Dict) -> Tuple[float, Dict, str]:
        """
        AI评分
        
        Returns:
            (总分, 分项得分, 分析文本)
        
        Note: 这个方法是异步的，实际调用时需要传入AI调用函数
        """
        # 这里只是一个接口定义
        # 实际使用时，需要传入一个AI调用函数
        # 例如: ai_score = await ai_call(prompt)
        
        # 返回模拟结果
        return 7.5, {
            "skill_match": 8.0,
            "experience_fit": 7.0,
            "company_interest": 8.0,
            "growth_potential": 7.0
        }, "AI analysis placeholder"


class HybridScorer:
    """混合评分器 - 规则 + AI"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.rule_scorer = RuleBasedScorer(config)
        self.ai_scorer = AIScorer(config)
        
        hybrid_config = config.get('hybrid_scoring', {})
        self.weights = hybrid_config.get('weights', {
            'rule_based': 0.3,
            'ai_based': 0.7
        })
        self.divergence_threshold = hybrid_config.get('divergence_threshold', 3.0)
    
    def rule_score(self, job: Dict) -> ScoreResult:
        """仅规则评分"""
        score, breakdown = self.rule_scorer.score(job)
        
        # 生成简单分析
        analysis = self._generate_analysis(breakdown)
        
        # 生成建议
        recommendations = self._generate_recommendations(breakdown)
        
        return ScoreResult(
            score=score,
            breakdown=breakdown,
            analysis=analysis,
            recommendations=recommendations
        )
    
    async def hybrid_score(self, job: Dict, ai_call_func=None) -> ScoreResult:
        """
        混合评分
        
        Args:
            job: 职位信息
            ai_call_func: AI调用函数，接收prompt返回(score, breakdown, analysis)
        """
        # 规则评分
        rule_score, rule_breakdown = self.rule_scorer.score(job)
        
        # AI评分
        if ai_call_func:
            ai_score, ai_breakdown, ai_analysis = await ai_call_func(job)
        else:
            ai_score, ai_breakdown, ai_analysis = await self.ai_scorer.score(job)
        
        # 混合计算
        w_rule = self.weights.get('rule_based', 0.3)
        w_ai = self.weights.get('ai_based', 0.7)
        
        final_score = rule_score * w_rule + ai_score * w_ai
        
        # 检查差异
        divergence = abs(rule_score - ai_score)
        needs_review = divergence > self.divergence_threshold
        
        breakdown = {
            "rule_score": rule_score,
            "ai_score": ai_score,
            "final_score": round(final_score, 2),
            "divergence": round(divergence, 2),
            "needs_review": needs_review,
            "rule_breakdown": rule_breakdown,
            "ai_breakdown": ai_breakdown
        }
        
        return ScoreResult(
            score=round(final_score, 2),
            breakdown=breakdown,
            analysis=ai_analysis,
            recommendations=[]
        )
    
    def _generate_analysis(self, breakdown: Dict) -> str:
        """生成简单分析"""
        matched = breakdown.get('matched_keywords', [])
        if matched:
            return f"Matched keywords: {', '.join(matched[:5])}"
        return "No strong keyword matches"
    
    def _generate_recommendations(self, breakdown: Dict) -> list:
        """生成建议"""
        recommendations = []
        
        score = breakdown.get('total', 0)
        if score >= 8:
            recommendations.append("High match - prioritize application")
        elif score >= 6:
            recommendations.append("Good match - apply with tailored resume")
        else:
            recommendations.append("Low match - consider skipping")
        
        return recommendations


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 测试配置
    test_config = {
        "base_score": {"starting_score": 5.0, "min_score": 0, "max_score": 10},
        "rule_based_scoring": {
            "keyword_weights": {
                "machine learning": 2.0,
                "python": 1.0,
                "senior": -1.0
            }
        },
        "target_companies": {
            "tier_1": ["picnic", "adyen"],
            "tier_1_bonus": 2.0
        }
    }
    
    scorer = HybridScorer(test_config)
    
    test_job = {
        "title": "Machine Learning Engineer",
        "company": "Picnic",
        "description": "Looking for ML engineer with Python experience"
    }
    
    result = scorer.rule_score(test_job)
    print(f"Score: {result.score}")
    print(f"Breakdown: {result.breakdown}")
    print(f"Analysis: {result.analysis}")
