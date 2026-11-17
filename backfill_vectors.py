"""One-time backfill: store each beer's taste profile as its vector.

The Beer collection uses 11-dim taste-profile vectors (the numeric properties
astringency, body, alcohol, bitter, sweet, sour, salty, fruits, hoppy, spices,
malty — each divided by 100). 'Similar beers' then means 'tastes alike'.

Usage:  .venv/bin/python backfill_vectors.py
Idempotent: skips beers that already have a vector.
"""

from sombeer.config import get_settings
from sombeer.retriever import connect

_TASTE_PROPS = ["astringency", "body", "alcohol", "bitter", "sweet", "sour",
                "salty", "fruits", "hoppy", "spices", "malty"]


def taste_vector(props: dict) -> list[float] | None:
    values = [props.get(p) for p in _TASTE_PROPS]
    if any(v is None for v in values):
        return None
    return [float(v) / 100.0 for v in values]


def main() -> None:
    cfg = get_settings().weaviate
    client = connect(cfg)
    try:
        coll = client.collections.get(cfg.collection)
        total = coll.aggregate.over_all(total_count=True).total_count
        print(f"backfilling taste-profile vectors for {total} beers…")

        done, skipped = 0, 0
        with coll.batch.fixed_size(batch_size=64) as batch:
            for obj in coll.iterator(include_vector=True):
                vec = obj.vector.get("default") if isinstance(obj.vector, dict) \
                    else obj.vector
                if vec:
                    skipped += 1
                    continue
                v = taste_vector(obj.properties)
                if v is None:
                    continue
                batch.update(uuid=obj.uuid, vector=v)
                done += 1
        print(f"done: {done} embedded, {skipped} already had vectors")
    finally:
        client.close()


if __name__ == "__main__":
    main()
