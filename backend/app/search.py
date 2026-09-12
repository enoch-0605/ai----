from __future__ import annotations

from typing import Protocol

import httpx

from .config import SEARCH_MAX_AGE_DAYS, SEARCH_MAX_RESULTS, SEARCH_TIMEOUT_SECONDS, TAVILY_API_KEY
from .evidence import EvidenceBundle, FreshnessStatus, SourceRecord, normalize_sources


class SearchProvider(Protocol):
    def search(self, topic: str, *, require_fresh: bool) -> EvidenceBundle: ...


class MockSearchProvider:
    def search(self, topic: str, *, require_fresh: bool) -> EvidenceBundle:
        source = SourceRecord(
            source_id="mock-topic",
            title=f"{topic} 主题资料",
            url="https://example.com/zhiguan/mock-source",
            publisher="知关 AI 示例资料",
            excerpt=f"这是用于测试和离线演示的主题资料：{topic}。该资料不代表实时事实。",
        )
        return EvidenceBundle(
            sources=[source] if require_fresh else [],
            freshness=FreshnessStatus.fresh if require_fresh else FreshnessStatus.offline,
            provider="mock",
        )


class TavilySearchProvider:
    def search(self, topic: str, *, require_fresh: bool) -> EvidenceBundle:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": topic,
                "search_depth": "advanced" if require_fresh else "basic",
                "max_results": SEARCH_MAX_RESULTS,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        records = [
            SourceRecord(
                source_id=f"tavily-{index}",
                title=str(item.get("title", "未命名来源")),
                url=str(item["url"]),
                publisher=str(item.get("url", "").split("/")[2] if item.get("url") else ""),
                excerpt=str(item.get("content", "")),
            )
            for index, item in enumerate(payload.get("results", []))
            if item.get("url") and item.get("content")
        ]
        return normalize_sources(
            records,
            max_results=SEARCH_MAX_RESULTS,
            max_age_days=SEARCH_MAX_AGE_DAYS,
            require_fresh=require_fresh,
            provider="tavily",
        )
