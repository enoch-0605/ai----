from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

from fastapi import HTTPException

from .store import Session, SessionStore
from .config import WECHAT_APPID, WECHAT_APPSECRET


@dataclass
class User:
    user_id: str
    nickname: str
    avatar_url: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UserService:
    def __init__(self, sessions: SessionStore) -> None:
        self.sessions = sessions
        self.users: dict[str, User] = {}
        self.tokens: dict[str, str] = {}

    def login(self, provider: str, code: str, anonymous_session_id: str | None = None) -> tuple[User, str]:
        if provider not in {"mock", "wechat"}:
            raise HTTPException(status_code=400, detail="INVALID_ARGUMENT")
        if not code.strip():
            raise HTTPException(status_code=422, detail="INVALID_ARGUMENT")

        identity = self._resolve_identity(provider, code.strip())
        user_id = next((user_id for user_id, token in self.tokens.items() if token == identity), None)
        if user_id is None:
            user_id = f"u_{uuid4().hex}"
            self.users[user_id] = User(user_id=user_id, nickname="学习用户")
            self.tokens[user_id] = identity

        user = self.users[user_id]
        if anonymous_session_id:
            session = self.sessions.get(anonymous_session_id)
            if session is not None and session.user_id is None:
                session.user_id = user.user_id
                self.sessions.save(session)
        return user, identity

    @staticmethod
    def _resolve_identity(provider: str, code: str) -> str:
        if provider == "mock":
            return f"mock:{code}"
        if not WECHAT_APPID or not WECHAT_APPSECRET:
            raise HTTPException(status_code=503, detail="WECHAT_NOT_CONFIGURED")

        query = urlencode({
            "appid": WECHAT_APPID,
            "secret": WECHAT_APPSECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        })
        try:
            with urlopen(f"https://api.weixin.qq.com/sns/jscode2session?{query}", timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except OSError as error:
            raise HTTPException(status_code=502, detail="WECHAT_REQUEST_FAILED") from error

        if payload.get("errcode"):
            raise HTTPException(status_code=401, detail=f"WECHAT_LOGIN_FAILED:{payload['errcode']}")
        openid = payload.get("openid")
        if not openid:
            raise HTTPException(status_code=502, detail="WECHAT_RESPONSE_INVALID")
        return f"wechat:{openid}"

    def authenticate(self, token: str | None) -> User:
        user_id = next((key for key, value in self.tokens.items() if value == token), None)
        if user_id is None or user_id not in self.users:
            raise HTTPException(status_code=401, detail="AUTH_REQUIRED")
        return self.users[user_id]

    def overview(self, user: User) -> dict:
        sessions = self.sessions.list_for_user(user.user_id)
        completed = [item for item in sessions if item.status.value == "completed"]
        answers = [answer for item in completed for answer in item.answers]
        wrong = [answer for answer in answers if not answer.is_correct]
        return {
            "completedCount": len(completed),
            "averageAccuracy": round(sum(item.score for item in completed) / sum(item.question_count for item in completed) * 100) if completed else 0,
            "totalMinutes": 0,
            "wrongCount": len(wrong),
        }

    def history(self, user: User) -> list[dict]:
        return [
            {
                "sessionId": session.session_id,
                "topic": session.topic,
                "status": session.status.value,
                "score": session.score,
                "totalQuestions": session.question_count,
                "accuracy": round(session.score / session.question_count * 100),
                "updatedAt": session.created_at.isoformat(),
            }
            for session in self.sessions.list_for_user(user.user_id)
        ]

    def mistakes(self, user: User) -> list[dict]:
        items: list[dict] = []
        for session in self.sessions.list_for_user(user.user_id):
            for answer in session.answers:
                if not answer.is_correct:
                    question = next((item for item in session.questions if item.question_id == answer.question_id), None)
                    if question:
                        items.append({
                            "questionId": question.question_id,
                            "sessionId": session.session_id,
                            "topic": session.topic,
                            "knowledgePoint": question.knowledge_point,
                            "difficulty": question.difficulty.value,
                            "reason": answer.feedback.explanation,
                            "status": "pending",
                        })
        return items
