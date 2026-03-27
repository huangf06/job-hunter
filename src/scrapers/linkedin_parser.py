import re


def _strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<li>", "\n- ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def clean_title(title: str) -> str:
    if not title:
        return ""

    title = title.strip().replace("\n", " ")
    title = re.sub(r"\s*with verification\s*$", "", title, flags=re.IGNORECASE)

    parts = re.split(r"\s{2,}", title)
    if len(parts) >= 2 and parts[0].strip() == parts[1].strip():
        title = parts[0].strip()

    length = len(title)
    if length >= 10:
        mid = length // 2
        for pos in range(max(4, mid - 5), min(length - 3, mid + 6)):
            first = title[:pos]
            second = title[pos:]
            if first == second:
                title = first
                break
            if len(second) >= 5 and first.startswith(second):
                title = first
                break

    return re.sub(r"\s+", " ", title).strip()


def parse_search_cards(cards: list[dict]) -> list[dict]:
    jobs = []
    for card in cards:
        title = clean_title(card.get("title", ""))
        company = card.get("company", "").strip()
        url = card.get("url", "").strip()
        if not title or not company or not url:
            continue
        jobs.append(
            {
                "title": title,
                "company": company,
                "location": card.get("location", "").strip(),
                "url": url,
                "source": "LinkedIn",
            }
        )
    return jobs


def extract_job_description(payload: dict) -> str:
    description = (
        payload.get("json_ld_description")
        or payload.get("detail_html")
        or payload.get("detail_text")
        or ""
    )
    return _strip_html(description)
