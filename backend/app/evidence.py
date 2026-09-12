from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class FreshnessStatus(str, Enum):
    offline = "offline"
    fresh = "fresh"
    stale = "stale"
    unavailable = "unavailable"


class GenerationMode(str, Enum):
    online = "online"
    offline = "offline"
    template = "template"


class SourceRecord(BaseModel):
    source_id: str
    title: str = Field(min_length=1, max_length=300)
    url: str
    publisher: str = ""
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    excerpt: str = Field(min_length=1, max_length=4000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source URL must be an absolute HTTP(S) URL")
        return value


class EvidenceBundle(BaseModel):
    sources: list[SourceRecord] = Field(default_factory=list, max_length=5)
    freshness: FreshnessStatus
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider: str = "mock"


def topic_requires_fresh_evidence(topic: str) -> bool:
    patterns = (
        r"\b20\d{2}\b",
        r"(最新|当前|近期|今天|本周|本月|今年|政策|法规|价格|版本|发布|新闻|时事|天气)",
        r"\b(v\d+(?:\.\d+)+|version)\b",
    )
    return bool(topic.strip()) and any(re.search(pattern, topic, re.IGNORECASE) for pattern in patterns)


def normalize_sources(
    records: Iterable[SourceRecord],
    *,
    max_results: int,
    max_age_days: int,
    require_fresh: bool,
    provider: str = "normalized",
) -> EvidenceBundle:
    now = datetime.now(timezone.utc)
    sources: list[SourceRecord] = []
    seen_urls: set[str] = set()
    for record in records:
        if record.url in seen_urls or not record.excerpt.strip():
            continue
        seen_urls.add(record.url)
        if require_fresh and record.published_at:
            age_days = (now - record.published_at.astimezone(timezone.utc)).days
            if age_days > max_age_days:
                continue
        sources.append(record)
        if len(sources) >= max_results:
            break
    freshness = FreshnessStatus.fresh if sources and require_fresh else (
        FreshnessStatus.offline if not require_fresh else FreshnessStatus.unavailable
    )
    return EvidenceBundle(sources=sources, freshness=freshness, provider=provider)


def validate_citations(
    citation_ids: list[str],
    evidence: EvidenceBundle | None,
    require_citation: bool,
) -> None:
    if evidence is None:
        if citation_ids:
            raise ValueError("EVIDENCE_UNSUPPORTED")
        return
    valid_ids = {source.source_id for source in evidence.sources}
    if require_citation and not citation_ids:
        raise ValueError("EVIDENCE_UNSUPPORTED")
    if any(item not in valid_ids for item in citation_ids):
        raise ValueError("EVIDENCE_UNSUPPORTED")


def validate_question_output(
    *,
    question_type: str,
    options: list[dict[str, str]],
    answer: str,
    stem: str,
    explanation: str,
    citation_ids: list[str],
    evidence: EvidenceBundle | None,
) -> None:
    expected_count = 2 if question_type == "true_false" else 4
    if not stem.strip() or not explanation.strip() or len(options) != expected_count:
        raise ValueError("AI_OUTPUT_INVALID")
    option_ids = [item.get("id", "") for item in options]
    if len(set(option_ids)) != len(option_ids) or answer not in option_ids:
        raise ValueError("AI_OUTPUT_INVALID")
    validate_citations(citation_ids, evidence, bool(evidence and evidence.freshness == FreshnessStatus.fresh))
