"""
logic.py — Game engine for Exploding Kittens.

Handles:
  - Game setup (deck creation, dealing)
  - Turn management (including Attack multi-turns)
  - Card effects (Attack, Skip, Nope, See the Future, Shuffle, cat pairs)
  - Exploding Kitten draw logic (defuse / elimination)
  - Win condition checking
  - Game-log accumulation
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from game.cards import Card, CardType, CAT_CARDS, create_base_deck
from game.player import Player



# Enums / simple data structures


class GamePhase(Enum):
    SETUP   = auto()
    PLAYING = auto()
    ENDED   = auto()


@dataclass
class ActionResult:
    """Value object returned by every public engine method."""
    success: bool
    message: str
    effect: Optional[str] = None          # descriptive effect key
    data: dict = field(default_factory=dict)



# GameEngine


class GameEngine:
    """
    Central controller for an Exploding Kittens game.

    Usage:
        engine = GameEngine(["Alice", "Bob", "Carol"])
        result = engine.play_card(CardType.SKIP)
        result = engine.draw_card()
    """


    # Construction / setup


    def __init__(self, player_names: list[str]) -> None:
        if not 2 <= len(player_names) <= 5:
            raise ValueError("Exploding Kittens requires 2–5 players.")
        if len(set(player_names)) != len(player_names):
            raise ValueError("All player names must be unique.")

        self.players: list[Player] = [
            Player(name.strip(), idx) for idx, name in enumerate(player_names)
        ]
        self.deck: list[Card] = []
        self.discard_pile: list[Card] = []
        self.phase: GamePhase = GamePhase.SETUP
        self.current_index: int = 0
        self.turn_number: int = 0
        self.winner: Optional[Player] = None
        self._log: list[str] = []

        self._setup()

    def _setup(self) -> None:
        """Deal cards and insert Exploding Kittens into shuffled deck."""
        num = len(self.players)
        deck = create_base_deck(num)

        # Each player gets 1 guaranteed Defuse + 4 random cards
        for player in self.players:
            defuse = self._pop_first(deck, CardType.DEFUSE)
            if defuse:
                player.add_card(defuse)
            for _ in range(4):
                if deck:
                    player.add_card(deck.pop())

        # Remaining deck cards go into the draw pile
        self.deck = deck

        # Insert (n-1) Exploding Kittens so exactly 1 player survives
        for _ in range(num - 1):
            self.deck.append(Card(CardType.EXPLODING_KITTEN))
        random.shuffle(self.deck)

        self.phase = GamePhase.PLAYING
        self.turn_number = 1
        self._log_msg(f"Game started! {num} players. Good luck!")
        self._log_msg(f"🎴 {self.current_player.name}'s turn — {self.deck_size} cards in deck.")


    # Public properties


    @property
    def current_player(self) -> Player:
        return self.players[self.current_index]

    @property
    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.is_alive]

    @property
    def deck_size(self) -> int:
        return len(self.deck)

    @property
    def is_over(self) -> bool:
        return self.phase == GamePhase.ENDED

    @property
    def log(self) -> list[str]:
        return list(self._log)

    def recent_log(self, n: int = 15) -> list[str]:
        return self._log[-n:]


    # Card playing


    def play_card(
        self,
        card_type: CardType,
        target: Optional[Player] = None,
    ) -> ActionResult:
        """
        Play one card from the current player's hand.

        Cat cards are automatically treated as a *pair*; the caller should
        only invoke this when the player has ≥ 2 of that cat type.
        A `target` player must be provided for cat-pair plays.
        """
        player = self.current_player
        if not player.has_card(card_type):
            return ActionResult(False, f"You don't have a {card_type.value} card.")

        # ── Nope is handled at GUI level before reaching here. ───────────
        # ── Defuse / Exploding Kitten are not played from hand manually. ─

        if card_type == CardType.ATTACK:
            return self._effect_attack(player)

        if card_type == CardType.SKIP:
            return self._effect_skip(player)

        if card_type == CardType.SEE_THE_FUTURE:
            return self._effect_see_future(player)

        if card_type == CardType.SHUFFLE:
            return self._effect_shuffle(player)

        if card_type == CardType.NOPE:
            # Nope played proactively doesn't do much on its own; GUI uses
            # play_nope_response instead.
            player.remove_card(CardType.NOPE)
            self.discard_pile.append(Card(CardType.NOPE))
            return ActionResult(True, "Nope played (no target effect).", "nope")

        if card_type in CAT_CARDS:
            return self._effect_cat_pair(player, card_type, target)

        return ActionResult(False, f"Cannot manually play {card_type.value}.")

    #  individual effects 

    def _effect_attack(self, player: Player) -> ActionResult:
        player.remove_card(CardType.ATTACK)
        self.discard_pile.append(Card(CardType.ATTACK))
        self._log_msg(f"⚔️  {player.name} plays Attack!")
        # End turn without drawing; next player inherits 2 turns
        self._advance_to_next(attacked=True)
        return ActionResult(True, "Attack! Next player takes 2 turns.", "attack")

    def _effect_skip(self, player: Player) -> ActionResult:
        player.remove_card(CardType.SKIP)
        self.discard_pile.append(Card(CardType.SKIP))
        self._log_msg(f"⏭  {player.name} plays Skip!")
        self._consume_turn_no_draw(player)
        return ActionResult(True, "Skipped! Turn ended without drawing.", "skip")

    def _effect_see_future(self, player: Player) -> ActionResult:
        player.remove_card(CardType.SEE_THE_FUTURE)
        self.discard_pile.append(Card(CardType.SEE_THE_FUTURE))
        self._log_msg(f"🔮 {player.name} peeks at the top of the deck.")
        top3 = [c.name for c in reversed(self.deck[-3:])] if self.deck else []
        return ActionResult(True, "Peeked at top 3 cards.", "see_future",
                            {"top3": top3})

    def _effect_shuffle(self, player: Player) -> ActionResult:
        player.remove_card(CardType.SHUFFLE)
        self.discard_pile.append(Card(CardType.SHUFFLE))
        random.shuffle(self.deck)
        self._log_msg(f"🔀 {player.name} shuffled the deck!")
        return ActionResult(True, "Deck shuffled!", "shuffle")

    def _effect_cat_pair(
        self, player: Player, card_type: CardType, target: Optional[Player]
    ) -> ActionResult:
        if not player.has_pair(card_type):
            return ActionResult(False, "You need a pair of cat cards!")
        if target is None or target == player:
            return ActionResult(False, "Select a different player to steal from.")
        if not target.is_alive:
            return ActionResult(False, f"{target.name} is already eliminated.")
        if target.card_count() == 0:
            return ActionResult(False, f"{target.name} has no cards to steal.")

        # Remove both copies from hand
        player.remove_card(card_type)
        player.remove_card(card_type)
        self.discard_pile.extend([Card(card_type), Card(card_type)])

        stolen = target.steal_random_card()
        if stolen:
            player.add_card(stolen)
            self._log_msg(
                f"🐱 {player.name} played a cat pair and stole a card from {target.name}!"
            )
            return ActionResult(
                True,
                f"Stole a card from {target.name}!",
                "cat_steal",
                {"stolen_card": stolen.name},
            )
        return ActionResult(False, "Target had no cards — steal failed.")


    # Nope response (called by GUI when a player reactively plays Nope)


    def play_nope(self, noping_player: Player) -> ActionResult:
        """Called when a player reactively plays a Nope card."""
        if not noping_player.has_card(CardType.NOPE):
            return ActionResult(False, f"{noping_player.name} has no Nope card.")
        noping_player.remove_card(CardType.NOPE)
        self.discard_pile.append(Card(CardType.NOPE))
        self._log_msg(f"🚫 {noping_player.name} played Nope!")
        return ActionResult(True, f"{noping_player.name} played Nope!", "nope")


    # Drawing


    def draw_card(self) -> ActionResult:
        """
        Draw the top card of the deck for the current player.
        Handles Exploding Kitten logic automatically.
        After a successful draw, advances to the next player if needed.
        """
        player = self.current_player
        if not self.deck:
            return ActionResult(False, "The deck is empty!")

        card = self.deck.pop()
        self._log_msg(f"{player.name} draws a card...")

        #  Exploding Kitten 
        if card.card_type == CardType.EXPLODING_KITTEN:
            return self._handle_exploding_kitten(player, card)

        #  Normal card 
        player.add_card(card)
        self._log_msg(f"  → {player.name} drew {card.icon} {card.name}.")
        self._consume_turn_after_draw(player)
        return ActionResult(True, f"Drew {card.name}.", "drew", {"card": card})

    def _handle_exploding_kitten(self, player: Player, bomb: Card) -> ActionResult:
        self._log_msg(f"💥 EXPLODING KITTEN drawn by {player.name}!")

        if player.has_card(CardType.DEFUSE):
            # Defuse it
            player.remove_card(CardType.DEFUSE)
            self.discard_pile.append(Card(CardType.DEFUSE))
            # Re-insert EK at a random position
            insert_pos = random.randint(0, len(self.deck))
            self.deck.insert(insert_pos, bomb)
            self._log_msg(f"🔧 {player.name} used a Defuse! EK back in the deck.")
            self._consume_turn_after_draw(player)
            return ActionResult(True, f"{player.name} defused the Exploding Kitten!",
                                "defused", {"insert_pos": insert_pos})

        # No defuse → eliminated
        player.eliminate()
        self.discard_pile.append(bomb)
        self._log_msg(f"💀 {player.name} has been eliminated!")
        self._check_winner()
        if not self.is_over:
            # Jump to next alive player without counting it as their turn
            self._skip_to_next_alive()
        return ActionResult(True, f"💥 {player.name} exploded and is eliminated!",
                            "exploded")


    # Turn management helpers


    def _consume_turn_after_draw(self, player: Player) -> None:
        """Decrement turn counter after drawing; advance when exhausted."""
        player.turns_remaining -= 1
        if player.turns_remaining <= 0:
            self._advance_to_next()

    def _consume_turn_no_draw(self, player: Player) -> None:
        """Skip / Attack already ended the turn without a draw."""
        player.turns_remaining -= 1
        if player.turns_remaining <= 0:
            self._advance_to_next()

    def _advance_to_next(self, attacked: bool = False) -> None:
        """Move current_index to the next alive player."""
        self._skip_to_next_alive()
        if attacked:
            self.current_player.turns_remaining += 1   # stacking attack
            if self.current_player.turns_remaining < 2:
                self.current_player.turns_remaining = 2
        else:
            if self.current_player.turns_remaining < 1:
                self.current_player.turns_remaining = 1
        self.turn_number += 1
        if not self.is_over:
            turns_txt = (
                f" ({self.current_player.turns_remaining} turns!)"
                if self.current_player.turns_remaining > 1 else ""
            )
            self._log_msg(
                f"🎴 {self.current_player.name}'s turn{turns_txt} — {self.deck_size} cards left."
            )

    def _skip_to_next_alive(self) -> None:
        """Rotate current_index to the next alive player (circular)."""
        for _ in range(len(self.players)):
            self.current_index = (self.current_index + 1) % len(self.players)
            if self.players[self.current_index].is_alive:
                return


    # Win condition


    def _check_winner(self) -> None:
        alive = self.alive_players
        if len(alive) == 1:
            self.winner = alive[0]
            self.phase = GamePhase.ENDED
            self._log_msg(f"🏆 {self.winner.name} is the last survivor and WINS!")


    # Summary / serialisation


    def get_summary(self) -> dict:
        return {
            "winner": self.winner.name if self.winner else None,
            "players": [p.name for p in self.players],
            "eliminated": [p.name for p in self.players if not p.is_alive],
            "survivors": [p.name for p in self.alive_players],
            "turn_count": self.turn_number,
        }


    # Utility


    @staticmethod
    def _pop_first(deck: list[Card], card_type: CardType) -> Optional[Card]:
        for i, c in enumerate(deck):
            if c.card_type == card_type:
                return deck.pop(i)
        return None

    def _log_msg(self, msg: str) -> None:
        self._log.append(msg)
