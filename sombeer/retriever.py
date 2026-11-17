"""Weaviate retriever: BM25 by style, near-vector by likeness."""

from __future__ import annotations

from opentelemetry import trace
from weaviate.collections.queries.metadata import MetadataQuery

from .config import WeaviateConfig
from .embedder import embed_one
from .schemas import BeerRecord, beer_text

tracer = trace.get_tracer(__name__)

_PROPS = ["name", "full_name", "brewery", "style_bjcp", "style_category",
          "abv", "tagline", "description"]
_STYLE_PROPS = ["style_bjcp^3", "style_category^3", "style_label^2",
                "name^1", "description^1", "tagline^1"]
_NAME_PROPS = ["name^3", "full_name^2", "description^1"]


class BeerRetriever:
    def __init__(self, cfg: WeaviateConfig, client) -> None:
        self.cfg = cfg
        self.client = client
        self.collection = client.collections.get(cfg.collection)

    # ── helpers ────────────────────────────────────────────────────────
    def _to_records(self, result, exclude_uuid: str | None = None) -> list[BeerRecord]:
        out = []
        for obj in result.objects:
            if exclude_uuid and str(obj.uuid) == exclude_uuid:
                continue
            p = obj.properties
            score = obj.metadata.score if obj.metadata else None
            distance = getattr(obj.metadata, "distance", None) if obj.metadata else None
            out.append(BeerRecord(
                name=p.get("name", "?"),
                full_name=p.get("full_name"),
                brewery=p.get("brewery"),
                style_bjcp=p.get("style_bjcp"),
                style_category=p.get("style_category"),
                abv=p.get("abv"),
                tagline=p.get("tagline"),
                description=p.get("description"),
                score=score if score is not None else (
                    1.0 - distance if distance is not None else None),
            ))
        return out

    # ── public API ─────────────────────────────────────────────────────
    def by_style(self, style: str) -> list[BeerRecord]:
        """Keyword search biased towards the style fields."""
        with tracer.start_as_current_span("retrieve_by_style") as span:
            span.set_attribute("openinference.span.kind", "RETRIEVER")
            span.set_attribute("input.value", style)
            res = self.collection.query.bm25(
                query=style, limit=self.cfg.limit,
                query_properties=_STYLE_PROPS,
                return_metadata=MetadataQuery(score=True),
            )
            records = self._to_records(res)
            span.set_attribute("retrieved_documents", len(records))
            return records

    def by_likeness(self, beer_name: str) -> list[BeerRecord]:
        """Semantic neighbours of the named beer (its own vector as query)."""
        with tracer.start_as_current_span("retrieve_by_likeness") as span:
            span.set_attribute("openinference.span.kind", "RETRIEVER")
            span.set_attribute("input.value", beer_name)

            # 1. locate the reference beer and its stored vector
            ref = self.collection.query.bm25(
                query=beer_name, limit=1, query_properties=_NAME_PROPS,
            ).objects
            if ref:
                obj = self.collection.query.get_by_id(
                    ref[0].uuid, include_vector=True)
                vec = obj.vector.get("default") if isinstance(obj.vector, dict) else obj.vector
            else:
                vec = embed_one(beer_text({"name": beer_name}))
            ref_uuid = str(ref[0].uuid) if ref else None

            # 2. semantic search with that vector
            res = self.collection.query.near_vector(
                vector=vec, limit=self.cfg.limit + 1,
                return_metadata=MetadataQuery(distance=True),
            )
            records = self._to_records(res, exclude_uuid=ref_uuid)
            if vec is None:
                records = []  # vectors not backfilled yet
            span.set_attribute("retrieved_documents", len(records))
            return records


def connect(cfg: WeaviateConfig):
    import weaviate

    return weaviate.connect_to_local(
        host=cfg.host, port=cfg.port, grpc_port=cfg.grpc_port
    )
