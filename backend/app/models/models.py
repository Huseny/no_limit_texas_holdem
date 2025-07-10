from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Union
import uuid
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------------
# Data models for the poker game
# ----------------------------------------------------------------------------


@dataclass
class Player:
    player_id: str
    stack: int
    cards: List[str] = field(default_factory=list)
    current_bet_in_round: int = 0
    status: str = "active"
    position: str = ""
    is_dealer: Optional[bool] = False
    is_small_blind: Optional[bool] = False
    is_big_blind: Optional[bool] = False


@dataclass
class GameState:
    hand_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pot: int = 0
    current_street: str = "preflop"
    current_bet: int = 0
    board_cards: List[str] = field(default_factory=list)
    players: List[Player] = field(default_factory=list)
    active_player_id: Optional[str] = None
    main_log: List[str] = field(default_factory=list)
    actions_log: List[str] = field(default_factory=list)
    winnings: Optional[Dict[str, int]] = None


@dataclass
class CompletedHand:
    id: str
    game_state: GameState


# ----------------------------------------------------------------------------
# Request models for API endpoints
# ----------------------------------------------------------------------------


class CreateHandRequest(BaseModel):
    stack_size: int = Field(..., gt=0)
    player_count: int = Field(2, ge=2, le=6)


class ActionRequest(BaseModel):
    hand_id: str
    action_type: Literal["fold", "check", "call", "raise", "bet", "all_in"]
    player_id: str
    amount: Optional[int] = None
