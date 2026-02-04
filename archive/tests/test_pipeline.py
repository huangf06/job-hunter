# Test full pipeline
import asyncio
from src.config.loader import ConfigLoader
from src.core.hunter import JobHunter

async def test():
    loader = ConfigLoader('config')
    config = loader.load()
    hunter = JobHunter(config)
    
    test_jobs = [
        {'title': 'Machine Learning Engineer', 'company': 'Picnic', 'description': 'Python, PyTorch, ML. Visa sponsorship available.', 'url': 'https://example.com/1'},
        {'title': 'Senior Role', 'company': 'Local Bank', 'description': 'Dutch required. 10+ years experience.', 'url': 'https://example.com/2'},
        {'title': 'Data Analyst', 'company': 'Startup', 'description': 'Entry level. SQL, Python.', 'url': 'https://example.com/3'},
    ]
    
    results = await hunter.process_jobs(test_jobs)
    print(f"\nProcessed {len(results)} jobs")

asyncio.run(test())
