import importlib

SCRAPERS = {
    "linkedin": "src.scrapers.linkedin:LinkedInScraper",
    "greenhouse": "src.scrapers.greenhouse:GreenhouseScraper",
    "iamexpat": "src.scrapers.iamexpat:IamExpatScraper",
}

ALIASES = {
    "ats": ["greenhouse"],
    "all": ["linkedin", "greenhouse"],
}


def resolve_platform_names(name: str) -> list[str]:
    if name in ALIASES:
        return list(ALIASES[name])
    if name in SCRAPERS:
        return [name]
    raise KeyError(f"Unknown scraper platform: {name}")


def get_scraper_class(name: str):
    platform_name = resolve_platform_names(name)[0]
    module_path, class_name = SCRAPERS[platform_name].split(":")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
