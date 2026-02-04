# Test scorer
from src.config.loader import ConfigLoader
from src.modules.scorer.engine import HybridScorer

loader = ConfigLoader('config')
config = loader.load()
scorer = HybridScorer(config.scoring)

test_jobs = [
    {'title': 'Machine Learning Engineer', 'company': 'Picnic', 'description': 'Python, PyTorch, ML. Visa sponsorship available.'},
    {'title': 'Data Scientist', 'company': 'Startup', 'description': 'Python, SQL, data analysis.'},
]

for job in test_jobs:
    result = scorer.rule_score(job)
    print(f"Job: {job['title']} @ {job['company']}")
    print(f"  Score: {result.score}")
    print(f"  Breakdown: {result.breakdown}")
    print(f"  Analysis: {result.analysis}")
    print()
