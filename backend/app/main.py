from fastapi import Depends, FastAPI, Header
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
    HistoryItem,
    LearningOverview,
    LoginRequest,
    LoginResponse,
    MistakeItem,
    UserProfile,
)
from .service import GameService
from .store import InMemorySessionStore, SqlAlchemySessionStore
from .users import User, UserService

store = SqlAlchemySessionStore() if STORAGE == "sqlalchemy" else InMemorySessionStore()
ai_service = LangChainAIService() if AI_PROVIDER == "deepseek" else MockAIService()
game_service = GameService(store, ai_service)
user_service = UserService(store)

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


def current_user(authorization: str | None = Header(default=None)) -> User:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    return user_service.authenticate(token)


def optional_user(authorization: str | None = Header(default=None)) -> User | None:
    if not authorization:
        return None
    return current_user(authorization)


@app.post("/api/v1/auth/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    user, token = user_service.login(request.provider, request.code, request.anonymousSessionId)
    return LoginResponse(token=token, user=UserProfile(userId=user.user_id, nickname=user.nickname, avatarUrl=user.avatar_url))


@app.get("/api/v1/auth/me", response_model=UserProfile)
def me(user: User = Depends(current_user)) -> UserProfile:
    return UserProfile(userId=user.user_id, nickname=user.nickname, avatarUrl=user.avatar_url)


@app.get("/api/v1/assets/overview", response_model=LearningOverview)
def assets_overview(user: User = Depends(current_user)) -> LearningOverview:
    return LearningOverview(**user_service.overview(user))


@app.get("/api/v1/assets/history", response_model=list[HistoryItem])
def assets_history(user: User = Depends(current_user)) -> list[HistoryItem]:
    return [HistoryItem(**item) for item in user_service.history(user)]


@app.get("/api/v1/assets/mistakes", response_model=list[MistakeItem])
def assets_mistakes(user: User = Depends(current_user)) -> list[MistakeItem]:
    return [MistakeItem(**item) for item in user_service.mistakes(user)]


@app.post("/api/v1/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest, user: User | None = Depends(optional_user)) -> CreateSessionResponse:
    user_id = None
    if user is not None:
        user_id = user.user_id
    return game_service.create_session(request, user_id)


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
