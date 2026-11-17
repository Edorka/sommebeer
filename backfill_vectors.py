#!/usr/bin/env python3
"""One-time backfill: embed all Beer objects with local MiniLM and store vectors.

Usage:  .venv/bin/python backfill_vectors.py
Takes ~3-5 minutes on CPU (3,197 beers). Safe to re-run (skips nothing, just
re-embeds and overwrites — deterministic model, same vectors).
"""

from sombeer.config import get_settings
from sombeer.embedder import embed
from sombeer.retriever import connect
from sombeer.schemas import beer_text


def main() -> None:
    cfg = get_settings().weaviate
    client = connect(cfg)
    try:
        coll = client.collections.get(cfg.collection)
        total = coll.aggregate.over_all(total_count=True).total_count
        print(f"embedding {total} beers from '{cfg.collection}'…")

        done = 0
        with coll.batch.fixed_size(batch_size=64) as batch:
            for obj in coll.iterator(include_vector=True):
                vec = obj.vector.get("default") if isinstance(obj.vector, dict) \
                    else obj.vector
                if vec:  # already has a vector — skip on re-runs
                    continue
                text = beer_text(obj.properties)
                (e,) = embed([text])
                batch.update(uuid=obj.uuid, vector=e)
                done += 1
                if done % 256 == 0:
                    print(f"  {done} embedded…")
        print(f"done: {done} beers embedded and stored in Weaviate")
    finally:
        client.close()


if __name__ == "__main__":
    main()
