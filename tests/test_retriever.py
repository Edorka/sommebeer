"""Tests for retriever record mapping — no live Weaviate needed."""

from types import SimpleNamespace
from uuid import uuid4

from sommebeer.retriever import BeerRetriever
from sommebeer.config import WeaviateConfig


def make_retriever():
    fake = SimpleNamespace(collections=SimpleNamespace(get=lambda name: None))
    return BeerRetriever(WeaviateConfig(), client=fake)


def fake_result(*, score=None, distance=None, uuid=None, name="Sculpin"):
    obj = SimpleNamespace(
        uuid=uuid or uuid4(),
        properties={"name": name, "brewery": "Ballast Point",
                   "style_bjcp": "American IPA", "abv": 7.0},
        metadata=SimpleNamespace(score=score, distance=distance),
    )
    return SimpleNamespace(objects=[obj]), obj


class TestToRecords:
    def test_bm25_score_is_kept(self):
        r = make_retriever()
        res, obj = fake_result(score=13.7)
        records = r._to_records(res)
        assert len(records) == 1
        assert records[0].name == "Sculpin"
        assert records[0].score == 13.7

    def test_distance_converts_to_similarity(self):
        r = make_retriever()
        res, _ = fake_result(distance=0.05)
        assert abs(r._to_records(res)[0].score - 0.95) < 1e-9

    def test_none_metadata_yields_none_score(self):
        r = make_retriever()
        obj = SimpleNamespace(uuid=uuid4(), properties={"name": "X"},
                              metadata=None)
        res = SimpleNamespace(objects=[obj])
        assert r._to_records(res)[0].score is None

    def test_excluded_uuid_is_filtered_out(self):
        r = make_retriever()
        res, obj = fake_result(score=1.0)
        records = r._to_records(res, exclude_uuid=str(obj.uuid))
        assert records == []

    def test_other_uuid_is_kept(self):
        r = make_retriever()
        res, _ = fake_result(score=1.0)
        records = r._to_records(res, exclude_uuid=str(uuid4()))
        assert len(records) == 1
