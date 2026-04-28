"""
player.py — Player model for Exploding Kittens.
"""

import random
from game.cards import Card, CardType


class Player:
    """Represents a single game participant."""

    def __init__(self, name: str, player_id: int) -> None:
        self.name: str = name
        self.player_id: int = player_id
        self.hand: list[Card] = []
        self.is_alive: bool = True
        self.turns_remaining: int = 1   # Increases to 2 when attacked


    # Hand management


    def add_card(self, card: Card) -> None:
        self.hand.append(card)

    def remove_card(self, card_type: CardType) -> Card | None:
        """Remove and return the first card of the given type, or None."""
        for i, c in enumerate(self.hand):
            if c.card_type == card_type:
                return self.hand.pop(i)
        return None

    def has_card(self, card_type: CardType) -> bool:
        return any(c.card_type == card_type for c in self.hand)

    def count_card(self, card_type: CardType) -> int:
        return sum(1 for c in self.hand if c.card_type == card_type)

    def has_pair(self, card_type: CardType) -> bool:
        return self.count_card(card_type) >= 2

    def steal_random_card(self) -> Card | None:
        """Return a random card from hand (removed); None if empty."""
        if not self.hand:
            return None
        card = random.choice(self.hand)
        self.hand.remove(card)
        return card

    def card_count(self) -> int:
        return len(self.hand)


    # State helpers


    def eliminate(self) -> None:
        self.is_alive = False
        self.hand.clear()   # eliminated players lose their hand

    def __repr__(self) -> str:
        status = "alive" if self.is_alive else "dead"
        return f"Player(name={self.name!r}, {status}, cards={self.card_count()})"
