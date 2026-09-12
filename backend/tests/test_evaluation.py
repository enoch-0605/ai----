from app.ai import MockAIService
from app.models import Difficulty, QuestionType


def test_deterministic_quality_fixture_reports_source_coverage():
    service = MockAIService()
    stable = service.generate_question("牛顿第二定律", 0, Difficulty.beginner, [QuestionType.single_choice], None)
    current = service.generate_question("Python 3.14 最新版本", 0, Difficulty.beginner, [QuestionType.single_choice], None)
    assert stable.generation_mode.value == "offline"
    assert current.generation_mode.value == "online"
    assert current.evidence is not None and current.evidence.sources
