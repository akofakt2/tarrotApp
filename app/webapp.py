from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Flask, abort, render_template, request

from app.infra.cards_repository import load_cards_repository


def _load_pages(locale: str, *, fallback_locale: str = "sk") -> dict[str, Any]:
    root = Path(__file__).resolve().parent.parent
    pages_path = root / "app" / "data" / "i18n" / f"pages.{locale}.json"
    if not pages_path.exists():
        pages_path = root / "app" / "data" / "i18n" / f"pages.{fallback_locale}.json"

    return json.loads(pages_path.read_text(encoding="utf-8"))


def create_app() -> Flask:
    base_dir = Path(__file__).resolve().parent  # .../app
    template_folder = base_dir / "templates"
    static_folder = base_dir / "static"

    app = Flask(
        __name__,
        template_folder=str(template_folder),
        static_folder=str(static_folder),
    )

    @app.get("/cards")
    def cards_catalog() -> str:
        locale = (request.args.get("locale") or "en").lower()
        if locale not in {"en", "sk"}:
            abort(400, "Unsupported locale")

        suit = request.args.get("suit")
        if suit is not None and suit.lower() in {"none", ""}:
            suit = None
        if suit is not None and suit not in {"wands", "cups", "swords", "pentacles"}:
            abort(400, "Unsupported suit")

        card_no_raw = request.args.get("card_no")
        card_no = None
        if card_no_raw and card_no_raw.lower() not in {"none", ""}:
            try:
                card_no = int(card_no_raw)
            except ValueError:
                abort(400, "card_no must be an integer")

        # If a major card is explicitly selected, show major detail even if `suit`
        # is present in the query string (e.g. after switching suits earlier).
        if card_no is not None:
            suit = None

        pages = _load_pages(locale, fallback_locale="sk")
        card_detail = pages.get("pages", {}).get("card_detail", {})
        upright_heading = card_detail.get("upright_heading", "Upright")
        reversed_heading = card_detail.get("reversed_heading", "Reversed")

        repo = load_cards_repository(locale=locale, fallback_locale="sk", validate_images=False)
        cards = repo.list_all()

        major_cards = sorted((c for c in cards if c.arcana == "major"), key=lambda c: c.card_no)
        suits = ["wands", "cups", "swords", "pentacles"]
        minor_cards_for_suit = []
        if suit:
            minor_cards_for_suit = sorted(
                (c for c in cards if c.arcana == "minor" and c.suit == suit),
                key=lambda c: c.card_no,
            )

        # Bottom content:
        # - if suit selected => show minor cards for this suit
        # - else => show one selected major card (or the first major card)
        bottom_major = None
        if not suit:
            if card_no is None:
                bottom_major = major_cards[0]
            else:
                bottom_major = next((c for c in major_cards if c.card_no == card_no), None)
            if bottom_major is None:
                abort(404, "Card not found")

        return render_template(
            "cards/catalog.html",
            locale=locale,
            major_cards=major_cards,
            suits=suits,
            selected_suit=suit,
            upright_heading=upright_heading,
            reversed_heading=reversed_heading,
            bottom_major=bottom_major,
            minor_cards_for_suit=minor_cards_for_suit,
            selected_card_no=card_no,
        )

    return app

