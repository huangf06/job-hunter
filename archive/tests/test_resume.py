# Test resume generator
import asyncio
from src.config.loader import ConfigLoader
from src.modules.resume.generator import ResumeGenerator

loader = ConfigLoader('config')
config = loader.load()
generator = ResumeGenerator(config.resume)

test_job = {
    'title': 'Machine Learning Engineer',
    'company': 'Picnic'
}

html = generator.generate(test_job)
print(f"Generated HTML length: {len(html)}")

# 保存
filepath = generator.save(html, test_job, 'output')
print(f"Saved to: {filepath}")

# 生成PDF
async def gen_pdf():
    pdf_path = await generator.to_pdf(filepath)
    print(f"PDF: {pdf_path}")

asyncio.run(gen_pdf())
print("Done!")
