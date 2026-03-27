import importlib


def test_registry_exposes_platform_names():
    registry = importlib.import_module("src.scrapers.registry")

    assert set(registry.SCRAPERS) == {"linkedin", "greenhouse", "iamexpat"}


def test_registry_exposes_platform_aliases():
    registry = importlib.import_module("src.scrapers.registry")

    assert registry.ALIASES["ats"] == ["greenhouse"]
    assert registry.ALIASES["all"] == ["linkedin", "greenhouse"]
