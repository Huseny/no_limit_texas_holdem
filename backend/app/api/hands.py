import uuid
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.models import (
    ActionRequest,
    CreateHandRequest,
    GameState,
    CompletedHand,
)
from app.core import game_logic
from app.db.repository import HandRepository

router = APIRouter()
repo = HandRepository()


@router.post("/api/hands/create", response_model=GameState)
def create_hand(request: CreateHandRequest):
    """Creates a new poker hand."""
    try:
        game_state = game_logic.create_new_hand(
            request.stack_size, request.player_count
        )
        return game_state
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/hands/action", response_model=GameState)
def perform_action(request: ActionRequest):
    """Processes a player action for a given hand."""
    try:
        current_game_state = game_logic.get_game_state(request.hand_id)
        if not current_game_state:
            raise HTTPException(status_code=404, detail="Hand not found.")

        game_state_after_action = game_logic.perform_action(
            request.hand_id, request.player_id, request.action_type, request.amount
        )

        if game_state_after_action.winnings:
            repo.save_completed_hand(game_state_after_action)

        return game_state_after_action

    except (ValueError, UserWarning) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/hands/", response_model=List[CompletedHand])
def get_all_hands():
    """Retrieves all completed hands."""
    return repo.get_all_completed_hands()


@router.get("/api/hands/{id}", response_model=CompletedHand)
def get_hand_by_id(id: str):
    """Retrieves a specific completed hand by its ID."""
    try:
        uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid hand ID format")
    hand = repo.get_completed_hand_by_id(id)
    if not hand:
        raise HTTPException(status_code=404, detail="Hand not found")
    return hand
