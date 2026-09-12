from types import SimpleNamespace

from app.search import TavilySearchProvider


def test_tavily_results_are_normalized(monkeypatch):
    response = SimpleNamespace(
        json=lambda: {
            "results": [
                {"title": "A source", "url": "https://example.com/a", "content": "A useful excerpt"},
                {"title": "Ignored", "url": "https://example.com/b", "content": ""},
            ]
        },
        raise_for_status=lambda: None,
    )
    monkeypatch.setattr("app.search.httpx.post", lambda *args, **kwargs: response)
    bundle = TavilySearchProvider().search("current topic", require_fresh=True)
    assert bundle.provider == "tavily"
    assert bundle.sources[0].title == "A source"
    assert bundle.sources[0].url == "https://example.com/a"
