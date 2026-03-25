from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.cards import Card, validate_cards


def _project_root() -> Path:
    # app/infra/cards_repository.py -> app/infra -> app -> project root
    return Path(__file__).resolve().parents[2]

def _cards_i18n_json_path(locale: str) -> Path:
    return _project_root() / "app" / "data" / "i18n" / f"cards.{locale}.json"


def _static_root() -> Path:
    return _project_root() / "app" / "static"


@dataclass(frozen=True, slots=True)
class CardsRepository:
    cards_by_id: dict[int, Card]
    locale: str
    fallback_locale: str

    def get(self, card_id: int) -> Card:
        try:
            return self.cards_by_id[card_id]
        except KeyError as e:
            raise KeyError(f"Unknown card_id: {card_id!r}") from e

    def list_all(self) -> list[Card]:
        return list(self.cards_by_id.values())


def _parse_cards_payload(payload: dict[str, Any]) -> list[Card]:
    raw_cards = payload.get("cards")
    if not isinstance(raw_cards, list):
        raise ValueError("cards.<locale>.json must have a top-level 'cards': [] array")
    cards = [Card.from_dict(c) for c in raw_cards]
    validate_cards(cards)
    return cards


def _validate_static_assets(*, cards: list[Card], images_dir: str) -> list[str]:
    warnings: list[str] = []
    static_root = _static_root()
    for c in cards:
        img = static_root / images_dir / c.image_path
        if not img.exists():
            warnings.append(f"Missing image for {c.id}: {images_dir}/{c.image_path}")
    return warnings


@lru_cache(maxsize=1)
def load_cards_repository(
    *,
    locale: str = "sk",
    fallback_locale: str = "sk",
    validate_images: bool = False,
    card_set: str = "default",
    images_base_dir: str = "cards",
) -> CardsRepository:
    locale_path = _cards_i18n_json_path(locale)
    if not locale_path.exists():
        locale_path = _cards_i18n_json_path(fallback_locale)

    payload = json.loads(locale_path.read_text(encoding="utf-8"))
    cards = _parse_cards_payload(payload)

    if validate_images:
        images_dir = f"{images_base_dir}/{card_set}".strip("/")
        warnings = _validate_static_assets(cards=cards, images_dir=images_dir)
        if warnings:
            joined = "\n".join(warnings[:10])
            more = "" if len(warnings) <= 10 else f"\n... and {len(warnings) - 10} more"
            raise FileNotFoundError(f"Some card images are missing:\n{joined}{more}")
    cards_by_id = {c.id: c for c in cards}
    resolved_locale = locale if _cards_i18n_json_path(locale).exists() else fallback_locale
    return CardsRepository(cards_by_id=cards_by_id, locale=resolved_locale, fallback_locale=fallback_locale)

