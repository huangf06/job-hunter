import importlib


def load_linkedin_parser_module():
    return importlib.import_module("src.scrapers.linkedin_parser")


def test_parser_extracts_search_cards_without_browser_objects():
    """Inventory from v6: card extraction must operate on provided card payloads, not Playwright pages."""
    parser = load_linkedin_parser_module()

    cards = [
        {
            "title": "Senior Data Engineer  Senior Data Engineer",
            "company": "Acme",
            "location": "Amsterdam",
            "url": "https://www.linkedin.com/jobs/view/123",
        }
    ]

    jobs = parser.parse_search_cards(cards)

    assert jobs == [
        {
            "title": "Senior Data Engineer",
            "company": "Acme",
            "location": "Amsterdam",
            "url": "https://www.linkedin.com/jobs/view/123",
            "source": "LinkedIn",
        }
    ]


def test_parser_extracts_job_description_from_inputs():
    """Inventory from v6: JD extraction belongs to parser helpers, independent of browser lifecycle."""
    parser = load_linkedin_parser_module()

    description = parser.extract_job_description(
        {
            "json_ld_description": "<p>Build ML systems.</p>",
            "detail_text": "ignored fallback text",
        }
    )

    assert "Build ML systems." in description
