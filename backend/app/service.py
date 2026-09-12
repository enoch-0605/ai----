from uuid import uuid4

from fastapi import HTTPException, status

from .ai import AIQuestionService
from .models import (
    CreateSessionRequest,
    CreateSessionResponse,
    LearningReport,
    PublicQuestion,
    QuestionAnswer,
    SessionResponse,
    SessionStatus,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from .store import AnswerRecord, Question, Session, SessionStore
from .metrics import GenerationTimer, generation_event


class GameService:
    def __init__(self, store: SessionStore, ai: AIQuestionService) -> None:
        self.store = store
        self.ai = ai

    def create_session(self, request: CreateSessionRequest, user_id: str | None = None) -> CreateSessionResponse:
        session_id = f"s_{uuid4().hex}"
        session = Session(
            session_id=session_id,
            topic=request.topic,
            difficulty=request.difficulty,
            question_count=request.questionCount,
            question_types=request.questionTypes,
            status=SessionStatus.playing,
            user_id=user_id,
        )
        question = self._generate_question(session, None)
        session.questions.append(question)
        self.store.save(session)
        return self._create_response(session, question)

    def get_session(self, session_id: str) -> SessionResponse:
        session = self._require_session(session_id)
        question = session.questions[session.current_index] if session.status != SessionStatus.completed else None
        feedback = session.answers[-1].feedback if session.answers and session.status == SessionStatus.feedback else None
        return SessionResponse(
            sessionId=session.session_id,
            status=session.status,
            currentIndex=session.current_index,
            totalQuestions=session.question_count,
            score=session.score,
            life=session.life,
            question=question.public() if question else None,
            feedback=feedback,
        )

    def submit_answer(self, session_id: str, request: SubmitAnswerRequest) -> SubmitAnswerResponse:
        session = self._require_session(session_id)
        if session.status == SessionStatus.completed:
            raise HTTPException(status_code=409, detail="ANSWER_ALREADY_SUBMITTED")
        if session.status == SessionStatus.feedback:
            duplicate = next((item for item in session.answers if item.client_request_id == request.clientRequestId), None)
            if duplicate:
                return self._submit_response(session, duplicate.feedback, self._next_question(session))
            raise HTTPException(status_code=409, detail="ANSWER_ALREADY_SUBMITTED")

        current = session.questions[session.current_index]
        if current.question_id != request.questionId:
            raise HTTPException(status_code=409, detail="QUESTION_OUT_OF_DATE")
        if any(item.client_request_id == request.clientRequestId for item in session.answers):
            duplicate = next(item for item in session.answers if item.client_request_id == request.clientRequestId)
            return self._submit_response(session, duplicate.feedback, self._next_question(session))

        is_correct = request.answer.upper() == current.answer.upper()
        if is_correct:
            session.score += 1
        else:
            session.life = max(0, session.life - 1)
        feedback = QuestionAnswer(
            answer=request.answer,
            isCorrect=is_correct,
            explanation=current.explanation,
            encouragement="回答正确，继续保持！" if is_correct else "别急，理解解析后再试一次相关知识点。",
            sources=current.evidence.sources if current.evidence else [],
        )
        record = AnswerRecord(current.question_id, request.answer, is_correct, feedback, request.clientRequestId)
        session.answers.append(record)
        self._adjust_difficulty(session)
        if session.current_index + 1 >= session.question_count:
            session.status = SessionStatus.completed
            self.store.save(session)
            return self._submit_response(session, feedback, None)

        session.status = SessionStatus.feedback
        self.store.save(session)
        return self._submit_response(session, feedback, self._next_question(session))

    def continue_after_feedback(self, session_id: str) -> SessionResponse:
        session = self._require_session(session_id)
        if session.status == SessionStatus.completed:
            return self.get_session(session_id)
        if session.status != SessionStatus.feedback:
            return self.get_session(session_id)
        previous = session.answers[-1].is_correct
        session.current_index += 1
        session.status = SessionStatus.playing
        if len(session.questions) <= session.current_index:
            session.questions.append(self._generate_question(session, previous))
        self.store.save(session)
        return self.get_session(session_id)

    def report(self, session_id: str) -> LearningReport:
        session = self._require_session(session_id)
        if session.status != SessionStatus.completed:
            raise HTTPException(status_code=409, detail="SESSION_NOT_COMPLETED")
        data = self.ai.generate_report(session.topic, [{"is_correct": item.is_correct} for item in session.answers])
        sources = []
        for question in session.questions:
            if question.evidence:
                sources.extend(question.evidence.sources)
        unique_sources = {source.source_id: source for source in sources}
        freshness = next(
            (question.evidence.freshness for question in session.questions if question.evidence),
            None,
        )
        return LearningReport(
            sessionId=session.session_id,
            score=session.score,
            totalQuestions=session.question_count,
            accuracy=data["accuracy"],
            summary=data["summary"],
            strengths=data["strengths"],
            weaknesses=data["weaknesses"],
            recommendations=data["recommendations"],
            sources=list(unique_sources.values()),
            freshness=freshness or "offline",
        )

    def _generate_question(self, session: Session, previous_correct: bool | None) -> Question:
        timer = GenerationTimer()
        try:
            generated = self.ai.generate_question(
                session.topic,
                len(session.questions),
                session.difficulty,
                session.question_types,
                previous_correct,
            )
        except (TimeoutError, ValueError) as error:
            detail = str(error) or "AI_OUTPUT_INVALID"
            generation_event(event="question_generation", session_id=session.session_id, provider="configured", status=detail, latency_ms=timer.elapsed_ms)
            raise HTTPException(status_code=503, detail=detail) from error
        generation_event(
            event="question_generation",
            session_id=session.session_id,
            provider=generated.evidence.provider if generated.evidence else "offline",
            status="success",
            evidence_count=len(generated.evidence.sources) if generated.evidence else 0,
            freshness=generated.evidence.freshness.value if generated.evidence else "offline",
            latency_ms=timer.elapsed_ms,
        )
        return Question(
            question_id=f"q_{uuid4().hex}",
            question_type=generated.question_type,
            knowledge_point=generated.knowledge_point,
            difficulty=generated.difficulty,
            stem=generated.stem,
            options=generated.options,
            answer=generated.answer,
            explanation=generated.explanation,
            evidence=generated.evidence,
            generation_mode=generated.generation_mode,
        )

    def _adjust_difficulty(self, session: Session) -> None:
        if len(session.answers) < 2:
            return
        recent = [answer.is_correct for answer in session.answers[-2:]]
        levels = ["beginner", "advanced", "expert"]
        current = levels.index(session.difficulty.value)
        if recent == [True, True]:
            session.difficulty = type(session.difficulty)(levels[min(current + 1, 2)])
        elif recent == [False, False]:
            session.difficulty = type(session.difficulty)(levels[max(current - 1, 0)])

    def _next_question(self, session: Session) -> PublicQuestion | None:
        if session.current_index + 1 >= session.question_count:
            return None
        if len(session.questions) <= session.current_index + 1:
            session.questions.append(self._generate_question(session, session.answers[-1].is_correct))
        return session.questions[session.current_index + 1].public()

    def _create_response(self, session: Session, question: Question) -> CreateSessionResponse:
        return CreateSessionResponse(
            sessionId=session.session_id,
            status=session.status,
            currentIndex=session.current_index,
            totalQuestions=session.question_count,
            score=session.score,
            life=session.life,
            question=question.public(),
        )

    def _submit_response(self, session: Session, feedback: QuestionAnswer, next_question: PublicQuestion | None) -> SubmitAnswerResponse:
        return SubmitAnswerResponse(
            sessionId=session.session_id,
            status=session.status,
            currentIndex=session.current_index,
            totalQuestions=session.question_count,
            score=session.score,
            life=session.life,
            feedback=feedback,
            nextQuestion=next_question,
        )

    def _require_session(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")
        return session
