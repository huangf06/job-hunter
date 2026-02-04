# Test script
from src.config.loader import ConfigLoader
from src.modules.filter.engine import FilterEngine

loader = ConfigLoader('config')
config = loader.load()
engine = FilterEngine(config.filters)

test_jobs = [
    {'title': 'Data Scientist', 'description': 'Python, ML. Visa sponsorship available.'},
    {'title': 'Senior Role', 'description': 'Dutch required. 10+ years experience.'},
]

for job in test_jobs:
    result = engine.check(job)
    score = engine.score(job)
    print(f"Job: {job['title']}")
    print(f"  Passed: {result.passed}, Reason: {result.reason}")
    print(f"  Soft score: {score}")
    print()
