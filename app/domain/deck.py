from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

Orientation = Literal["upright", "reversed"]


@dataclass(slots=True)
class Deck:
    order: list[int] = field(default_factory=list)
    orientations: dict[int, Orientation] = field(default_factory=dict)

    def reset(self, card_ids: list[int], *, seed: int | None = None) -> None:
        """
        Nastaví deck do "nového" stavu:
        - `order` je sekvenčný v poradí dodaných `card_ids`
        - všetky karty sú orientované ako `upright`

        `seed` je tu len pre kompatibilitu podpisu; pri `reset()` sa nepoužíva
        (orientácie sú vždy upright).
        """
        _ = seed
        self.order = list(card_ids)
        self.orientations = {card_id: "upright" for card_id in self.order}

    def init(self, card_ids: list[int], *, seed: int | None = None) -> None:
        """Alias pre `reset()` (API pre "reset/init")."""
        self.reset(card_ids, seed=seed)

    def shuffle(self, *, seed: int | None = None) -> None:
        """
        Zamieša karty a nastaví im náhodnú orientáciu.

        Výsledok:
        - karty nie sú v pôvodnom poradí (neidú za sebou)
        - každá karta má 50/50 šancu byť `upright` alebo `reversed`
        """
        rng = random.Random(seed)
        rng.shuffle(self.order)

        self.orientations = {
            card_id: ("reversed" if rng.random() < 0.5 else "upright") for card_id in self.order
        }

    def draw(self, n: int) -> list[tuple[int, Orientation]]:
        if n < 0:
            raise ValueError("n must be >= 0")

        drawn: list[tuple[int, Orientation]] = []
        for _ in range(min(n, len(self.order))):
            card_id = self.order.pop(0)
            orientation: Literal["upright", "reversed"] = self.orientations.get(card_id, "upright")
            drawn.append((card_id, orientation))
        return drawn

