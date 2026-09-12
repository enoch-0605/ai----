from dataclasses import dataclass
from typing import Protocol

import httpx

from .models import Difficulty, QuestionType
from .config import CURRENT_TOPIC_REQUIRES_SEARCH, SEARCH_PROVIDER
from .config import AI_RETRY_ATTEMPTS
from .evidence import (
    EvidenceBundle,
    FreshnessStatus,
    GenerationMode,
    topic_requires_fresh_evidence,
    validate_question_output,
)
from .search import MockSearchProvider, SearchProvider, TavilySearchProvider


@dataclass
class GeneratedQuestion:
    question_type: QuestionType
    knowledge_point: str
    difficulty: Difficulty
    stem: str
    options: list[dict[str, str]]
    answer: str
    explanation: str
    evidence: EvidenceBundle | None = None
    generation_mode: GenerationMode = GenerationMode.offline


class AIQuestionService(Protocol):
    def generate_question(
        self,
        topic: str,
        question_index: int,
        difficulty: Difficulty,
        question_types: list[QuestionType],
        previous_correct: bool | None,
    ) -> GeneratedQuestion: ...

    def generate_report(self, topic: str, answers: list[dict]) -> dict: ...


class MockAIService:
    def __init__(self, search: SearchProvider | None = None) -> None:
        self.search = search or MockSearchProvider()

    def generate_question(
        self,
        topic: str,
        question_index: int,
        difficulty: Difficulty,
        question_types: list[QuestionType],
        previous_correct: bool | None,
    ) -> GeneratedQuestion:
        question_type = question_types[question_index % len(question_types)]
        require_fresh = CURRENT_TOPIC_REQUIRES_SEARCH and topic_requires_fresh_evidence(topic)
        evidence = self.search.search(topic, require_fresh=require_fresh) if require_fresh else None
        if require_fresh and (not evidence.sources or evidence.freshness != FreshnessStatus.fresh):
            raise ValueError("SEARCH_NO_EVIDENCE")
        if question_type == QuestionType.true_false:
            return GeneratedQuestion(
                question_type=question_type,
                knowledge_point=f"{topic}核心概念",
                difficulty=difficulty,
                stem=f"关于“{topic}”的基础描述是否正确？",
                options=[{"id": "A", "text": "正确"}, {"id": "B", "text": "错误"}],
                answer="A",
                explanation="这是根据当前主题核心概念设计的判断题，建议结合定义进行复习。",
                evidence=evidence,
                generation_mode=GenerationMode.online if evidence else GenerationMode.offline,
            )
        return GeneratedQuestion(
            question_type=question_type,
            knowledge_point=f"{topic}核心概念",
            difficulty=difficulty,
            stem=f"下面哪一项最符合“{topic}”的核心概念？",
            options=[
                {"id": "A", "text": "核心概念的准确描述"},
                {"id": "B", "text": "与主题无关的干扰项"},
                {"id": "C", "text": "常见但不完整的理解"},
                {"id": "D", "text": "与概念相反的说法"},
            ],
            answer="A",
            explanation="核心概念需要结合定义、边界和应用场景一起理解。",
            evidence=evidence,
            generation_mode=GenerationMode.online if evidence else GenerationMode.offline,
        )

    def generate_report(self, topic: str, answers: list[dict]) -> dict:
        correct = sum(1 for answer in answers if answer["is_correct"])
        total = len(answers)
        accuracy = round(correct / total * 100) if total else 0
        return {
            "summary": f"你完成了“{topic}”的学习挑战，基础理解已经形成。",
            "strengths": ["核心概念识别"],
            "weaknesses": ["需要继续巩固题目解析"],
            "recommendations": ["复习错题并再次挑战相同知识点"],
            "accuracy": accuracy,
        }


class LangChainAIService:
    def __init__(self) -> None:
        from .ai_langchain import DeepSeekQuestionChain

        self.search: SearchProvider = TavilySearchProvider() if SEARCH_PROVIDER == "tavily" else MockSearchProvider()
        self.question_chain = DeepSeekQuestionChain()
        self.report_service = MockAIService()

    def generate_question(
        self,
        topic: str,
        question_index: int,
        difficulty: Difficulty,
        question_types: list[QuestionType],
        previous_correct: bool | None,
    ) -> GeneratedQuestion:
        question_type = question_types[question_index % len(question_types)]
        require_fresh = CURRENT_TOPIC_REQUIRES_SEARCH and topic_requires_fresh_evidence(topic)
        evidence = self._search(topic, require_fresh) if require_fresh else None
        if require_fresh and (not evidence or not evidence.sources or evidence.freshness != FreshnessStatus.fresh):
            raise ValueError("SEARCH_NO_EVIDENCE")
        result = None
        last_error: Exception | None = None
        for _ in range(max(1, AI_RETRY_ATTEMPTS)):
            try:
                result = self.question_chain.invoke(
                    topic, difficulty.value, question_type.value, question_index + 1,
                    evidence_text="\n".join(f"[{source.source_id}] {source.excerpt}" for source in evidence.sources) if evidence else "",
                )
                validate_question_output(
                    question_type=result.question_type,
                    options=result.options,
                    answer=result.answer,
                    stem=result.stem,
                    explanation=result.explanation,
                    citation_ids=result.citation_ids,
                    evidence=evidence,
                )
                break
            except (TimeoutError, ValueError) as error:
                last_error = error
        if result is None:
            raise last_error or ValueError("AI_OUTPUT_INVALID")
        return GeneratedQuestion(
            question_type=QuestionType(result.question_type),
            knowledge_point=result.knowledge_point,
            difficulty=Difficulty(result.difficulty),
            stem=result.stem,
            options=result.options,
            answer=result.answer,
            explanation=result.explanation,
            evidence=evidence,
            generation_mode=GenerationMode.online if evidence else GenerationMode.offline,
        )

    def _search(self, topic: str, require_fresh: bool) -> EvidenceBundle:
        last_error: Exception | None = None
        for _ in range(max(1, AI_RETRY_ATTEMPTS)):
            try:
                return self.search.search(topic, require_fresh=require_fresh)
            except (TimeoutError, OSError, httpx.TimeoutException) as error:
                last_error = error
        raise ValueError("SEARCH_TIMEOUT") from last_error

    def generate_report(self, topic: str, answers: list[dict]) -> dict:
        return self.report_service.generate_report(topic, answers)
