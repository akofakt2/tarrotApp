from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from flask import Flask, abort, render_template, request

from app.domain.deck import Deck
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

    app.config["TAROT_CARD_SET"] = os.getenv("TAROT_CARD_SET", "default")
    app.config["TAROT_CARD_IMAGES_BASE_DIR"] = os.getenv("TAROT_CARD_IMAGES_BASE_DIR", "cards")

    @app.get("/cards")
    def cards_catalog() -> str:
        locale = (request.args.get("locale") or "en").lower()
        if locale not in {"en", "sk"}:
            abort(400, "Unsupported locale")

        card_set = (request.args.get("set") or app.config.get("TAROT_CARD_SET") or "default").strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", card_set):
            abort(400, "Unsupported card set")
        images_base_dir = (app.config.get("TAROT_CARD_IMAGES_BASE_DIR") or "cards").strip().strip("/")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_/-]*", images_base_dir):
            abort(500, "Invalid TAROT_CARD_IMAGES_BASE_DIR")
        card_images_dir = f"{images_base_dir}/{card_set}".strip("/")

        suit = request.args.get("suit")
        if suit is not None and suit.lower() in {"none", ""}:
            suit = None
        if suit is not None and suit not in {"wands", "cups", "swords", "pentacles"}:
            abort(400, "Unsupported suit")

        card_id_raw = request.args.get("id")
        card_id = None
        if card_id_raw and card_id_raw.lower() not in {"none", ""}:
            try:
                card_id = int(card_id_raw)
            except ValueError:
                abort(400, "id must be an integer")

        # If a major card is explicitly selected, show major detail even if `suit`
        # is present in the query string (e.g. after switching suits earlier).
        if card_id is not None:
            suit = None

        pages = _load_pages(locale, fallback_locale="sk")
        card_detail = pages.get("pages", {}).get("card_detail", {})
        upright_heading = card_detail.get("upright_heading", "Upright")
        reversed_heading = card_detail.get("reversed_heading", "Reversed")

        repo = load_cards_repository(
            locale=locale,
            fallback_locale="sk",
            validate_images=False,
            card_set=card_set,
            images_base_dir=images_base_dir,
        )
        cards = repo.list_all()

        major_cards = sorted((c for c in cards if c.arcana == "major"), key=lambda c: c.id)
        suits = ["wands", "cups", "swords", "pentacles"]
        minor_cards_for_suit = []
        if suit:
            minor_cards_for_suit = sorted(
                (c for c in cards if c.arcana == "minor" and c.suit == suit),
                key=lambda c: c.id,
            )

        # Bottom content:
        # - if suit selected => show minor cards for this suit
        # - else => show one selected major card (or the first major card)
        bottom_major = None
        if not suit:
            if card_id is None:
                bottom_major = major_cards[0]
            else:
                bottom_major = next((c for c in major_cards if c.id == card_id), None)
            if bottom_major is None:
                abort(404, "Card not found")

        return render_template(
            "cards/catalog.html",
            locale=locale,
            card_set=card_set,
            card_images_dir=card_images_dir,
            major_cards=major_cards,
            suits=suits,
            selected_suit=suit,
            upright_heading=upright_heading,
            reversed_heading=reversed_heading,
            bottom_major=bottom_major,
            minor_cards_for_suit=minor_cards_for_suit,
            selected_id=card_id,
        )

    @app.get("/deck")
    def deck_view() -> str:
        locale = (request.args.get("locale") or "en").lower()
        if locale not in {"en", "sk"}:
            abort(400, "Unsupported locale")

        card_set = (request.args.get("set") or app.config.get("TAROT_CARD_SET") or "default").strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", card_set):
            abort(400, "Unsupported card set")
        images_base_dir = (app.config.get("TAROT_CARD_IMAGES_BASE_DIR") or "cards").strip().strip("/")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_/-]*", images_base_dir):
            abort(500, "Invalid TAROT_CARD_IMAGES_BASE_DIR")
        card_images_dir = f"{images_base_dir}/{card_set}".strip("/")

        seed_raw = request.args.get("seed")
        seed: int | None = None
        if seed_raw and seed_raw.lower() not in {"none", ""}:
            try:
                seed = int(seed_raw)
            except ValueError:
                abort(400, "seed must be an integer")

        repo = load_cards_repository(
            locale=locale,
            fallback_locale="sk",
            validate_images=False,
            card_set=card_set,
            images_base_dir=images_base_dir,
        )
        cards = repo.list_all()

        d = Deck()
        d.reset(sorted((c.id for c in cards)))
        d.shuffle(seed=seed)

        cards_by_id = {c.id: c for c in cards}
        deck_cards = [(cards_by_id[card_id], d.orientations.get(card_id, "upright")) for card_id in d.order]

        return render_template(
            "deck/view.html",
            locale=locale,
            card_set=card_set,
            card_images_dir=card_images_dir,
            deck_cards=deck_cards,
            seed=seed,
        )

    return app

