import logging
from time import monotonic

logger = logging.getLogger("zhiguan.generation")


def generation_event(
    *,
    event: str,
    session_id: str | None,
    provider: str,
    status: str,
    evidence_count: int = 0,
    freshness: str = "offline",
    retry_count: int = 0,
    latency_ms: int | None = None,
) -> None:
    logger.info(
        "generation_event event=%s session_id=%s provider=%s status=%s "
        "evidence_count=%d freshness=%s retry_count=%d latency_ms=%s",
        event,
        session_id or "-",
        provider,
        status,
        evidence_count,
        freshness,
        retry_count,
        latency_ms if latency_ms is not None else "-",
    )


class GenerationTimer:
    def __init__(self) -> None:
        self.started_at = monotonic()

    @property
    def elapsed_ms(self) -> int:
        return round((monotonic() - self.started_at) * 1000)
