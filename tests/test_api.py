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
        assert response.json()["answer"] == "**Stout** on tap!"

    def test_ids_for_the_ui_are_hex_or_blank(self):
        with make_client("**meal**") as client:
            response = client.post("/chat", json={"question": "one stout"})
        body = response.json()
        # when Phoenix tracing is off the ids are honest zeros; the UI only
        # offers thumbs when they are real hex
        assert len(body["trace_id"]) == 32 and len(body["span_id"]) == 16
        int(body["trace_id"], 16) and int(body["span_id"], 16)

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


class TestFeedback:
    """Votes land as Phoenix span annotations — backend is a thin relay."""

    def test_posts_an_annotation_to_the_collector(self, monkeypatch):
        posted = []

        def fake_annotate(endpoint, span_id, trace_id, rating):
            posted.append({"endpoint": endpoint, "span_id": span_id,
                           "trace_id": trace_id, "rating": rating})

        monkeypatch.setattr("backend.main.annotate_span", fake_annotate)
        with make_client("hi") as client:
            response = client.post("/feedback", json={
                "trace_id": "a" * 32, "span_id": "b" * 16, "rating": "up"})
        assert response.status_code == 204
        assert posted[0]["rating"] == "up"

    def test_has_twice_means_unreachable_collector(self, monkeypatch):
        import httpx
        monkeypatch.setattr(
            "backend.main.annotate_span",
            lambda *a, **kw: (_ for _ in ()).throw(httpx.ConnectError("x")))
        with make_client("hi") as client:
            response = client.post("/feedback", json={
                "trace_id": "a" * 32, "span_id": "b" * 16, "rating": "down"})
        assert response.status_code == 502

    def test_rejects_garbage_ids_and_ratings(self):
        with make_client("hi") as client:
            for bad in (
                {"trace_id": "xyz", "span_id": "b" * 16, "rating": "up"},
                {"trace_id": "a" * 32, "span_id": "zzz", "rating": "up"},
                {"trace_id": "a" * 32, "span_id": "b" * 16, "rating": "meh"},
            ):
                response = client.post("/feedback", json=bad)
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
