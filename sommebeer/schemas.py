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
    count: int | None = Field(
        None, description="how many beers the customer asked for, if stated", ge=1
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
        style_bits = [style for style in (self.style_bjcp, self.style_category)
                      if style]
        if style_bits:
            head += f" — {' / '.join(style_bits)}"
        if self.abv is not None:
            head += f", {self.abv}% ABV"
        description = self.description or self.tagline or ""
        if description:
            head += f". {description.strip()[:220]}"
        return head
