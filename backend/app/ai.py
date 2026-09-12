from dataclasses import dataclass
from typing import Protocol

from .models import Difficulty, QuestionType


@dataclass
class GeneratedQuestion:
    question_type: QuestionType
    knowledge_point: str
    difficulty: Difficulty
    stem: str
    options: list[dict[str, str]]
    answer: str
    explanation: str


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
    def generate_question(
        self,
        topic: str,
        question_index: int,
        difficulty: Difficulty,
        question_types: list[QuestionType],
        previous_correct: bool | None,
    ) -> GeneratedQuestion:
        question_type = question_types[question_index % len(question_types)]
        if question_type == QuestionType.true_false:
            return GeneratedQuestion(
                question_type=question_type,
                knowledge_point=f"{topic}核心概念",
                difficulty=difficulty,
                stem=f"关于“{topic}”的基础描述是否正确？",
                options=[{"id": "A", "text": "正确"}, {"id": "B", "text": "错误"}],
                answer="A",
                explanation="这是根据当前主题核心概念设计的判断题，建议结合定义进行复习。",
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
        result = self.question_chain.invoke(topic, difficulty.value, question_type.value, question_index + 1)
        return GeneratedQuestion(
            question_type=QuestionType(result.question_type),
            knowledge_point=result.knowledge_point,
            difficulty=Difficulty(result.difficulty),
            stem=result.stem,
            options=result.options,
            answer=result.answer,
            explanation=result.explanation,
        )

    def generate_report(self, topic: str, answers: list[dict]) -> dict:
        return self.report_service.generate_report(topic, answers)
