"""
app.py — Tkinter GUI for Exploding Kittens Digital Edition.

Screens:
    MainMenuScreen  → splash / navigation
    SetupScreen     → enter player names
    GameScreen      → main gameplay
    HistoryScreen   → leaderboard / game records
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import Optional, Callable

from game.cards import Card, CardType, CAT_CARDS, CARD_COLORS, CARD_ICONS
from game.logic import GameEngine
from game.player import Player
from database.storage import GameStorage
from utils.helpers import validate_player_names, format_duration

# ────────────────────────────────────────────────────────────────────────
# Design tokens
# ────────────────────────────────────────────────────────────────────────

T = {
    "bg":        "#1a1a2e",
    "surface":   "#16213e",
    "card_bg":   "#0f3460",
    "accent":    "#e94560",
    "accent2":   "#f5a623",
    "green":     "#27ae60",
    "text":      "#f0f0f0",
    "text_dim":  "#8899aa",
    "white":     "#ffffff",
    "danger":    "#e74c3c",
    "border":    "#2a2a4a",
    "selected":  "#FFD700",
}

FONT_TITLE  = ("Segoe UI", 28, "bold")
FONT_H2     = ("Segoe UI", 16, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Courier New", 10)
FONT_CARD   = ("Segoe UI", 8, "bold")
FONT_ICON   = ("Segoe UI Emoji", 20)
FONT_ICON_S = ("Segoe UI Emoji", 14)

# ────────────────────────────────────────────────────────────────────────
# Reusable widgets
# ────────────────────────────────────────────────────────────────────────

def flat_btn(
    parent,
    text: str,
    command: Callable,
    bg: str = T["surface"],
    fg: str = T["text"],
    font=FONT_BODY,
    padx: int = 16,
    pady: int = 8,
    **kw,
) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        font=font,
        relief="flat",
        cursor="hand2",
        activebackground=T["accent2"],
        activeforeground=T["white"],
        padx=padx,
        pady=pady,
        **kw,
    )


def label(
    parent,
    text: str,
    font=FONT_BODY,
    fg: str = T["text"],
    bg: str = T["bg"],
    **kw,
) -> tk.Label:
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)


# ────────────────────────────────────────────────────────────────────────
# Card widget
# ────────────────────────────────────────────────────────────────────────

class CardWidget(tk.Canvas):
    """
    A clickable card rendered on a Canvas.
    Width/height in pixels; selected cards get a gold border.
    """

    W, H = 78, 108

    def __init__(
        self,
        parent,
        card: Card,
        on_click: Optional[Callable] = None,
        selected: bool = False,
        **kw,
    ) -> None:
        super().__init__(
            parent,
            width=self.W,
            height=self.H,
            bg=T["bg"],
            highlightthickness=3,
            highlightbackground=T["selected"] if selected else "#333355",
            cursor="hand2" if on_click else "arrow",
            **kw,
        )
        self.card = card
        self._draw(selected)
        if on_click:
            self.bind("<Button-1>", lambda _e: on_click(card))

    def _draw(self, selected: bool) -> None:
        w, h = self.W, self.H
        # Background fill
        self.create_rectangle(0, 0, w, h, fill=self.card.color, outline="")

        # Subtle diagonal stripe overlay for texture
        for x in range(-h, w, 14):
            self.create_line(x, 0, x + h, h, fill="#ffffff15", width=6)

        # Icon
        self.create_text(w // 2, h // 2 - 12, text=self.card.icon,
                         font=FONT_ICON, fill="white")

        # Card name (wrapped)
        name = self.card.name
        if len(name) > 12:
            words = name.split()
            mid = max(1, len(words) // 2)
            name = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
        self.create_text(w // 2, h - 16, text=name,
                         font=FONT_CARD, fill="white",
                         width=w - 6, justify="center")

        # "SELECTED" banner
        if selected:
            self.create_rectangle(0, 0, w, 16, fill=T["selected"], outline="")
            self.create_text(w // 2, 8, text="SELECTED",
                             font=("Segoe UI", 7, "bold"), fill="#000")


# ────────────────────────────────────────────────────────────────────────
# Screen base
# ────────────────────────────────────────────────────────────────────────

class Screen(tk.Frame):
    """Base class for all top-level screens."""

    def __init__(self, parent: "App") -> None:
        super().__init__(parent, bg=T["bg"])

    def _section(self, title: str) -> tk.Frame:
        """Helper: labelled section separator."""
        f = tk.Frame(self, bg=T["bg"])
        f.pack(fill="x", padx=16, pady=(8, 2))
        label(f, title, font=("Segoe UI", 10, "bold"), fg=T["text_dim"]).pack(side="left")
        tk.Frame(f, bg=T["border"], height=1).pack(side="left", fill="x", expand=True, padx=8)
        return f


# ────────────────────────────────────────────────────────────────────────
# Main Menu
# ────────────────────────────────────────────────────────────────────────

class MainMenuScreen(Screen):
    def __init__(self, parent: "App") -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        # Hero area
        hero = tk.Frame(self, bg=T["bg"])
        hero.pack(expand=True)

        label(hero, "💥", font=("Segoe UI Emoji", 80), bg=T["bg"]).pack(pady=(60, 0))
        label(hero, "EXPLODING KITTENS", font=FONT_TITLE, fg=T["accent"]).pack()
        label(hero, "Digital Edition", font=FONT_BODY, fg=T["text_dim"]).pack(pady=(0, 40))

        # Buttons
        app: "App" = self.master  # type: ignore[assignment]
        for text, cmd, colour in [
            ("🎮   New Game",      app.show_setup,   T["accent"]),
            ("📊   Game History",  app.show_history,  T["card_bg"]),
            ("❌   Quit",          app.quit,           "#3a3a5c"),
        ]:
            flat_btn(hero, text, cmd, bg=colour, font=FONT_H2,
                     padx=30, pady=12, width=22).pack(pady=6)

        label(hero, "2 – 5 players  ·  Survive the kitten",
              font=FONT_SMALL, fg=T["text_dim"]).pack(pady=(30, 0))


# ────────────────────────────────────────────────────────────────────────
# Setup Screen
# ────────────────────────────────────────────────────────────────────────

class SetupScreen(Screen):
    def __init__(self, parent: "App") -> None:
        super().__init__(parent)
        self._entries: list[tk.Entry] = []
        self._build()

    def _build(self) -> None:
        label(self, "🎴  Game Setup", font=FONT_TITLE, fg=T["text"]).pack(pady=(30, 4))
        label(self, "Enter player names (2 – 5 players)",
              font=FONT_BODY, fg=T["text_dim"]).pack(pady=(0, 20))

        form = tk.Frame(self, bg=T["bg"])
        form.pack()

        defaults = ["Alice", "Bob", "", "", ""]
        for i in range(5):
            row = tk.Frame(form, bg=T["bg"])
            row.pack(pady=5)
            label(row, f"Player {i + 1}", font=FONT_BODY, fg=T["text_dim"],
                  width=10, anchor="e").pack(side="left")
            e = tk.Entry(row, font=FONT_BODY, width=22,
                         bg=T["surface"], fg=T["text"],
                         insertbackground=T["text"], relief="flat")
            e.pack(side="left", padx=(8, 0), ipady=6)
            if defaults[i]:
                e.insert(0, defaults[i])
            self._entries.append(e)

        btn_row = tk.Frame(self, bg=T["bg"])
        btn_row.pack(pady=28)

        app: "App" = self.master  # type: ignore[assignment]
        flat_btn(btn_row, "← Back", app.show_main_menu,
                 bg=T["surface"], padx=20, pady=10).pack(side="left", padx=8)
        flat_btn(btn_row, "Start Game →", self._on_start,
                 bg=T["accent"], font=FONT_H2, padx=20, pady=10).pack(side="left", padx=8)

    def _on_start(self) -> None:
        names = [e.get().strip() for e in self._entries if e.get().strip()]
        ok, msg = validate_player_names(names)
        if not ok:
            messagebox.showerror("Invalid Setup", msg, parent=self)
            return
        app: "App" = self.master  # type: ignore[assignment]
        app.start_game(names)


# ────────────────────────────────────────────────────────────────────────
# Game Screen
# ────────────────────────────────────────────────────────────────────────

class GameScreen(Screen):
    """
    Layout:
        ┌─────────────────────────────────────────┐
        │  Other players status bar               │  ← players_bar
        ├──────────────┬──────────────────────────┤
        │  Deck panel  │  Game log                │  ← middle
        ├──────────────┴──────────────────────────┤
        │  Turn banner                            │  ← turn_banner
        ├─────────────────────────────────────────┤
        │  Hand label + action buttons            │  ← hand_header
        │  [Card][Card][Card]...                  │  ← hand_area
        └─────────────────────────────────────────┘
    """

    def __init__(self, parent: "App", engine: GameEngine, storage: GameStorage) -> None:
        super().__init__(parent)
        self.engine = engine
        self.storage = storage
        self._selected: list[CardType] = []          # selected card types
        self._start_time = datetime.datetime.now()
        self._draw_pending = True                     # must draw before ending turn
        self._build()
        self.refresh()

    # ------------------------------------------------------------------ #
    # Layout construction
    # ------------------------------------------------------------------ #

    def _build(self) -> None:
        # ── Other players bar ───────────────────────────────────────────
        self._players_bar = tk.Frame(self, bg=T["surface"], pady=4)
        self._players_bar.pack(fill="x")

        # ── Middle row ──────────────────────────────────────────────────
        mid = tk.Frame(self, bg=T["bg"])
        mid.pack(fill="both", expand=True, padx=10, pady=6)

        # Deck panel (left)
        deck_panel = tk.Frame(mid, bg=T["surface"], padx=12, pady=12)
        deck_panel.pack(side="left", fill="y")

        label(deck_panel, "DRAW PILE", font=("Segoe UI", 9, "bold"),
              fg=T["text_dim"], bg=T["surface"]).pack()
        self._deck_count = label(deck_panel, "0",
                                 font=("Segoe UI", 40, "bold"),
                                 fg=T["accent2"], bg=T["surface"])
        self._deck_count.pack(pady=4, ipadx=10)
        label(deck_panel, "cards", font=FONT_SMALL,
              fg=T["text_dim"], bg=T["surface"]).pack()

        tk.Frame(deck_panel, bg=T["border"], height=1).pack(fill="x", pady=10)

        self._draw_btn = flat_btn(
            deck_panel, "🃏 Draw Card", self._on_draw,
            bg=T["accent"], font=("Segoe UI", 10, "bold"),
            padx=8, pady=8,
        )
        self._draw_btn.pack(fill="x")

        # Discard count label
        self._discard_label = label(deck_panel, "Discard: 0",
                                    font=FONT_SMALL, fg=T["text_dim"], bg=T["surface"])
        self._discard_label.pack(pady=(6, 0))

        # Game log (right)
        log_frame = tk.Frame(mid, bg=T["bg"])
        log_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

        label(log_frame, "📜 Game Log", font=("Segoe UI", 10, "bold"),
              fg=T["text_dim"]).pack(anchor="w")

        self._log_box = tk.Text(
            log_frame,
            height=9,
            bg=T["surface"],
            fg=T["text"],
            font=FONT_MONO,
            relief="flat",
            state="disabled",
            wrap="word",
            padx=6,
            pady=4,
        )
        self._log_box.pack(fill="both", expand=True)
        sb = tk.Scrollbar(log_frame, command=self._log_box.yview)
        self._log_box.configure(yscrollcommand=sb.set)

        # ── Turn banner ─────────────────────────────────────────────────
        self._turn_banner = label(self, "", font=FONT_H2,
                                  bg=T["accent"], fg=T["white"], pady=6)
        self._turn_banner.pack(fill="x", padx=10, pady=(2, 0))

        # ── Hand header ─────────────────────────────────────────────────
        hh = tk.Frame(self, bg=T["bg"])
        hh.pack(fill="x", padx=10, pady=(6, 2))

        label(hh, "Your Hand:", font=("Segoe UI", 10, "bold"), fg=T["text"]).pack(side="left")

        # Action buttons
        btn_area = tk.Frame(hh, bg=T["bg"])
        btn_area.pack(side="right")

        self._play_btn = flat_btn(
            btn_area, "▶  Play Selected", self._on_play,
            bg=T["green"], font=("Segoe UI", 9, "bold"),
            padx=10, pady=5, state="disabled",
        )
        self._play_btn.pack(side="left", padx=4)

        flat_btn(btn_area, "✕  Clear", self._clear_selection,
                 bg=T["surface"], font=("Segoe UI", 9),
                 padx=10, pady=5).pack(side="left", padx=4)

        flat_btn(btn_area, "🏳  Forfeit", self._forfeit,
                 bg="#3a3a5c", font=("Segoe UI", 9),
                 padx=10, pady=5).pack(side="left", padx=4)

        # ── Hand area ────────────────────────────────────────────────────
        hand_outer = tk.Frame(self, bg=T["bg"])
        hand_outer.pack(fill="x", padx=10, pady=(0, 8))

        # Scrollable hand (horizontal)
        self._hand_canvas = tk.Canvas(hand_outer, bg=T["bg"],
                                      height=CardWidget.H + 12, highlightthickness=0)
        self._hand_canvas.pack(side="left", fill="x", expand=True)

        h_scroll = tk.Scrollbar(hand_outer, orient="horizontal",
                                command=self._hand_canvas.xview)
        h_scroll.pack(side="bottom", fill="x")
        self._hand_canvas.configure(xscrollcommand=h_scroll.set)

        self._hand_inner = tk.Frame(self._hand_canvas, bg=T["bg"])
        self._hand_canvas.create_window((0, 0), window=self._hand_inner, anchor="nw")
        self._hand_inner.bind("<Configure>", lambda _e: self._hand_canvas.configure(
            scrollregion=self._hand_canvas.bbox("all")
        ))

    # ------------------------------------------------------------------ #
    # Refresh / render
    # ------------------------------------------------------------------ #

    def refresh(self) -> None:
        if self.engine.is_over:
            self._end_game()
            return

        engine = self.engine
        current = engine.current_player

        # Deck / discard counts
        self._deck_count.config(text=str(engine.deck_size))
        self._discard_label.config(text=f"Discard: {len(engine.discard_pile)}")

        # Turn banner
        t = current.turns_remaining
        extra = f"  ({t} turns left)" if t > 1 else ""
        self._turn_banner.config(text=f"⚡ {current.name}'s Turn{extra}")

        # Players bar
        for w in self._players_bar.winfo_children():
            w.destroy()

        for p in engine.players:
            is_cur = (p == current)
            alive = p.is_alive
            icon = "💀" if not alive else ("⚡" if is_cur else "👤")
            bg = T["accent"] if is_cur else (T["surface"] if alive else "#2a2a2a")
            fg = T["white"] if is_cur else (T["text"] if alive else T["text_dim"])
            txt = f"{icon} {p.name}  [{p.card_count()}]"
            label(self._players_bar, txt, font=("Segoe UI", 10, "bold"),
                  bg=bg, fg=fg).pack(side="left", padx=3, pady=3, ipadx=8, ipady=4)

        # Game log
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        for line in engine.recent_log(20):
            self._log_box.insert("end", f"  {line}\n")
        self._log_box.see("end")
        self._log_box.config(state="disabled")

        # Hand
        self._render_hand(current)

    def _render_hand(self, player: Player) -> None:
        for w in self._hand_inner.winfo_children():
            w.destroy()

        selected_set = set(self._selected)
        sel_counts: dict[CardType, int] = {}
        for ct in self._selected:
            sel_counts[ct] = sel_counts.get(ct, 0) + 1

        counts_drawn: dict[CardType, int] = {}
        for card in player.hand:
            ct = card.card_type
            drawn = counts_drawn.get(ct, 0)
            sel_n = sel_counts.get(ct, 0)
            selected = drawn < sel_n
            counts_drawn[ct] = drawn + 1

            f = tk.Frame(self._hand_inner, bg=T["bg"])
            f.pack(side="left", padx=3, pady=4)
            CardWidget(f, card, on_click=self._toggle_card, selected=selected).pack()

        self._play_btn.config(state="normal" if self._selected else "disabled")

    # ------------------------------------------------------------------ #
    # Card selection
    # ------------------------------------------------------------------ #

    def _toggle_card(self, card: Card) -> None:
        ct = card.card_type
        current = sel_count = self._selected.count(ct)

        if ct in self._selected:
            # De-select one
            self._selected.remove(ct)
        else:
            if card.is_cat_card():
                p = self.engine.current_player
                if not p.has_pair(ct):
                    messagebox.showinfo(
                        "Need a Pair",
                        f"You need 2 {card.name} cards to play them together.",
                        parent=self,
                    )
                    return
                # Select the pair
                self._selected.clear()
                self._selected.extend([ct, ct])
            else:
                self._selected.clear()
                self._selected.append(ct)

        self._render_hand(self.engine.current_player)

    def _clear_selection(self) -> None:
        self._selected.clear()
        self._render_hand(self.engine.current_player)

    # ------------------------------------------------------------------ #
    # Card play
    # ------------------------------------------------------------------ #

    def _on_play(self) -> None:
        if not self._selected:
            return

        ct = self._selected[0]
        player = self.engine.current_player

        # ── Nope check for other players ────────────────────────────────
        if ct not in (CardType.DEFUSE, CardType.EXPLODING_KITTEN):
            if self._prompt_nope(player, ct):
                self._selected.clear()
                self.refresh()
                return

        # ── Cat pair: choose target ─────────────────────────────────────
        target: Optional[Player] = None
        if ct in CAT_CARDS:
            target = self._pick_target()
            if target is None:
                return

        result = self.engine.play_card(ct, target=target)

        if not result.success:
            messagebox.showerror("Cannot Play", result.message, parent=self)
            return

        # ── See the Future pop-up ───────────────────────────────────────
        if result.effect == "see_future":
            top3 = result.data.get("top3", [])
            body = (
                "\n".join(f"  {i+1}. {n}" for i, n in enumerate(top3))
                if top3 else "  (The deck is empty)"
            )
            messagebox.showinfo("🔮 See the Future",
                                f"Top cards (closest first):\n{body}", parent=self)

        # ── Cat steal notification ───────────────────────────────────────
        if result.effect == "cat_steal":
            stolen = result.data.get("stolen_card", "a card")
            messagebox.showinfo("🐱 Cat Steal!",
                                f"You stole: {stolen}", parent=self)

        self._selected.clear()
        if self.engine.is_over:
            self._end_game()
        else:
            self.refresh()

    def _prompt_nope(self, playing: Player, ct: CardType) -> bool:
        """Ask each other alive player (with a Nope) if they want to react."""
        for p in self.engine.alive_players:
            if p == playing or not p.has_card(CardType.NOPE):
                continue
            card_name = ct.value
            answer = messagebox.askyesno(
                "🚫 Nope?",
                f"{p.name}, {playing.name} is about to play {card_name}.\n\n"
                f"You have a Nope card — do you want to cancel it?",
                parent=self,
            )
            if answer:
                r = self.engine.play_nope(p)
                messagebox.showinfo("Noped!", r.message, parent=self)
                return True
        return False

    def _pick_target(self) -> Optional[Player]:
        """Modal dialog to choose a steal target."""
        options = [
            p for p in self.engine.alive_players
            if p != self.engine.current_player and p.card_count() > 0
        ]
        if not options:
            messagebox.showinfo("No Targets",
                                "No other players have cards to steal from.", parent=self)
            return None

        dialog = tk.Toplevel(self)
        dialog.title("Choose a Target")
        dialog.configure(bg=T["bg"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        chosen: list[Optional[Player]] = [None]

        label(dialog, "Steal from which player?",
              font=FONT_H2, fg=T["text"]).pack(pady=(20, 10), padx=24)

        for p in options:
            flat_btn(
                dialog,
                f"👤 {p.name}  ({p.card_count()} cards)",
                lambda pl=p: [chosen.__setitem__(0, pl), dialog.destroy()],
                bg=T["surface"], font=FONT_BODY,
                padx=12, pady=8,
            ).pack(fill="x", padx=24, pady=4)

        flat_btn(dialog, "Cancel", dialog.destroy,
                 bg="#3a3a5c", pady=6).pack(pady=(8, 16), padx=24, fill="x")

        dialog.wait_window()
        return chosen[0]

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #

    def _on_draw(self) -> None:
        result = self.engine.draw_card()
        if not result.success:
            messagebox.showerror("Error", result.message, parent=self)
            return

        effect = result.effect
        if effect == "exploded":
            messagebox.showwarning("💥 BOOM!",
                                   result.message + "\n\nBetter luck next time!", parent=self)
        elif effect == "defused":
            messagebox.showinfo("🔧 Defused!", result.message, parent=self)
        else:
            card = result.data.get("card")
            if card:
                messagebox.showinfo(
                    "Card Drawn",
                    f"You drew:\n\n{card.icon}  {card.name}\n\n{card.description}",
                    parent=self,
                )

        self._selected.clear()
        if self.engine.is_over:
            self._end_game()
        else:
            self.refresh()

    # ------------------------------------------------------------------ #
    # Forfeit
    # ------------------------------------------------------------------ #

    def _forfeit(self) -> None:
        p = self.engine.current_player
        if not messagebox.askyesno(
            "Forfeit?",
            f"{p.name}, are you sure you want to forfeit?\n"
            "You will be eliminated from the game.",
            parent=self,
        ):
            return
        p.eliminate()
        self.engine._log_msg(f"🏳 {p.name} forfeited.")
        self.engine._check_winner()
        if self.engine.is_over:
            self._end_game()
        else:
            self.engine._advance_to_next()
            self._selected.clear()
            self.refresh()

    # ------------------------------------------------------------------ #
    # End game
    # ------------------------------------------------------------------ #

    def _end_game(self) -> None:
        summary = self.engine.get_summary()
        winner = summary.get("winner", "Unknown")
        turns = summary.get("turn_count", 0)
        duration = int((datetime.datetime.now() - self._start_time).total_seconds())

        try:
            self.storage.save_game(summary, duration)
        except Exception as exc:
            print(f"[GameScreen] Failed to save game: {exc}")

        elim = summary.get("eliminated", [])
        elim_txt = f"\nEliminated: {', '.join(elim)}" if elim else ""
        messagebox.showinfo(
            "🎉 Game Over!",
            f"🏆  {winner} wins!\n\n"
            f"Turns played: {turns}\n"
            f"Duration: {format_duration(duration)}"
            f"{elim_txt}",
            parent=self,
        )
        app: "App" = self.master  # type: ignore[assignment]
        app.show_main_menu()


# ────────────────────────────────────────────────────────────────────────
# History Screen
# ────────────────────────────────────────────────────────────────────────

class HistoryScreen(Screen):
    def __init__(self, parent: "App", storage: GameStorage) -> None:
        super().__init__(parent)
        self.storage = storage
        self._build()

    def _build(self) -> None:
        label(self, "📊  Game History", font=FONT_TITLE, fg=T["text"]).pack(pady=(28, 6))

        # Stats bar
        stats = self.storage.get_statistics()
        if stats.get("total_games"):
            top = stats.get("top_player", "–")
            wins = stats.get("top_player_wins", 0)
            avg_t = stats.get("avg_turns", 0)
            stats_txt = (
                f"  Total games: {stats['total_games']}  ·  "
                f"Top player: {top} ({wins} win{'s' if wins != 1 else ''})  ·  "
                f"Avg turns: {avg_t}  "
            )
        else:
            stats_txt = "  No games played yet."

        label(self, stats_txt, font=FONT_BODY, fg=T["text_dim"],
              bg=T["surface"]).pack(fill="x", ipadx=4, ipady=6)

        # Treeview
        cols = ("Date", "Players", "Winner", "Turns", "Duration")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("EK.Treeview",
                        background=T["surface"],
                        foreground=T["text"],
                        fieldbackground=T["surface"],
                        rowheight=28,
                        font=FONT_BODY)
        style.configure("EK.Treeview.Heading",
                        background=T["accent"],
                        foreground=T["white"],
                        font=("Segoe UI", 10, "bold"),
                        relief="flat")
        style.map("EK.Treeview",
                  background=[("selected", T["card_bg"])],
                  foreground=[("selected", T["white"])])

        frame = tk.Frame(self, bg=T["bg"])
        frame.pack(fill="both", expand=True, padx=16, pady=10)

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                             style="EK.Treeview", selectmode="browse")
        widths = [130, 220, 120, 70, 80]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        for row in self.storage.get_all_games():
            tree.insert("", "end", values=row)

        # Leaderboard
        self._section("🏆  Win Leaderboard")
        lb_frame = tk.Frame(self, bg=T["bg"])
        lb_frame.pack(fill="x", padx=16, pady=(4, 0))

        winners = self.storage.get_player_wins()
        if winners:
            for rank, (name, wins) in enumerate(winners[:5], 1):
                medal = ["🥇", "🥈", "🥉", "4.", "5."][rank - 1]
                label(lb_frame,
                      f"  {medal}  {name}  —  {wins} win{'s' if wins != 1 else ''}",
                      font=FONT_BODY, fg=T["text"]).pack(anchor="w")
        else:
            label(lb_frame, "  No wins recorded yet.", font=FONT_BODY,
                  fg=T["text_dim"]).pack(anchor="w")

        app: "App" = self.master  # type: ignore[assignment]
        flat_btn(self, "← Back to Menu", app.show_main_menu,
                 bg=T["surface"], font=FONT_BODY,
                 padx=20, pady=10).pack(pady=16)


# ────────────────────────────────────────────────────────────────────────
# Application root
# ────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    """Root Tk window — owns screen navigation and shared resources."""

    def __init__(self) -> None:
        super().__init__()
        self.title("💥 Exploding Kittens — Digital Edition")
        self.configure(bg=T["bg"])
        self.geometry("940x720")
        self.minsize(820, 620)

        # Shared storage
        self.storage = GameStorage()

        # Currently displayed screen
        self._screen: Optional[Screen] = None
        self.show_main_menu()

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    def _set_screen(self, screen: Screen) -> None:
        if self._screen is not None:
            self._screen.destroy()
        self._screen = screen
        screen.pack(fill="both", expand=True)

    def show_main_menu(self) -> None:
        self._set_screen(MainMenuScreen(self))

    def show_setup(self) -> None:
        self._set_screen(SetupScreen(self))

    def show_history(self) -> None:
        self._set_screen(HistoryScreen(self, self.storage))

    def start_game(self, player_names: list[str]) -> None:
        try:
            engine = GameEngine(player_names)
            self._set_screen(GameScreen(self, engine, self.storage))
        except ValueError as exc:
            messagebox.showerror("Setup Error", str(exc), parent=self)
