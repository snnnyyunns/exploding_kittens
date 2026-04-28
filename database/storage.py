"""
storage.py — PostgreSQL persistence layer for Exploding Kittens.

Requires:
    pip install psycopg2-binary

Set the DATABASE_URL environment variable before running, e.g.:
    export DATABASE_URL="postgresql://user:password@localhost:5432/exploding_kittens"

Or configure individual variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os
import datetime
from typing import Any

import psycopg2
import psycopg2.extras


#  Connection config 

def _get_connection() -> "psycopg2.extensions.connection":
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 5432)),
            dbname=os.environ.get("DB_NAME", "exploding_kittens"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "ict555"),
        )
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _init_db(conn) -> None:
    """Create tables if they do not already exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id            SERIAL PRIMARY KEY,
                played_at     TEXT    NOT NULL,
                num_players   INTEGER NOT NULL,
                winner        TEXT    NOT NULL,
                turn_count    INTEGER NOT NULL,
                duration_secs INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS game_players (
                id        SERIAL PRIMARY KEY,
                game_id   INTEGER NOT NULL REFERENCES games(id),
                name      TEXT    NOT NULL,
                survived  INTEGER NOT NULL DEFAULT 0
            );
        """)
    conn.commit()


class GameStorage:
    """High-level API for reading and writing game records (PostgreSQL backend)."""

    def __init__(self) -> None:
        conn = _get_connection()
        _init_db(conn)
        conn.close()

    #  Write 

    def save_game(self, summary: dict, duration_secs: int) -> int:
        try:
            conn = _get_connection()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            winner = summary.get("winner") or "N/A"
            players = summary.get("players", [])
            survivors = set(summary.get("survivors", []))
            turns = summary.get("turn_count", 0)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO games (played_at, num_players, winner, turn_count, duration_secs)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (now, len(players), winner, turns, duration_secs),
                )
                game_id: int = cur.fetchone()["id"]

                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO game_players (game_id, name, survived) VALUES %s",
                    [(game_id, p, 1 if p in survivors else 0) for p in players],
                )
            conn.commit()
            return game_id
        except psycopg2.Error as exc:
            print(f"[storage] Error saving game: {exc}")
            return -1
        finally:
            conn.close()

    #  Read 

    def get_all_games(self) -> list[tuple[Any, ...]]:
        try:
            conn = _get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        g.played_at,
                        STRING_AGG(gp.name, ', ') AS players,
                        g.winner,
                        g.turn_count,
                        g.duration_secs || 's'
                    FROM games g
                    JOIN game_players gp ON gp.game_id = g.id
                    GROUP BY g.id
                    ORDER BY g.id DESC
                """)
                return [tuple(r.values()) for r in cur.fetchall()]
        except psycopg2.Error as exc:
            print(f"[storage] Error reading games: {exc}")
            return []
        finally:
            conn.close()

    def get_statistics(self) -> dict:
        try:
            conn = _get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS total FROM games")
                total = cur.fetchone()["total"]
                if total == 0:
                    return {"total_games": 0}

                cur.execute("""
                    SELECT name, COUNT(*) AS wins
                    FROM game_players WHERE survived = 1
                    GROUP BY name ORDER BY wins DESC LIMIT 1
                """)
                top = cur.fetchone()

                cur.execute("SELECT AVG(duration_secs) AS d, AVG(turn_count) AS t FROM games")
                avgs = cur.fetchone()

            return {
                "total_games": total,
                "top_player": top["name"] if top else "N/A",
                "top_player_wins": top["wins"] if top else 0,
                "avg_duration_secs": round(avgs["d"] or 0),
                "avg_turns": round(avgs["t"] or 0),
            }
        except psycopg2.Error as exc:
            print(f"[storage] Error reading stats: {exc}")
            return {}
        finally:
            conn.close()

    def get_player_wins(self) -> list[tuple[str, int]]:
        try:
            conn = _get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name, COUNT(*) AS wins
                    FROM game_players WHERE survived = 1
                    GROUP BY name ORDER BY wins DESC
                """)
                return [(r["name"], r["wins"]) for r in cur.fetchall()]
        except psycopg2.Error as exc:
            print(f"[storage] Error reading wins: {exc}")
            return []
        finally:
            conn.close()
