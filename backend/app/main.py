from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai import LangChainAIService, MockAIService
from .config import AI_PROVIDER, STORAGE
from .models import (
    CreateSessionRequest,
    CreateSessionResponse,
    FeedbackRequest,
    LearningReport,
    SessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from .service import GameService
from .store import InMemorySessionStore, SqlAlchemySessionStore

store = SqlAlchemySessionStore() if STORAGE == "sqlalchemy" else InMemorySessionStore()
ai_service = LangChainAIService() if AI_PROVIDER == "deepseek" else MockAIService()
game_service = GameService(store, ai_service)

app = FastAPI(title="知关 AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    return game_service.create_session(request)


@app.get("/api/v1/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    return game_service.get_session(session_id)


@app.post("/api/v1/sessions/{session_id}/answers", response_model=SubmitAnswerResponse)
def submit_answer(session_id: str, request: SubmitAnswerRequest) -> SubmitAnswerResponse:
    return game_service.submit_answer(session_id, request)


@app.post("/api/v1/sessions/{session_id}/continue", response_model=SessionResponse)
def continue_session(session_id: str) -> SessionResponse:
    return game_service.continue_after_feedback(session_id)


@app.post("/api/v1/sessions/{session_id}/reports", response_model=LearningReport)
def create_report(session_id: str) -> LearningReport:
    return game_service.report(session_id)


@app.post("/api/v1/feedback")
def report_feedback(request: FeedbackRequest) -> dict[str, str]:
    return {"status": "received", "questionId": request.questionId}
