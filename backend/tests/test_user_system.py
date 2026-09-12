from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login():
    response = client.post("/api/v1/auth/login", json={"provider": "mock", "code": "test-user"})
    assert response.status_code == 200
    return response.json()


def test_login_and_profile():
    payload = login()
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['token']}"})
    assert response.status_code == 200
    assert response.json()["userId"] == payload["user"]["userId"]
    assert response.json()["nickname"] == "学习用户"


def test_assets_require_authentication():
    response = client.get("/api/v1/assets/history")
    assert response.status_code == 401
    assert response.json()["detail"] == "AUTH_REQUIRED"


def test_session_is_bound_and_history_is_available_after_login():
    session = client.post("/api/v1/sessions", json={"topic": "历史"}).json()
    payload = login()
    bound = client.post(
        "/api/v1/auth/login",
        json={"provider": "mock", "code": "test-user", "anonymousSessionId": session["sessionId"]},
    ).json()
    response = client.get("/api/v1/assets/history", headers={"Authorization": f"Bearer {bound['token']}"})
    assert response.status_code == 200
    assert response.json()[0]["sessionId"] == session["sessionId"]
