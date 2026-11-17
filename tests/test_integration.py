"""Integration tests — auto-skipped when Weaviate / the LLM are not running."""

import socket

import pytest

from sommebeer.config import get_settings
from sommebeer.retriever import BeerRetriever, connect


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


settings = get_settings()

weaviate_up = _reachable(settings.weaviate.host, settings.weaviate.port)
llm_up = _reachable("127.0.0.1", 11434)

pytestmark = pytest.mark.skipif(
    not weaviate_up, reason="Weaviate is not running")


@pytest.fixture(scope="module")
def retriever():
    client = connect(settings.weaviate)
    yield BeerRetriever(settings.weaviate, client)
    client.close()


@pytest.mark.skipif(not weaviate_up, reason="Weaviate is not running")
class TestWeaviate:
    def test_collection_exists_and_is_populated(self, retriever):
        coll = retriever.collection
        assert coll.aggregate.over_all(total_count=True).total_count > 100

    def test_beers_have_11_dim_taste_vectors(self, retriever):
        obj = next(iter(retriever.collection.iterator(include_vector=True)))
        vec = obj.vector.get("default") if isinstance(obj.vector, dict) \
            else obj.vector
        assert vec is not None and len(vec) == 11

    def test_by_style_returns_matching_beers(self, retriever):
        records = retriever.by_style("IPA")
        assert len(records) == settings.weaviate.limit
        assert all(beer.style_bjcp for beer in records)

    def test_by_likeness_returns_neighbours(self, retriever):
        records = retriever.by_likeness("Flower Power India Pale Ale")
        assert len(records) == settings.weaviate.limit
        assert records[0].score is not None

    def test_count_limit_is_honored(self, retriever):
        assert len(retriever.by_style("stout", limit=3)) == 3


@pytest.mark.skipif(not llm_up, reason="local LLM (11434) is not running")
class TestGraphEndToEnd:
    def test_full_agent_roundtrip(self, retriever):
        from sommebeer.llm import get_chat_model
        from sommebeer.graph import build_graph

        graph = build_graph(get_chat_model(settings.llm), retriever)
        state = graph.invoke({"question": "recommend me 2 IPAs"},
                             config={"recursion_limit": 10})
        assert state["intent"] == "by_style"
        assert len(state["beers"]) == 2
        assert state["answer"]
