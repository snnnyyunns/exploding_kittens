# 💥 Exploding Kittens — Digital Edition

A faithful digital recreation of the Exploding Kittens card game, built with Python and Tkinter.

---

## 📋 Requirements

| Requirement | Version |
|---|---|
| Python | ≥ 3.10 |
| Tkinter | Bundled with Python (see note below) |
| SQLite3 | Bundled with Python |

> **Ubuntu / Debian users:** If you see `ModuleNotFoundError: No module named 'tkinter'`, install it with:
> ```bash
> sudo apt-get install python3-tk
> ```

---

## 🚀 How to Run (from scratch)

### Step 1 — Clone / Download the project

```bash
# If using git:
git clone <repo-url>
cd exploding_kittens

# Or unzip the project folder and cd into it
cd exploding_kittens
```

### Step 2 — Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Run the game

```bash
python main.py
```

---

## 🃏 How to Play

### Objective
Be the **last player alive** — avoid drawing an Exploding Kitten without a Defuse card.

### Setup
- Each player starts with **1 Defuse card + 4 random cards**.
- The deck contains **(number of players − 1)** Exploding Kittens.

### On Your Turn
1. **Play cards** from your hand (optional — you can play as many as you like before drawing).
2. **Draw a card** from the top of the deck.
   - If it's an **Exploding Kitten** and you have a **Defuse**: use it automatically — you survive!
   - If it's an **Exploding Kitten** and you have **no Defuse**: 💀 you're eliminated.

### Card Guide

| Card | Effect |
|------|--------|
| 💥 Exploding Kitten | You explode unless you have a Defuse |
| 🔧 Defuse | Saves you from an Exploding Kitten |
| ⚔️ Attack | End your turn without drawing; next player takes 2 turns |
| ⏭ Skip | End your turn without drawing |
| 🔮 See the Future | Peek at the top 3 cards of the deck |
| 🔀 Shuffle | Shuffle the draw pile |
| 🚫 Nope | Cancel another player's action (played reactively) |
| 🐱 Cat Cards | Play as a **pair** to steal a random card from another player |

### Winning
The last player still alive wins the game!

---

## 🗂 Project Structure

```
exploding_kittens/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── README.md
│
├── game/                    # Core game logic (no GUI code)
│   ├── __init__.py
│   ├── cards.py             # CardType enum, Card class, deck factory
│   ├── player.py            # Player class and hand management
│   └── logic.py             # GameEngine — rules, turns, effects
│
├── gui/                     # Tkinter user interface
│   ├── __init__.py
│   └── app.py               # App (root), all Screen subclasses, CardWidget
│
├── database/                # Data persistence
│   ├── __init__.py
│   └── storage.py           # SQLite CRUD via GameStorage class
│
├── utils/                   # Shared helpers
│   ├── __init__.py
│   └── helpers.py           # Formatting, validation, utility functions
│
└── data/                    # Created automatically at runtime
    └── game_records.db      # SQLite database
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: tkinter` | `sudo apt-get install python3-tk` |
| Window looks blank | Make sure you activated the venv |
| Database errors | Delete `data/game_records.db` and restart |
