from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.cards import Card, CardBase, CardText, build_localized_card, validate_cards


def _project_root() -> Path:
    # app/infra/cards_repository.py -> app/infra -> app -> project root
    return Path(__file__).resolve().parents[2]


def _cards_base_json_path() -> Path:
    return _project_root() / "app" / "data" / "tarot" / "cards.base.json"


def _cards_i18n_json_path(locale: str) -> Path:
    return _project_root() / "app" / "data" / "i18n" / f"cards.{locale}.json"


def _static_root() -> Path:
    return _project_root() / "app" / "static"


@dataclass(frozen=True, slots=True)
class CardsRepository:
    cards_by_id: dict[str, Card]
    locale: str
    fallback_locale: str

    def get(self, card_id: str) -> Card:
        try:
            return self.cards_by_id[card_id]
        except KeyError as e:
            raise KeyError(f"Unknown card_id: {card_id!r}") from e

    def list_all(self) -> list[Card]:
        return list(self.cards_by_id.values())


def _parse_base_cards_payload(payload: dict[str, Any]) -> list[CardBase]:
    raw_cards = payload.get("cards")
    if not isinstance(raw_cards, list):
        raise ValueError("cards.base.json must have a top-level 'cards': [] array")
    cards = [CardBase.from_dict(c) for c in raw_cards]
    validate_cards(cards)
    return cards


def _parse_i18n_cards_payload(payload: dict[str, Any]) -> dict[int, CardText]:
    raw_cards = payload.get("cards")
    if not isinstance(raw_cards, list):
        raise ValueError("cards.<locale>.json must have a top-level 'cards': [] array")

    parsed: dict[int, CardText] = {}
    for raw in raw_cards:
        if not isinstance(raw, dict):
            raise ValueError("Localized card entry must be an object")
        text = CardText.from_dict(raw)
        parsed[text.card_no] = text
    return parsed


def _validate_static_assets(cards: list[CardBase]) -> list[str]:
    warnings: list[str] = []
    static_root = _static_root()
    for c in cards:
        img = static_root / c.image_path
        if not img.exists():
            warnings.append(f"Missing image for {c.id}: {c.image_path}")
    return warnings


@lru_cache(maxsize=1)
def load_cards_repository(
    *, locale: str = "sk", fallback_locale: str = "sk", validate_images: bool = False
) -> CardsRepository:
    base_payload = json.loads(_cards_base_json_path().read_text(encoding="utf-8"))
    base_cards = _parse_base_cards_payload(base_payload)

    fallback_payload = json.loads(_cards_i18n_json_path(fallback_locale).read_text(encoding="utf-8"))
    fallback_texts = _parse_i18n_cards_payload(fallback_payload)

    requested_texts: dict[int, CardText] = {}
    if locale != fallback_locale:
        locale_path = _cards_i18n_json_path(locale)
        if locale_path.exists():
            requested_payload = json.loads(locale_path.read_text(encoding="utf-8"))
            requested_texts = _parse_i18n_cards_payload(requested_payload)

    if validate_images:
        warnings = _validate_static_assets(base_cards)
        if warnings:
            joined = "\n".join(warnings[:10])
            more = "" if len(warnings) <= 10 else f"\n... and {len(warnings) - 10} more"
            raise FileNotFoundError(f"Some card images are missing:\n{joined}{more}")

    localized: dict[str, Card] = {}
    for base_card in base_cards:
        text = requested_texts.get(base_card.card_no) or fallback_texts.get(base_card.card_no)
        if text is None:
            raise ValueError(
                f"Missing localized text for card_no={base_card.card_no} ({base_card.id!r}) in locale={locale!r} "
                f"and fallback_locale={fallback_locale!r}"
            )
        if text.id != base_card.id:
            raise ValueError(
                f"Localized id mismatch for card_no={base_card.card_no}: "
                f"base={base_card.id!r}, localized={text.id!r}"
            )
        resolved_locale = locale if base_card.card_no in requested_texts else fallback_locale
        localized[base_card.id] = build_localized_card(base_card, text, resolved_locale)

    return CardsRepository(cards_by_id=localized, locale=locale, fallback_locale=fallback_locale)

