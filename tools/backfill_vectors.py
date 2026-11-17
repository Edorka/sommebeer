"""One-time backfill: store each beer's taste profile as its vector.

The Beer collection uses 11-dim taste-profile vectors (the numeric properties
astringency, body, alcohol, bitter, sweet, sour, salty, fruits, hoppy, spices,
malty — each divided by 100). 'Similar beers' then means 'tastes alike'.

Usage:  .venv/bin/python backfill_vectors.py
Idempotent: skips beers that already have a vector.
"""

from sommebeer.config import get_settings
from sommebeer.retriever import connect

_TASTE_PROPS = ["astringency", "body", "alcohol", "bitter", "sweet", "sour",
                "salty", "fruits", "hoppy", "spices", "malty"]


def taste_vector(properties: dict) -> list[float] | None:
    """The 11 taste numbers of a beer, scaled to 0-1 — or None if incomplete."""
    values = [properties.get(name) for name in _TASTE_PROPS]
    if any(value is None for value in values):
        return None
    return [float(value) / 100.0 for value in values]


def _stored_vector(obj) -> list[float] | None:
    if isinstance(obj.vector, dict):
        return obj.vector.get("default")
    return obj.vector


def _embed_missing(coll) -> tuple[int, int]:
    """Vectorize every taste profile not yet embedded. Returns (done, skipped)."""
    done, skipped = 0, 0
    with coll.batch.fixed_size(batch_size=64) as batch:
        for obj in coll.iterator(include_vector=True):
            if _stored_vector(obj):
                skipped += 1
                continue
            vector = taste_vector(obj.properties)
            if vector is None:
                continue
            batch.update(uuid=obj.uuid, vector=vector)
            done += 1
    return done, skipped


def main() -> None:
    cfg = get_settings().weaviate
    client = connect(cfg)
    try:
        coll = client.collections.get(cfg.collection)
        total = coll.aggregate.over_all(total_count=True).total_count
        print(f"backfilling taste-profile vectors for {total} beers…")
        done, skipped = _embed_missing(coll)
        print(f"done: {done} embedded, {skipped} already had vectors")
    finally:
        client.close()


if __name__ == "__main__":
    main()
