from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_invalid_topic_is_rejected():
    response = client.post("/api/v1/sessions", json={"topic": "", "questionCount": 5})
    assert response.status_code == 422


def test_answer_for_wrong_question_is_rejected():
    created = client.post("/api/v1/sessions", json={"topic": "物理"}).json()
    response = client.post(
        f"/api/v1/sessions/{created['sessionId']}/answers",
        json={"questionId": "q_wrong", "answer": "A", "clientRequestId": "wrong-question"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "QUESTION_OUT_OF_DATE"
