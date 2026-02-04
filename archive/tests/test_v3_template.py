# Test new resume template
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test_template():
    template_path = Path("templates/resume_v3.html")
    output_path = Path("output/test_resume_v3.pdf")
    
    print(f"Testing template: {template_path}")
    print(f"Output: {output_path}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto(f"file:///{template_path.absolute()}")
        await page.wait_for_load_state("networkidle")
        
        await page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "0.55in", "right": "0.55in", "bottom": "0.55in", "left": "0.55in"},
            print_background=True
        )
        
        await browser.close()
    
    print(f"✓ PDF generated successfully!")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

asyncio.run(test_template())
