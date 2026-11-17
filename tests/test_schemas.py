"""Tests for Pydantic schemas: validation and formatting."""

import pytest
from pydantic import ValidationError

from sommebeer.schemas import BeerRecord, RouterDecision


class TestRouterDecision:
    def test_valid_style(self):
        d = RouterDecision(intent="by_style", style="IPA", count=6)
        assert d.intent == "by_style"
        assert d.count == 6

    def test_valid_likeness(self):
        d = RouterDecision(intent="by_likeness", beer_name="Pliny The Elder")
        assert d.beer_name == "Pliny The Elder"
        assert d.count is None

    def test_invalid_intent_rejected(self):
        with pytest.raises(ValidationError):
            RouterDecision(intent="by_telepathy")

    def test_count_must_be_positive(self):
        with pytest.raises(ValidationError):
            RouterDecision(intent="by_style", style="IPA", count=0)

    def test_count_must_be_int(self):
        with pytest.raises(ValidationError):
            RouterDecision(intent="by_style", style="IPA", count="six")


class TestBeerRecord:
    def make(self, **over):
        base = dict(
            name="Sculpin", brewery="Ballast Point", style_bjcp="American IPA",
            abv=7.0, description="A bold, citrusy IPA.",
        )
        base.update(over)
        return BeerRecord(**base)

    def test_card_has_name_brewery_style_abv(self):
        card = self.make().card()
        assert "Sculpin" in card
        assert "Ballast Point" in card
        assert "American IPA" in card
        assert "7.0% ABV" in card
        assert "A bold, citrusy IPA." in card

    def test_card_survives_missing_fields(self):
        card = self.make(brewery=None, abv=None, description=None,
                         style_bjcp=None).card()
        assert card.startswith("- Sculpin")
        assert "%" not in card  # no ABV to render

    def test_card_truncates_long_description(self):
        rec = self.make(description="hoppy " * 100)
        assert len(rec.card()) < 400

    def test_defaults_are_none(self):
        rec = BeerRecord(name="Anything")
        assert rec.score is None
        assert rec.card() == "- Anything"
