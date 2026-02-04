# LinkedIn 职位自动抓取方案

## 需求背景

自动化获取LinkedIn职位信息，替代以下手动流程：
1. 登录LinkedIn
2. 点击Jobs
3. 搜索关键词（如"data engineer"）
4. 设置地点（Netherlands）
5. 筛选Date posted为past 24 hours
6. 筛选Remote为Hybrid和on-site
7. 滚动页面加载完整列表
8. 用F12控制台运行JS脚本提取数据

## 现有JS提取脚本

```javascript
(function() {
    let jobs = [];
    // 适配 LinkedIn 不同的 DOM 结构
    let items = document.querySelectorAll('.jobs-search-results__list-item, li.occludable-update, .job-card-container');

    console.log(`%c[LinkedIn Harvester] Found ${items.length} items. Processing...`, "color: #0073b1; font-weight: bold;");

    items.forEach(item => {
        try {
            // 提取职位标题
            let titleEl = item.querySelector('.job-card-list__title, .artdeco-entity-lockup__title, .job-card-container__link');
            if (!titleEl) return;
            let title = titleEl.innerText.trim();

            // 提取公司名
            let companyEl = item.querySelector('.job-card-container__company-name, .artdeco-entity-lockup__subtitle, .job-card-container__company-link');
            let company = companyEl ? companyEl.innerText.trim() : "Unknown";

            // 提取地点
            let locationEl = item.querySelector('.job-card-container__metadata-item, .artdeco-entity-lockup__caption');
            let location = locationEl ? locationEl.innerText.trim().replace(/\n/g, "") : "";

            // 提取链接并清理
            let link = "";
            let linkEl = item.querySelector('a.job-card-list__title, a.artdeco-entity-lockup__title, a.job-card-container__link');
            if (linkEl) {
                link = linkEl.href.split('?')[0];
            }

            // 基础优先级逻辑
            let priority = "Medium";
            let lowerTitle = title.toLowerCase();
            if (lowerTitle.includes("senior") || lowerTitle.includes("lead") || lowerTitle.includes("staff") || lowerTitle.includes("principal")) priority = "High";
            if (lowerTitle.includes("quant") || lowerTitle.includes("machine learning") || lowerTitle.includes("ai")) priority = "High";
            if (lowerTitle.includes("intern") || lowerTitle.includes("junior")) priority = "Low";

            // 格式化为 CSV 行
            let date = new Date().toISOString().split('T')[0];
            let row = `"${date}","${company.replace(/"/g, '""')}","${title.replace(/"/g, '""')}","${location.replace(/"/g, '""')}","${link}","${priority}","todo",""`;

            // 去重判断
            if (link && !jobs.some(j => j.includes(link))) {
                jobs.push(row);
            }
        } catch (e) {
            // 忽略解析失败的单个条目
        }
    });

    if (jobs.length > 0) {
        console.log("\n%c[SUCCESS] Copy the lines below to your leads.csv:\n", "color: green; font-weight: bold;");
        console.log(jobs.join("\n"));
        console.log("\n%c--------------------------------------------------", "color: #999;");
    } else {
        console.warn("[WARNING] No jobs found. Try scrolling down the list first to trigger lazy loading.");
    }
})();
```

## 方案对比

### 方案1: 浏览器自动化（Selenium/Playwright）- 推荐自建

最接近手动流程的自动化方案。

**优点**：
- 完全控制
- 免费
- 可复用现有JS逻辑

**缺点**：
- 需要处理登录、反爬虫检测
- 维护成本

**参考资源**：
- [Tutorial: Web Scraping LinkedIn Jobs with Playwright](https://dev.to/victorlg98/tutorial-web-scraping-linkedin-jobs-with-playwright-2h7l)
- [GitHub: LinkedIn-Job-Selenium-Scrapper](https://github.com/hossam-elshabory/LinkedIn-Job-Selenium-Scrapper)
- [How to Scrape LinkedIn Jobs With Python](https://scrapeops.io/python-web-scraping-playbook/python-scrape-linkedin-jobs/)

### 方案2: 第三方Scraping API服务

| 服务 | 特点 | 价格 |
|------|------|------|
| **Bright Data** | 企业级，代理池强大 | $$$$ |
| **Phantombuster** | 无代码，易用 | $59+/月 |
| **Apify** | 开源actor生态 | 按用量 |
| **ScrapingDog** | 简单API | $40+/月 |

**优点**：稳定，处理反爬虫，无需维护
**缺点**：付费，数据格式可能不完全符合需求

### 方案3: LinkedIn官方渠道（有限）

- **LinkedIn Jobs API**：仅对合作伙伴开放，普通开发者无法使用
- **RSS Feed**：LinkedIn已关闭公开RSS

## 推荐实现：Playwright + 现有JS逻辑

```python
# linkedin_job_scraper.py 核心结构
import json
from playwright.sync_api import sync_playwright
from datetime import datetime

class LinkedInJobScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def login(self, page):
        # 处理登录，建议用cookie持久化避免频繁登录
        pass

    def search_jobs(self, page, keyword, location):
        # 导航到Jobs，输入搜索条件
        url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}"
        page.goto(url)

        # 应用筛选器
        page.click('[aria-label="Date posted filter"]')
        page.click('text=Past 24 hours')
        # ... 其他筛选器

    def scroll_and_load(self, page):
        # 滚动加载完整列表
        for _ in range(10):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

    def extract_jobs(self, page):
        # 直接复用现有JS逻辑
        return page.evaluate("""() => {
            // 上面的JS代码
        }""")

    def run(self, keyword, location):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            self.login(page)
            self.search_jobs(page, keyword, location)
            self.scroll_and_load(page)
            jobs = self.extract_jobs(page)

            browser.close()
            return jobs
```

## 注意事项

1. **账号风险**：频繁自动化操作可能导致账号被限制
   - 使用非headless模式
   - 添加随机延迟
   - 控制请求频率
   - 使用独立账号

2. **LinkedIn ToS**：技术上可行，但违反LinkedIn服务条款，仅供个人求职使用

3. **替代数据源**：考虑同时抓取Indeed、Glassdoor等平台，分散风险

## 下一步

- [ ] 创建新项目文件夹
- [ ] 实现Playwright自动化脚本
- [ ] 添加cookie持久化（避免频繁登录）
- [ ] 添加配置文件（关键词、地点、筛选条件）
- [ ] 输出CSV/JSON格式
- [ ] 可选：定时任务（cron/Task Scheduler）

## 参考链接

- [How to Scrape LinkedIn Data in 2026 - Bright Data](https://brightdata.com/blog/how-tos/linkedin-scraping-guide)
- [10 Best LinkedIn Scraper Tools for Data Extraction 2026](https://www.browseract.com/blog/best-linkedin-scraper-tools-for-data-extraction)
- [Top 26 LinkedIn Scraping Tools to Extract Data in 2026](https://evaboot.com/blog/linkedin-scraping-tools)
