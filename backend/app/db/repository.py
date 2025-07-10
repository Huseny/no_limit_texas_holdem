import dataclasses
import json
from typing import List, Optional
from app.db.connection import get_db_connection
from app.models.models import CompletedHand, GameState, Player
from psycopg2.extras import RealDictCursor, RealDictRow


class HandRepository:
    def save_completed_hand(self, hand: GameState):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO completed_hands (id, game_state) VALUES (%s, %s)",
                    (hand.hand_id, json.dumps(dataclasses.asdict(hand))),
                )
                conn.commit()

    def get_all_completed_hands(self) -> List[CompletedHand]:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, game_state FROM completed_hands ORDER BY created_at DESC"
                )
                rows = cur.fetchall()

                return [self._parse_completed_hand(row) for row in rows]

    def get_completed_hand_by_id(self, hand_id: str) -> Optional[CompletedHand]:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, game_state FROM completed_hands WHERE id = %s",
                    (hand_id,),
                )
                row = cur.fetchone()
                if row:
                    return self._parse_completed_hand(row)
                return None

    def _parse_completed_hand(self, row: RealDictRow) -> CompletedHand:
        game_state_data = row["game_state"]

        if "players" in game_state_data and game_state_data["players"] is not None:
            game_state_data["players"] = [
                Player(**p_data) for p_data in game_state_data["players"]
            ]

        game_state = GameState(**game_state_data)

        return CompletedHand(
            id=row["id"],
            game_state=game_state,
        )
