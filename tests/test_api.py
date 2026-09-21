from fastapi.testclient import TestClient

import source.api as api


client = TestClient(api.app)


def test_health_returns_status_without_model_details():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_serves_frontend():
    response = client.get("/")

    assert response.status_code == 200
    assert "NVIDIA AI Agent" in response.text


def test_chat_rejects_empty_prompt():
    response = client.post("/api/chat", json={"prompt": ""})

    assert response.status_code == 422


def test_chat_streams_agent_events(monkeypatch):
    monkeypatch.setattr(
        api,
        "stream_events",
        lambda prompt: iter(
            [
                {"type": "prompt", "content": prompt},
                {"type": "content", "content": "Hello"},
                {"type": "done", "elapsed": 0.2},
            ]
        ),
    )

    response = client.post("/api/chat", json={"prompt": "Hi"})

    assert response.status_code == 200
    assert '"type": "content"' in response.text
    assert '"content": "Hello"' in response.text
    assert '"type": "done"' in response.text
