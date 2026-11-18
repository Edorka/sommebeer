"""Tests for the FastAPI deliverable — stubbed graph, no live services needed."""

from fastapi.testclient import TestClient

from backend.main import ChatRequest, create_app


class StubGraph:
    """Stands in for the LangGraph so no LLM/Weaviate is required."""

    def __init__(self, answer: str):
        self.answer = answer
        self.received = None

    def invoke(self, state, config=None):
        self.received = state
        return {"answer": self.answer}


def make_client(answer: str) -> TestClient:
    app = create_app()
    app.state.graph = StubGraph(answer)
    return TestClient(app)


class TestChat:
    def test_returns_the_answer(self):
        with make_client("**Stout** on tap!") as client:
            response = client.post("/chat",
                                   json={"question": "one stout please"})
        assert response.status_code == 200
        assert response.json() == {"answer": "**Stout** on tap!"}

    def test_passes_the_question_to_the_graph(self):
        stub = StubGraph("sure!")
        app = create_app()
        app.state.graph = stub
        with TestClient(app) as client:
            client.post("/chat", json={"question": "any IPAs?"})
        assert stub.received == {"question": "any IPAs?"}

    def test_empty_question_is_rejected(self):
        with make_client("hi") as client:
            response = client.post("/chat", json={"question": ""})
        assert response.status_code == 422


class TestHealth:
    def test_reports_status_and_services(self):
        with make_client("hi") as client:
            response = client.get("/health")
        body = response.json()
        assert response.status_code == 200
        assert body["status"] == "ok"
        assert isinstance(body["weaviate"], bool)
        assert isinstance(body["llm"], bool)


class TestCors:
    def test_development_allows_all_origins(self):
        with make_client("hi") as client:
            response = client.post("/chat", json={"question": "hi"},
                                   headers={"Origin": "http://localhost:5173"})
        assert response.headers["access-control-allow-origin"] == "*"

    def test_production_restricts_origins(self, monkeypatch):
        monkeypatch.setenv("SOMMEBEER_API__ENVIRONMENT", "production")
        with make_client("hi") as client:
            response = client.post("/chat", json={"question": "hi"},
                                   headers={"Origin": "http://localhost:5173"})
        assert "access-control-allow-origin" not in response.headers
