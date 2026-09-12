from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    beginner = "beginner"
    advanced = "advanced"
    expert = "expert"


class QuestionType(str, Enum):
    single_choice = "single_choice"
    true_false = "true_false"


class SessionStatus(str, Enum):
    playing = "playing"
    feedback = "feedback"
    completed = "completed"
    failed = "failed"


class QuestionOption(BaseModel):
    id: str
    text: str


class PublicQuestion(BaseModel):
    questionId: str
    type: QuestionType
    knowledgePoint: str
    difficulty: Difficulty
    stem: str
    options: list[QuestionOption]


class QuestionAnswer(BaseModel):
    answer: str
    isCorrect: bool
    explanation: str
    encouragement: str


class CreateSessionRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    questionCount: Literal[5, 10] = 5
    difficulty: Difficulty = Difficulty.beginner
    questionTypes: list[QuestionType] = [QuestionType.single_choice, QuestionType.true_false]


class CreateSessionResponse(BaseModel):
    sessionId: str
    status: SessionStatus
    currentIndex: int
    totalQuestions: int
    score: int
    life: int
    question: PublicQuestion


class SessionResponse(BaseModel):
    sessionId: str
    status: SessionStatus
    currentIndex: int
    totalQuestions: int
    score: int
    life: int
    question: PublicQuestion | None = None
    feedback: QuestionAnswer | None = None


class SubmitAnswerRequest(BaseModel):
    questionId: str
    answer: str = Field(min_length=1, max_length=20)
    clientRequestId: str = Field(min_length=1, max_length=100)


class SubmitAnswerResponse(BaseModel):
    sessionId: str
    status: SessionStatus
    currentIndex: int
    totalQuestions: int
    score: int
    life: int
    feedback: QuestionAnswer
    nextQuestion: PublicQuestion | None = None


class LearningReport(BaseModel):
    sessionId: str
    score: int
    totalQuestions: int
    accuracy: int
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    disclaimer: str = "AI 生成内容仅供学习参考。"


class FeedbackRequest(BaseModel):
    questionId: str
    reason: str = Field(min_length=1, max_length=500)
