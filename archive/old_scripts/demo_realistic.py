# Demo with realistic job data
import asyncio
from src.config.loader import ConfigLoader
from src.core.hunter import JobHunter

async def demo():
    """使用真实格式的职位数据进行演示"""
    
    # 模拟从LinkedIn爬取的职位
    realistic_jobs = [
        {
            "id": "4123456789",
            "title": "Machine Learning Engineer",
            "company": "Picnic",
            "location": "Amsterdam, North Holland, Netherlands",
            "url": "https://www.linkedin.com/jobs/view/4123456789/",
            "description": """
            About the role:
            We are looking for a Machine Learning Engineer to join our team in Amsterdam. 
            You will work on building and deploying ML models that power our logistics and 
            demand forecasting systems.
            
            Requirements:
            - 2-4 years of experience in ML engineering
            - Strong Python skills, experience with PyTorch or TensorFlow
            - Experience with data pipelines and ML infrastructure
            - Bachelor's or Master's degree in Computer Science or related field
            
            What we offer:
            - Visa sponsorship for highly skilled migrants
            - Competitive salary
            - Hybrid work model
            """,
            "source": "linkedin",
            "scraped_at": "2026-02-03T21:30:00",
            "has_easy_apply": True
        },
        {
            "id": "4123456790",
            "title": "Senior Data Scientist (Dutch Speaking)",
            "company": "ABN AMRO",
            "location": "Amsterdam",
            "url": "https://www.linkedin.com/jobs/view/4123456790/",
            "description": """
            Senior Data Scientist position at ABN AMRO.
            
            Requirements:
            - 8+ years of experience in data science
            - Fluent Dutch required for client communication
            - Experience with credit risk modeling
            - Master's or PhD in quantitative field
            """,
            "source": "linkedin",
            "scraped_at": "2026-02-03T21:30:00",
            "has_easy_apply": True
        },
        {
            "id": "4123456791",
            "title": "Junior Data Analyst",
            "company": "Coolblue",
            "location": "Rotterdam",
            "url": "https://www.linkedin.com/jobs/view/4123456791/",
            "description": """
            Junior Data Analyst wanted!
            
            Are you passionate about data and e-commerce? Join Coolblue's data team.
            
            Requirements:
            - 0-2 years experience
            - SQL and Python skills
            - Good communication skills
            - EU work permit or eligible for visa sponsorship
            
            We offer relocation assistance.
            """,
            "source": "linkedin",
            "scraped_at": "2026-02-03T21:30:00",
            "has_easy_apply": True
        },
        {
            "id": "4123456792",
            "title": "Principal Engineer - AI Platform",
            "company": "Booking.com",
            "location": "Amsterdam",
            "url": "https://www.linkedin.com/jobs/view/4123456792/",
            "description": """
            Principal Engineer to lead our AI Platform team.
            
            Requirements:
            - 12+ years of software engineering experience
            - 5+ years in ML/AI leadership roles
            - Experience managing large engineering teams
            - Deep expertise in distributed systems
            """,
            "source": "linkedin",
            "scraped_at": "2026-02-03T21:30:00",
            "has_easy_apply": False
        },
        {
            "id": "4123456793",
            "title": "Quantitative Researcher",
            "company": "Optiver",
            "location": "Amsterdam",
            "url": "https://www.linkedin.com/jobs/view/4123456793/",
            "description": """
            Join Optiver as a Quantitative Researcher!
            
            About the role:
            Develop and improve pricing models, risk management tools, and trading algorithms.
            
            Requirements:
            - 1-3 years experience in quantitative research or trading
            - Strong programming skills (Python, C++)
            - Master's or PhD in Mathematics, Physics, CS, or related
            - Experience with statistical modeling and data analysis
            
            We sponsor visas for exceptional candidates.
            """,
            "source": "linkedin",
            "scraped_at": "2026-02-03T21:30:00",
            "has_easy_apply": True
        }
    ]
    
    print("="*70)
    print("DEMO: Processing realistic LinkedIn job data")
    print("="*70)
    print(f"\nInput: {len(realistic_jobs)} jobs from LinkedIn\n")
    
    # 加载配置
    loader = ConfigLoader('config')
    config = loader.load()
    
    # 初始化
    hunter = JobHunter(config)
    
    # 处理
    results = await hunter.process_jobs(realistic_jobs)
    
    print("\n" + "="*70)
    print("DETAILED RESULTS:")
    print("="*70)
    
    for r in results:
        print(f"\n{r.company} - {r.title}")
        print(f"  Status: {r.status}")
        if r.filter_reason:
            print(f"  Reason: {r.filter_reason}")
        if r.score:
            print(f"  Score: {r.score}")
        if r.resume_path:
            print(f"  Resume: {r.resume_path}")

asyncio.run(demo())
