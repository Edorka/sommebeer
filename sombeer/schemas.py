"""Pydantic schemas: router decisions, beer records, structured outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RouterDecision(BaseModel):
    """Result of classifying a customer message."""

    intent: Literal["by_style", "by_likeness", "general"]
    style: str | None = Field(
        None, description="beer style mentioned, e.g. 'IPA', 'stout' — for by_style"
    )
    beer_name: str | None = Field(
        None, description="beer name mentioned, e.g. 'Flower Power' — for by_likeness"
    )


class BeerRecord(BaseModel):
    """A beer as retrieved from Weaviate."""

    name: str
    full_name: str | None = None
    brewery: str | None = None
    style_bjcp: str | None = None
    style_category: str | None = None
    abv: float | None = None
    tagline: str | None = None
    description: str | None = None
    score: float | None = None

    def card(self) -> str:
        """Compact one-beer card for the LLM prompt."""
        head = f"- {self.name}"
        if self.brewery:
            head += f" ({self.brewery})"
        bits = [b for b in (self.style_bjcp, self.style_category) if b]
        if bits:
            head += f" — {' / '.join(bits)}"
        if self.abv is not None:
            head += f", {self.abv}% ABV"
        desc = self.description or self.tagline or ""
        if desc:
            desc = desc.strip()
            head += f". {desc[:220]}"
        return head


def beer_text(props: dict) -> str:
    """Text that gets embedded for a beer. Keep in sync with backfill_vectors.py."""
    name = props.get("name") or ""
    full_name = props.get("full_name") or name
    style_bits = " ".join(
        str(p) for p in (props.get("style_bjcp"), props.get("style_category")) if p
    )
    body = " ".join(
        str(p) for p in (props.get("tagline"), props.get("description")) if p
    )
    return f"{full_name} | {style_bits} | {body or name}".strip()
