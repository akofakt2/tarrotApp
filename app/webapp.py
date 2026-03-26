"""Flask app: presný balík 78 kariet + JSON a obrázky podľa TAROT_LOCALE."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from flask import Flask, abort, current_app, render_template, request

from app.domain.cards import Card, validate_cards
from app.domain.deck import Deck

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[misc, assignment]

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data" / "i18n"


def _load_cards(locale: str) -> list[Card]:
    path = DATA_DIR / f"cards.{locale}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Chýba presný súbor: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("cards")
    if not isinstance(raw, list):
        raise ValueError("cards.<locale>.json: očakávam pole 'cards'")
    cards = [Card.from_dict(c) for c in raw]
    validate_cards(cards)
    return cards


def _load_pages(locale: str) -> dict[str, Any]:
    path = DATA_DIR / f"pages.{locale}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Chýba presný súbor: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_card_faces(cards: list[Card], images_dir: Path) -> None:
    missing: list[str] = []
    for c in cards:
        p = images_dir / c.image_path
        if not p.is_file():
            missing.append(f"{c.id}: {c.image_path}")
    if missing:
        raise FileNotFoundError(
            "Chýbajú obrázky predných strán kariet:\n" + "\n".join(missing[:20])
            + (f"\n... a ďalších {len(missing) - 20}" if len(missing) > 20 else "")
        )


def create_app() -> Flask:
    if load_dotenv is not None:
        load_dotenv()

    app = Flask(
        __name__,
        template_folder=str(APP_DIR / "templates"),
        static_folder=str(APP_DIR / "static"),
    )

    locale = (os.getenv("TAROT_LOCALE") or "en").strip().lower()
    if locale not in {"en", "sk"}:
        raise ValueError("TAROT_LOCALE musí byť en alebo sk")

    cards = _load_cards(locale)
    pages = _load_pages(locale)

    card_set = (os.getenv("TAROT_CARD_SET") or "default").strip()
    img_base = (os.getenv("TAROT_CARD_IMAGES_BASE_DIR") or "cards").strip().strip("/")
    images_abs = APP_DIR / "static" / img_base / card_set
    card_back = (os.getenv("TAROT_CARD_BACK") or "back.png").strip()

    Deck.validate_back(card_back, images_abs)
    _validate_card_faces(cards, images_abs)

    app.config["CARDS"] = cards
    app.config["PAGES"] = pages
    app.config["LOCALE"] = locale
    app.config["CARD_IMAGES_DIR"] = f"{img_base}/{card_set}"
    app.config["CARD_BACK"] = card_back
    app.config["CARD_IMAGES_ABS"] = images_abs

    @app.get("/cards")
    def cards_catalog() -> str:
        loc = current_app.config["LOCALE"]
        suit = request.args.get("suit")
        if suit and suit.lower() in {"", "none"}:
            suit = None
        if suit and suit not in {"wands", "cups", "swords", "pentacles"}:
            abort(400, "Neplatný suit")

        card_id = None
        raw_id = request.args.get("id")
        if raw_id and raw_id.lower() not in {"", "none"}:
            try:
                card_id = int(raw_id)
            except ValueError:
                abort(400, "id musí byť číslo")
        if card_id is not None:
            suit = None

        pages = current_app.config["PAGES"]
        detail = pages.get("pages", {}).get("card_detail", {})
        up = detail.get("upright_heading", "Upright")
        rev = detail.get("reversed_heading", "Reversed")

        all_cards: list[Card] = current_app.config["CARDS"]
        major = sorted((c for c in all_cards if c.arcana == "major"), key=lambda c: c.id)
        suits = ["wands", "cups", "swords", "pentacles"]
        minors = []
        if suit:
            minors = sorted(
                (c for c in all_cards if c.arcana == "minor" and c.suit == suit),
                key=lambda c: c.id,
            )

        bottom = None
        if not suit:
            if card_id is None:
                bottom = major[0]
            else:
                bottom = next((c for c in major if c.id == card_id), None)
            if bottom is None:
                abort(404, "Karta nenájdená")

        return render_template(
            "cards/catalog.html",
            locale=loc,
            card_images_dir=current_app.config["CARD_IMAGES_DIR"],
            major_cards=major,
            suits=suits,
            selected_suit=suit,
            upright_heading=up,
            reversed_heading=rev,
            bottom_major=bottom,
            minor_cards_for_suit=minors,
            selected_id=card_id,
        )

    @app.get("/deck")
    def deck_view() -> str:
        loc = current_app.config["LOCALE"]
        all_cards: list[Card] = current_app.config["CARDS"]
        d = Deck(
            back=current_app.config["CARD_BACK"],
            images_dir=current_app.config["CARD_IMAGES_ABS"],
        )
        d.reset(sorted(c.id for c in all_cards))
        d.shuffle()

        by_id = {c.id: c for c in all_cards}
        deck_cards = [(by_id[i], d.orientations.get(i, "upright")) for i in d.order]

        return render_template(
            "deck/view.html",
            locale=loc,
            card_images_dir=current_app.config["CARD_IMAGES_DIR"],
            deck_back=current_app.config["CARD_BACK"],
            deck_cards=deck_cards,
        )

    return app
