from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select

from .db import GameSessionRecord, create_session_factory
from .evidence import EvidenceBundle, FreshnessStatus, GenerationMode
from .models import Difficulty, PublicQuestion, QuestionAnswer, QuestionType, SessionStatus


@dataclass
class Question:
    question_id: str
    question_type: QuestionType
    knowledge_point: str
    difficulty: Difficulty
    stem: str
    options: list[dict[str, str]]
    answer: str
    explanation: str
    evidence: EvidenceBundle | None = None
    generation_mode: GenerationMode = GenerationMode.offline

    def public(self) -> PublicQuestion:
        return PublicQuestion(
            questionId=self.question_id,
            type=self.question_type,
            knowledgePoint=self.knowledge_point,
            difficulty=self.difficulty,
            stem=self.stem,
            options=self.options,
            sources=self.evidence.sources if self.evidence else [],
            freshness=self.evidence.freshness if self.evidence else FreshnessStatus.offline,
            generationMode=self.generation_mode,
        )


@dataclass
class AnswerRecord:
    question_id: str
    answer: str
    is_correct: bool
    feedback: QuestionAnswer
    client_request_id: str


@dataclass
class Session:
    session_id: str
    topic: str
    difficulty: Difficulty
    question_count: int
    question_types: list[QuestionType]
    status: SessionStatus
    current_index: int = 0
    score: int = 0
    life: int = 3
    questions: list[Question] = field(default_factory=list)
    answers: list[AnswerRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str | None = None


class SessionStore(Protocol):
    def save(self, session: Session) -> None: ...
    def get(self, session_id: str) -> Session | None: ...
    def list_for_user(self, user_id: str) -> list[Session]: ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}

    def save(self, session: Session) -> None:
        self.sessions[session.session_id] = session

    def get(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    def list_for_user(self, user_id: str) -> list[Session]:
        return sorted(
            (session for session in self.sessions.values() if session.user_id == user_id),
            key=lambda session: session.created_at,
            reverse=True,
        )


class SqlAlchemySessionStore:
    def __init__(self) -> None:
        self.session_factory = create_session_factory()

    def save(self, session: Session) -> None:
        payload = {
            "topic": session.topic,
            "difficulty": session.difficulty.value,
            "question_count": session.question_count,
            "current_index": session.current_index,
            "score": session.score,
            "life": session.life,
            "status": session.status.value,
            "state_json": {
                "question_types": [item.value for item in session.question_types],
                "questions": [self._question_to_dict(item) for item in session.questions],
                "answers": [self._answer_to_dict(item) for item in session.answers],
            },
            "created_at": session.created_at.replace(tzinfo=None),
            "user_id": session.user_id,
        }
        with self.session_factory.begin() as database:
            record = database.get(GameSessionRecord, session.session_id)
            if record is None:
                database.add(GameSessionRecord(id=session.session_id, **payload))
            else:
                for key, value in payload.items():
                    setattr(record, key, value)

    def get(self, session_id: str) -> Session | None:
        with self.session_factory() as database:
            record = database.scalar(select(GameSessionRecord).where(GameSessionRecord.id == session_id))
        if record is None:
            return None
        state = record.state_json
        return Session(
            session_id=record.id,
            topic=record.topic,
            difficulty=Difficulty(record.difficulty),
            question_count=record.question_count,
            question_types=[QuestionType(item) for item in state["question_types"]],
            status=SessionStatus(record.status),
            current_index=record.current_index,
            score=record.score,
            life=record.life,
            questions=[self._question_from_dict(item) for item in state["questions"]],
            answers=[self._answer_from_dict(item) for item in state["answers"]],
            created_at=record.created_at.replace(tzinfo=timezone.utc),
            user_id=record.user_id,
        )

    def list_for_user(self, user_id: str) -> list[Session]:
        with self.session_factory() as database:
            records = database.scalars(
                select(GameSessionRecord)
                .where(GameSessionRecord.user_id == user_id)
                .order_by(GameSessionRecord.created_at.desc())
            ).all()
        return [self._record_to_session(record) for record in records]

    def _record_to_session(self, record: GameSessionRecord) -> Session:
        state = record.state_json
        return Session(
            session_id=record.id,
            topic=record.topic,
            difficulty=Difficulty(record.difficulty),
            question_count=record.question_count,
            question_types=[QuestionType(item) for item in state["question_types"]],
            status=SessionStatus(record.status),
            current_index=record.current_index,
            score=record.score,
            life=record.life,
            questions=[self._question_from_dict(item) for item in state["questions"]],
            answers=[self._answer_from_dict(item) for item in state["answers"]],
            created_at=record.created_at.replace(tzinfo=timezone.utc),
            user_id=record.user_id,
        )

    @staticmethod
    def _question_to_dict(question: Question) -> dict:
        return {
            **question.__dict__,
            "question_type": question.question_type.value,
            "difficulty": question.difficulty.value,
            "evidence": question.evidence.model_dump(mode="json") if question.evidence else None,
            "generation_mode": question.generation_mode.value,
        }

    @staticmethod
    def _question_from_dict(payload: dict) -> Question:
        from .evidence import EvidenceBundle

        evidence = EvidenceBundle.model_validate(payload["evidence"]) if payload.get("evidence") else None
        return Question(**{
            **payload,
            "question_type": QuestionType(payload["question_type"]),
            "difficulty": Difficulty(payload["difficulty"]),
            "evidence": evidence,
            "generation_mode": GenerationMode(payload.get("generation_mode", "offline")),
        })

    @staticmethod
    def _answer_to_dict(answer: AnswerRecord) -> dict:
        return {**answer.__dict__, "feedback": answer.feedback.model_dump()}

    @staticmethod
    def _answer_from_dict(payload: dict) -> AnswerRecord:
        return AnswerRecord(**{**payload, "feedback": QuestionAnswer.model_validate(payload["feedback"])})
