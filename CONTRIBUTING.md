# Contributing to sommebeer

## Code style

This repo follows the same personal style as [blockpy](https://github.com/Edorka/blockpy):

- **Short functions only** — ≤ 15 lines, ideally ≤ 10. If a function grows,
  split it into named steps that tell the story (`_find_reference_beer`,
  `_neighbours`, `_keyword_fallback`).
- **No single-character variable or argument names** — not even in
  comprehensions. `beer`, not `b`; `settings`, not `s`; `records`, not `r`.
  The only exceptions are `_` and the conventional `f` inside decorators.
- Names should say what the thing *is*, not what type it has.

## Everything else

- All behavior changes go through `tests/` — `pytest` must stay green
  (integration tests run live when the stack is up, skip otherwise).
- Keep the tender's grounding rules intact: it recommends only what
  Weaviate returned.
