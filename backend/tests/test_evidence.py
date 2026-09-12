from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.evidence import (
    EvidenceBundle,
    FreshnessStatus,
    SourceRecord,
    normalize_sources,
    topic_requires_fresh_evidence,
    validate_question_output,
)


def test_current_topic_detection_and_source_deduplication():
    assert topic_requires_fresh_evidence("Python 3.14 最新版本")
    source = SourceRecord(
        source_id="one",
        title="Source",
        url="https://example.com/source",
        excerpt="Current information",
    )
    bundle = normalize_sources([source, source], max_results=5, max_age_days=30, require_fresh=True)
    assert bundle.freshness == FreshnessStatus.fresh
    assert len(bundle.sources) == 1


def test_stale_sources_are_removed_for_current_topics():
    source = SourceRecord(
        source_id="old",
        title="Old",
        url="https://example.com/old",
        published_at=datetime.now(timezone.utc) - timedelta(days=60),
        excerpt="Old information",
    )
    bundle = normalize_sources([source], max_results=5, max_age_days=30, require_fresh=True)
    assert bundle.freshness == FreshnessStatus.unavailable
    assert bundle.sources == []


def test_question_output_requires_valid_options_and_citations():
    evidence = EvidenceBundle(
        sources=[SourceRecord(source_id="s1", title="Source", url="https://example.com", excerpt="Fact")],
        freshness=FreshnessStatus.fresh,
    )
    validate_question_output(
        question_type="single_choice",
        options=[{"id": "A", "text": "one"}, {"id": "B", "text": "two"}, {"id": "C", "text": "three"}, {"id": "D", "text": "four"}],
        answer="A",
        stem="Which answer?",
        explanation="A is supported.",
        citation_ids=["s1"],
        evidence=evidence,
    )
    with pytest.raises(ValueError, match="EVIDENCE_UNSUPPORTED"):
        validate_question_output(
            question_type="single_choice",
            options=[{"id": "A", "text": "one"}, {"id": "B", "text": "two"}, {"id": "C", "text": "three"}, {"id": "D", "text": "four"}],
            answer="A",
            stem="Which answer?",
            explanation="Unsupported.",
            citation_ids=[],
            evidence=evidence,
        )


def test_offline_question_output_does_not_require_evidence():
    validate_question_output(
        question_type="single_choice",
        options=[
            {"id": "A", "text": "正确"},
            {"id": "B", "text": "错误"},
            {"id": "C", "text": "无关"},
            {"id": "D", "text": "未知"},
        ],
        answer="A",
        stem="稳定主题题目",
        explanation="离线生成的基础解析",
        citation_ids=[],
        evidence=None,
    )
