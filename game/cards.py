"""
cards.py — Card definitions, types, and deck creation for Exploding Kittens.
"""

import random
from enum import Enum


class CardType(Enum):
    EXPLODING_KITTEN = "Exploding Kitten"
    DEFUSE = "Defuse"
    ATTACK = "Attack"
    SKIP = "Skip"
    SEE_THE_FUTURE = "See the Future"
    SHUFFLE = "Shuffle"
    NOPE = "Nope"
    TACOCAT = "Tacocat"
    CATTERMELON = "Cattermelon"
    HAIRY_POTATO_CAT = "Hairy Potato Cat"
    RAINBOW_CAT = "Rainbow-Ralphing Cat"
    BEARD_CAT = "Beard Cat"


# Cat card types (require pairs to use)
CAT_CARDS = [
    CardType.TACOCAT,
    CardType.CATTERMELON,
    CardType.HAIRY_POTATO_CAT,
    CardType.RAINBOW_CAT,
    CardType.BEARD_CAT,
]

# Visual color per card type (hex strings for tkinter)
CARD_COLORS: dict[CardType, str] = {
    CardType.EXPLODING_KITTEN: "#D32F2F",
    CardType.DEFUSE:           "#388E3C",
    CardType.ATTACK:           "#B71C1C",
    CardType.SKIP:             "#1565C0",
    CardType.SEE_THE_FUTURE:   "#6A1B9A",
    CardType.SHUFFLE:          "#E65100",
    CardType.NOPE:             "#C62828",
    CardType.TACOCAT:          "#E91E8A",
    CardType.CATTERMELON:      "#2E7D32",
    CardType.HAIRY_POTATO_CAT: "#795548",
    CardType.RAINBOW_CAT:      "#7B1FA2",
    CardType.BEARD_CAT:        "#0277BD",
}

CARD_ICONS: dict[CardType, str] = {
    CardType.EXPLODING_KITTEN: "💥",
    CardType.DEFUSE:           "🔧",
    CardType.ATTACK:           "⚔️",
    CardType.SKIP:             "⏭",
    CardType.SEE_THE_FUTURE:   "🔮",
    CardType.SHUFFLE:          "🔀",
    CardType.NOPE:             "🚫",
    CardType.TACOCAT:          "🌮",
    CardType.CATTERMELON:      "🍉",
    CardType.HAIRY_POTATO_CAT: "🥔",
    CardType.RAINBOW_CAT:      "🌈",
    CardType.BEARD_CAT:        "🧔",
}

CARD_DESCRIPTIONS: dict[CardType, str] = {
    CardType.EXPLODING_KITTEN: "You explode unless you play a Defuse card!",
    CardType.DEFUSE:           "Disarm an Exploding Kitten when drawn.",
    CardType.ATTACK:           "End your turn without drawing. Next player takes 2 turns.",
    CardType.SKIP:             "End your turn without drawing a card.",
    CardType.SEE_THE_FUTURE:   "Secretly peek at the top 3 cards of the deck.",
    CardType.SHUFFLE:          "Shuffle the draw pile.",
    CardType.NOPE:             "Cancel any action except Exploding Kitten / Defuse.",
    CardType.TACOCAT:          "Play as a pair to steal a random card from a player.",
    CardType.CATTERMELON:      "Play as a pair to steal a random card from a player.",
    CardType.HAIRY_POTATO_CAT: "Play as a pair to steal a random card from a player.",
    CardType.RAINBOW_CAT:      "Play as a pair to steal a random card from a player.",
    CardType.BEARD_CAT:        "Play as a pair to steal a random card from a player.",
}


class Card:
    """Represents a single playing card."""

    def __init__(self, card_type: CardType) -> None:
        self.card_type = card_type
        self.name: str = card_type.value
        self.color: str = CARD_COLORS[card_type]
        self.icon: str = CARD_ICONS[card_type]
        self.description: str = CARD_DESCRIPTIONS[card_type]

    # ------------------------------------------------------------------ #
    def is_cat_card(self) -> bool:
        return self.card_type in CAT_CARDS

    def is_action_card(self) -> bool:
        """Returns True for cards that have an immediate effect when played."""
        return self.card_type in (
            CardType.ATTACK,
            CardType.SKIP,
            CardType.SEE_THE_FUTURE,
            CardType.SHUFFLE,
            CardType.NOPE,
        )

    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:
        return f"Card({self.name})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Card) and self.card_type == other.card_type

    def __hash__(self) -> int:
        return hash(self.card_type)


# ────────────────────────────────────────────────────────────────────────
# Deck factory
# ────────────────────────────────────────────────────────────────────────

def create_base_deck(num_players: int) -> list[Card]:
    """
    Build and shuffle a full deck *without* Exploding Kittens.
    Exploding Kittens are inserted separately after dealing.

    Composition (approximate standard deck):
        Attack      × 4
        Skip        × 4
        Nope        × 5
        See Future  × 5
        Shuffle     × 4
        Cat cards   × 4 each (5 types = 20 total)
        Defuse      × (num_players + 2), capped at 6
    """
    if not 2 <= num_players <= 5:
        raise ValueError("Number of players must be between 2 and 5.")

    deck: list[Card] = []

    # Action cards
    for _ in range(4):
        deck.append(Card(CardType.ATTACK))
        deck.append(Card(CardType.SKIP))
        deck.append(Card(CardType.SHUFFLE))

    for _ in range(5):
        deck.append(Card(CardType.NOPE))
        deck.append(Card(CardType.SEE_THE_FUTURE))

    # Cat cards – 4 of each type
    for cat_type in CAT_CARDS:
        for _ in range(4):
            deck.append(Card(cat_type))

    # Defuse cards
    num_defuse = min(num_players + 2, 6)
    for _ in range(num_defuse):
        deck.append(Card(CardType.DEFUSE))

    random.shuffle(deck)
    return deck
