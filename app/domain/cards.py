from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Arcana = Literal["major", "minor"]
Suit = Literal["wands", "cups", "swords", "pentacles"]
Orientation = Literal["upright", "reversed"]


@dataclass(frozen=True, slots=True)
class CardBase:
    card_no: int
    id: str
    arcana: Arcana
    number: int | None
    suit: Suit | None
    rank: str | None
    image_path: str

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "CardBase":
        required = (
            "card_no",
            "id",
            "arcana",
            "image_path",
        )
        missing = [k for k in required if k not in raw]
        if missing:
            raise ValueError(f"Card missing required fields: {missing}")

        arcana = raw["arcana"]
        if arcana not in ("major", "minor"):
            raise ValueError(f"Invalid arcana: {arcana!r}")

        suit = raw.get("suit")
        if suit is not None and suit not in ("wands", "cups", "swords", "pentacles"):
            raise ValueError(f"Invalid suit: {suit!r}")

        return CardBase(
            card_no=int(raw["card_no"]),
            id=str(raw["id"]),
            arcana=arcana,
            number=raw.get("number"),
            suit=suit,
            rank=raw.get("rank"),
            image_path=str(raw["image_path"]),
        )


@dataclass(frozen=True, slots=True)
class CardText:
    card_no: int
    id: str
    name: str
    keywords: tuple[str, ...]
    meaning_upright: str
    meaning_reversed: str
    archetype: str | None = None
    description: str | None = None

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "CardText":
        required = ("card_no", "id", "name", "keywords", "meaning_upright", "meaning_reversed")
        missing = [k for k in required if k not in raw]
        if missing:
            raise ValueError(f"Localized card missing required fields: {missing}")

        keywords = raw["keywords"]
        if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            raise ValueError("keywords must be a list[str]")

        return CardText(
            card_no=int(raw["card_no"]),
            id=str(raw["id"]),
            name=str(raw["name"]),
            keywords=tuple(keywords),
            meaning_upright=str(raw["meaning_upright"]),
            meaning_reversed=str(raw["meaning_reversed"]),
            archetype=raw.get("archetype"),
            description=raw.get("description"),
        )


@dataclass(frozen=True, slots=True)
class Card:
    card_no: int
    id: str
    name: str
    arcana: Arcana
    number: int | None
    suit: Suit | None
    rank: str | None
    keywords: tuple[str, ...]
    meaning_upright: str
    meaning_reversed: str
    image_path: str
    locale: str
    archetype: str | None = None
    description: str | None = None


def build_localized_card(base: CardBase, text: CardText, locale: str) -> Card:
    return Card(
        card_no=base.card_no,
        id=base.id,
        name=text.name,
        arcana=base.arcana,
        number=base.number,
        suit=base.suit,
        rank=base.rank,
        keywords=text.keywords,
        meaning_upright=text.meaning_upright,
        meaning_reversed=text.meaning_reversed,
        image_path=base.image_path,
        locale=locale,
        archetype=text.archetype,
        description=text.description,
    )


def validate_cards(cards: list[CardBase]) -> None:
    if len(cards) != 78:
        raise ValueError(f"Expected 78 cards, got {len(cards)}")

    card_numbers = [c.card_no for c in cards]
    if sorted(card_numbers) != list(range(1, 79)):
        raise ValueError("card_no must be a unique continuous range 1..78")

    ids = [c.id for c in cards]
    seen: set[str] = set()
    duplicates: set[str] = set()
    for card_id in ids:
        if card_id in seen:
            duplicates.add(card_id)
        seen.add(card_id)
    if duplicates:
        raise ValueError(f"Duplicate card ids: {sorted(duplicates)}")

