"""Weaviate retriever: BM25 by style, near-vector by likeness."""

from __future__ import annotations

from opentelemetry import trace
from weaviate.classes.query import MetadataQuery

from .config import WeaviateConfig
from .schemas import BeerRecord

tracer = trace.get_tracer(__name__)

_STYLE_PROPS = ["style_bjcp^3", "style_category^3", "style_label^2",
                "name^1", "description^1", "tagline^1"]
_NAME_PROPS = ["name^3", "full_name^2", "description^1"]


def _vector_of(obj) -> list[float] | None:
    """The stored vector of a fetched object, whichever shape it comes in."""
    if isinstance(obj.vector, dict):
        return obj.vector.get("default")
    return obj.vector


class BeerRetriever:
    def __init__(self, cfg: WeaviateConfig, client) -> None:
        self.cfg = cfg
        self.client = client
        self.collection = client.collections.get(cfg.collection)

    # ── helpers ────────────────────────────────────────────────────────
    def _score_of(self, metadata) -> float | None:
        """BM25 score when present, else similarity (1 − distance)."""
        score = metadata.score if metadata else None
        distance = getattr(metadata, "distance", None) if metadata else None
        if score is not None:
            return score
        if distance is not None:
            return 1.0 - distance
        return None

    def _record_from(self, obj) -> BeerRecord:
        props = obj.properties
        return BeerRecord(
            name=props.get("name", "?"),
            full_name=props.get("full_name"),
            brewery=props.get("brewery"),
            style_bjcp=props.get("style_bjcp"),
            style_category=props.get("style_category"),
            abv=props.get("abv"),
            tagline=props.get("tagline"),
            description=props.get("description"),
            score=self._score_of(obj.metadata),
        )

    def _to_records(self, result, exclude_uuid: str | None = None) -> list[BeerRecord]:
        records = []
        for obj in result.objects:
            if exclude_uuid and str(obj.uuid) == exclude_uuid:
                continue
            records.append(self._record_from(obj))
        return records

    def _bm25_records(self, query: str, properties, limit: int) -> list[BeerRecord]:
        result = self.collection.query.bm25(
            query=query, limit=limit, query_properties=properties,
            return_metadata=MetadataQuery(score=True),
        )
        return self._to_records(result)

    def _reference(self, beer_name: str) -> tuple[list[float] | None, str | None]:
        """(vector, uuid) of the best-matching stocked beer, or (None, None)."""
        matches = self.collection.query.bm25(
            query=beer_name, limit=1, query_properties=_NAME_PROPS,
        ).objects
        if not matches:
            return None, None
        reference = self.collection.query.fetch_object_by_id(
            matches[0].uuid, include_vector=True)
        return _vector_of(reference), str(matches[0].uuid)

    def _neighbours(self, vector: list[float], exclude_uuid: str | None,
                    limit: int) -> list[BeerRecord]:
        result = self.collection.query.near_vector(
            vector, limit=limit + 1,
            return_metadata=MetadataQuery(distance=True),
        )
        return self._to_records(result, exclude_uuid=exclude_uuid)

    def _likeness_records(self, beer_name: str,
                          result_limit: int) -> list[BeerRecord]:
        """Neighbours of the reference beer, or a keyword fallback."""
        vector, reference_uuid = self._reference(beer_name)
        if vector:
            return self._neighbours(vector, reference_uuid, result_limit)
        return self._bm25_records(beer_name, _STYLE_PROPS, result_limit)

    # ── public API ─────────────────────────────────────────────────────
    def by_style(self, style: str, limit: int | None = None) -> list[BeerRecord]:
        """Keyword search biased towards the style fields."""
        with tracer.start_as_current_span("retrieve_by_style") as span:
            span.set_attribute("openinference.span.kind", "RETRIEVER")
            span.set_attribute("input.value", style)
            records = self._bm25_records(style, _STYLE_PROPS,
                                         limit or self.cfg.limit)
            span.set_attribute("retrieved_documents", len(records))
            return records

    def by_likeness(self, beer_name: str, limit: int | None = None) -> list[BeerRecord]:
        """Semantic neighbours of the named beer (its own taste-profile vector):
        with 11-dim taste vectors, 'similar' means 'tastes alike'."""
        result_limit = limit or self.cfg.limit
        with tracer.start_as_current_span("retrieve_by_likeness") as span:
            span.set_attribute("openinference.span.kind", "RETRIEVER")
            span.set_attribute("input.value", beer_name)
            records = self._likeness_records(beer_name, result_limit)
            span.set_attribute("retrieved_documents", len(records))
            return records


def connect(cfg: WeaviateConfig):
    import weaviate

    return weaviate.connect_to_local(
        host=cfg.host, port=cfg.port, grpc_port=cfg.grpc_port
    )
