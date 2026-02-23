# Multi-Platform Job Scraping — Design Doc

Date: 2026-02-23
Status: Approved
Scope: Phase 1 (IamExpat + Greenhouse + Lever)

## 目标

扩展爬取范围，从仅 LinkedIn 扩展到荷兰求职主流平台。Phase 1 覆盖：
- **IamExpat Jobs** — 外籍人士专属，职位通常提供签证担保
- **Greenhouse ATS** — 目标公司 career page (公开 JSON API)
- **Lever ATS** — 目标公司 career page (公开 JSON API)

Phase 2 (未来): Indeed.nl (反爬复杂，延后)
暂缓: Glassdoor (与 Indeed 重叠度高，ROI 低)

## 架构

### 现有 LinkedIn scraper 保持不变

`scripts/linkedin_scraper_v6.py` 不迁移，通过 import 调用。

### 新增文件结构

```
src/scrapers/
├── base.py              # BaseScraper 抽象类
├── iamexpat.py          # IamExpat Jobs (Playwright)
├── greenhouse.py        # Greenhouse API (requests)
└── lever.py             # Lever API (requests)

scripts/
└── multi_scraper.py     # Orchestrator CLI

config/
└── target_companies.yaml # 目标公司 ATS 配置
```

### 数据流

```
target_companies.yaml ──→ GreenhouseScraper ──→ insert_job(source="Greenhouse")
                     ──→ LeverScraper      ──→ insert_job(source="Lever")
search_profiles.yaml ──→ IamExpatScraper   ──→ insert_job(source="IamExpat")
```

下游 pipeline (filter → score → AI analyze → resume) 完全不变。

## BaseScraper 接口

```python
class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, save_to_db: bool = True) -> list[dict]:
        """返回统一格式的 job dict 列表"""
        pass
```

统一 job dict 格式 (与 LinkedIn scraper 一致):
```python
{
    "title": str,
    "company": str,
    "location": str,
    "url": str,           # 用于生成 job_id (MD5)
    "description": str,   # 完整 JD
    "source": str,        # "IamExpat" | "Greenhouse" | "Lever"
    "scraped_at": str,    # ISO timestamp
    "search_profile": str,
    "search_query": str
}
```

## 配置

### target_companies.yaml (新增)

```yaml
companies:
  - name: Booking.com
    ats: greenhouse
    board_token: bookingcom
    location_filter: "Amsterdam"

  - name: Adyen
    ats: greenhouse
    board_token: adyen

  - name: Spotify
    ats: lever
    board_token: spotify
    location_filter: "Netherlands"
```

### search_profiles.yaml (扩展)

```yaml
profiles:
  ml_data:
    iamexpat:
      queries:
        - keywords: "data engineer"
        - keywords: "machine learning engineer"
        - keywords: "python developer"
```

## 各平台实现要点

| Scraper | 方式 | API/URL | 分页 | 备注 |
|---------|------|---------|------|------|
| Greenhouse | requests | `boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` | 无需 (返回全部) | 无认证，无反爬 |
| Lever | requests | `api.lever.co/v0/postings/{token}?mode=json` | `skip`+`limit` | 无认证，无反爬 |
| IamExpat | Playwright | `iamexpat.nl/career/jobs-netherlands?search={kw}&page={n}` | `page` 参数, 20条/页 | Next.js, 需浏览器渲染 |

共享逻辑:
- `location_filter`: 按关键词过滤荷兰相关职位
- `title_blacklist` / `company_blacklist`: 复用现有配置
- Dedup: URL-based MD5 hash (与 LinkedIn 一致)

## CI 集成

在 `job-pipeline.yml` 中 LinkedIn scraper 之后、`--process` 之前加入:
```yaml
- name: Scrape all platforms
  run: python scripts/multi_scraper.py --all --save-to-db
```

## 决策记录

- LinkedIn scraper 不迁移 (复杂度高，运行稳定，重构无收益)
- Glassdoor 暂缓 (与 Indeed 同属一家，职位重叠，反爬最难)
- Indeed 放 Phase 2 (反爬复杂，需要专门处理)
- ATS 范围: 手动维护目标公司列表 (可控且精准)
- 技术路线: API 优先 + Playwright 兜底
