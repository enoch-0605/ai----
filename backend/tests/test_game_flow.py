from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_answer_and_report_flow():
    created = client.post(
        "/api/v1/sessions",
        json={"topic": "量子力学基础", "questionCount": 5, "difficulty": "beginner"},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["totalQuestions"] == 5
    assert payload["question"]["options"]
    session_id = payload["sessionId"]

    for index in range(5):
        current = client.get(f"/api/v1/sessions/{session_id}").json()
        answer = "A"
        response = client.post(
            f"/api/v1/sessions/{session_id}/answers",
            json={
                "questionId": current["question"]["questionId"],
                "answer": answer,
                "clientRequestId": f"request-{index}",
            },
        )
        assert response.status_code == 200
        if index < 4:
            assert response.json()["feedback"]["isCorrect"] is True
            client.post(f"/api/v1/sessions/{session_id}/continue")

    report = client.post(f"/api/v1/sessions/{session_id}/reports")
    assert report.status_code == 200
    assert report.json()["accuracy"] == 100
    assert report.json()["totalQuestions"] == 5


def test_duplicate_submission_does_not_change_score():
    created = client.post("/api/v1/sessions", json={"topic": "历史", "questionCount": 5}).json()
    session_id = created["sessionId"]
    question_id = created["question"]["questionId"]
    request = {"questionId": question_id, "answer": "B", "clientRequestId": "same-request"}

    first = client.post(f"/api/v1/sessions/{session_id}/answers", json=request)
    second = client.post(f"/api/v1/sessions/{session_id}/answers", json=request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["score"] == second.json()["score"] == 0
    assert first.json()["life"] == second.json()["life"] == 2


def test_missing_session_returns_domain_error():
    response = client.get("/api/v1/sessions/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "SESSION_NOT_FOUND"


def test_two_consecutive_correct_answers_raise_next_question_difficulty():
    created = client.post(
        "/api/v1/sessions",
        json={"topic": "数学", "questionCount": 5, "difficulty": "beginner"},
    ).json()
    session_id = created["sessionId"]

    for index in range(2):
        current = client.get(f"/api/v1/sessions/{session_id}").json()
        client.post(
            f"/api/v1/sessions/{session_id}/answers",
            json={
                "questionId": current["question"]["questionId"],
                "answer": "A",
                "clientRequestId": f"difficulty-{index}",
            },
        )
        client.post(f"/api/v1/sessions/{session_id}/continue")

    resumed = client.get(f"/api/v1/sessions/{session_id}")
    assert resumed.status_code == 200
    assert resumed.json()["question"]["difficulty"] == "advanced"
