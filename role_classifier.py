"""
Role Classifier - 岗位分类器
根据 JD 自动识别最适合的岗位类型
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import yaml
from pathlib import Path


@dataclass
class ClassificationResult:
    """分类结果"""
    role: str
    confidence: float
    scores: Dict[str, float]
    matched_keywords: Dict[str, List[str]]
    applied_rules: List[str]


class RoleClassifier:
    """岗位分类器"""
    
    # 角色代码映射
    ROLE_CODES = {
        'ml_engineer': 'ML Engineer',
        'data_engineer': 'Data Engineer',
        'data_scientist': 'Data Scientist',
        'quant': 'Quant Researcher'
    }
    
    def __init__(self, config_path: str = "config/role_templates.yaml"):
        """初始化分类器"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.keyword_weights = self.config.get('role_classifier', {}).get('keyword_weights', {})
        self.special_rules = self.config.get('role_classifier', {}).get('special_rules', {})
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_path.exists():
            # 尝试其他路径
            alt_paths = [
                Path("job-hunter") / self.config_path,
                Path("workspace/job-hunter") / self.config_path,
            ]
            for path in alt_paths:
                if path.exists():
                    self.config_path = path
                    break
        
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def classify(self, title: str, description: str, company: str = "") -> ClassificationResult:
        """
        分类岗位类型
        
        Args:
            title: 职位标题
            description: 职位描述
            company: 公司名称
            
        Returns:
            ClassificationResult: 分类结果
        """
        text = f"{title} {description}".lower()
        company_lower = company.lower()
        
        # 初始化分数
        scores = {
            'ml_engineer': 0.0,
            'data_engineer': 0.0,
            'data_scientist': 0.0,
            'quant': 0.0
        }
        
        matched_keywords = {
            'ml_engineer': [],
            'data_engineer': [],
            'data_scientist': [],
            'quant': []
        }
        
        applied_rules = []
        
        # 1. 检查公司强制覆盖规则
        company_override = self.special_rules.get('company_override', {})
        if company_lower in company_override:
            forced_role = company_override[company_lower]
            scores[forced_role] = 100.0  # 强制最高分
            applied_rules.append(f"Company override: {company} -> {forced_role}")
            return ClassificationResult(
                role=forced_role,
                confidence=1.0,
                scores=scores,
                matched_keywords=matched_keywords,
                applied_rules=applied_rules
            )
        
        # 2. 检查标题强制匹配规则
        title_override = self.special_rules.get('title_override', [])
        for rule in title_override:
            pattern = rule.get('pattern', '')
            if re.search(pattern, title, re.IGNORECASE):
                forced_role = rule.get('role')
                scores[forced_role] = 100.0
                applied_rules.append(f"Title override: {pattern} -> {forced_role}")
                return ClassificationResult(
                    role=forced_role,
                    confidence=1.0,
                    scores=scores,
                    matched_keywords=matched_keywords,
                    applied_rules=applied_rules
                )
        
        # 3. 计算关键词得分
        for role, keywords in self.keyword_weights.items():
            for keyword, weight in keywords.items():
                if keyword in text:
                    scores[role] += weight
                    matched_keywords[role].append(keyword)
        
        # 4. 应用排除规则 (降权)
        exclude_patterns = self.special_rules.get('exclude_patterns', [])
        for rule in exclude_patterns:
            pattern = rule.get('pattern', '')
            if re.search(pattern, text, re.IGNORECASE):
                reduce_roles = rule.get('reduce_roles', [])
                reduction = rule.get('reduction', 0)
                for role in reduce_roles:
                    scores[role] -= reduction
                    applied_rules.append(f"Exclusion: {pattern} reduces {role} by {reduction}")
        
        # 5. 确定最佳匹配
        best_role = max(scores, key=scores.get)
        best_score = scores[best_role]
        
        # 计算置信度 (基于分数差距)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2 and sorted_scores[0] > 0:
            confidence = min(1.0, (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0])
        else:
            confidence = 0.5 if best_score > 0 else 0.0
        
        return ClassificationResult(
            role=best_role,
            confidence=confidence,
            scores=scores,
            matched_keywords=matched_keywords,
            applied_rules=applied_rules
        )
    
    def get_role_name(self, role_code: str) -> str:
        """获取角色显示名称"""
        return self.ROLE_CODES.get(role_code, role_code)
    
    def explain_classification(self, result: ClassificationResult) -> str:
        """生成分类解释报告"""
        lines = [
            f"Classification Result: {self.get_role_name(result.role)}",
            f"Confidence: {result.confidence:.1%}",
            "",
            "Scores:",
        ]
        
        for role, score in sorted(result.scores.items(), key=lambda x: x[1], reverse=True):
            role_name = self.get_role_name(role)
            marker = "*" if role == result.role else " "
            lines.append(f"  [{marker}] {role_name}: {score:.1f}")
        
        if result.matched_keywords.get(result.role):
            lines.extend([
                "",
                f"Matched Keywords for {self.get_role_name(result.role)}:",
            ])
            for kw in result.matched_keywords[result.role][:10]:  # 最多显示10个
                lines.append(f"  • {kw}")
        
        if result.applied_rules:
            lines.extend([
                "",
                "Applied Rules:",
            ])
            for rule in result.applied_rules:
                lines.append(f"  • {rule}")
        
        return "\n".join(lines)


# ============== 测试 ==============

def test_classifier():
    """测试分类器"""
    classifier = RoleClassifier()
    
    test_cases = [
        {
            "title": "Machine Learning Engineer",
            "description": "Build production ML pipelines using PyTorch, Docker, Kubernetes. Deploy models to AWS.",
            "company": "Picnic"
        },
        {
            "title": "Data Engineer",
            "description": "Design data pipelines with Spark, Databricks, Delta Lake. ETL workflows.",
            "company": "ABN AMRO"
        },
        {
            "title": "Data Scientist",
            "description": "Statistical modeling, A/B testing, insights. Python, SQL.",
            "company": "Booking.com"
        },
        {
            "title": "Quantitative Researcher",
            "description": "Alpha research, backtesting, factor modeling. Python, statistics.",
            "company": "Optiver"
        },
        {
            "title": "Senior ML Engineer",
            "description": "Deep learning, recommendation systems, MLOps.",
            "company": "Unknown"
        }
    ]
    
    print("="*70)
    print("Role Classifier Test")
    print("="*70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['title']} @ {test['company']}")
        print("-"*70)
        
        result = classifier.classify(
            title=test['title'],
            description=test['description'],
            company=test['company']
        )
        
        print(classifier.explain_classification(result))


if __name__ == "__main__":
    test_classifier()
