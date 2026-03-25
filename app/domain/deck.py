from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

from app.domain.cards import Orientation


@dataclass(slots=True)
class Deck:
    order: list[str] = field(default_factory=list)
    orientations: dict[str, Orientation] = field(default_factory=dict)

    def reset(self, card_ids: list[str], *, seed: int | None = None) -> None:
        self.order = list(card_ids)
        self.orientations = {}
        self.shuffle(seed=seed)

    def shuffle(self, *, seed: int | None = None) -> None:
        rng = random.Random(seed)
        rng.shuffle(self.order)

        self.orientations = {
            card_id: ("reversed" if rng.random() < 0.5 else "upright") for card_id in self.order
        }

    def draw(self, n: int) -> list[tuple[str, Orientation]]:
        if n < 0:
            raise ValueError("n must be >= 0")

        drawn: list[tuple[str, Orientation]] = []
        for _ in range(min(n, len(self.order))):
            card_id = self.order.pop(0)
            orientation: Literal["upright", "reversed"] = self.orientations.get(card_id, "upright")
            drawn.append((card_id, orientation))
        return drawn

