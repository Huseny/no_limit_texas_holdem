import uuid
from pokerkit import Automation, Card, NoLimitTexasHoldem, State
from typing import Dict, Optional, List, Any
from app.models.models import GameState, Player
from app.utils.logger import Logger


active_games: Dict[str, State] = {}
game_states: Dict[str, GameState] = {}

# Store initial stack sizes for each game, per player, to calculate winnings accurately
initial_player_stack_sizes: Dict[str, Dict[str, int]] = {}
bet_size = (20, 40)


def _to_card_str(cards: List[Card]) -> List[str]:
    """Converts a list of Card objects to a list of strings."""
    return [str(card) for card in cards]


def _detect_street_change(old_state: GameState, new_state: GameState) -> Optional[List]:
    """
    Detects if the street has changed between two GameState objects.
    Returns a dict with the new street name and the cards added if changed, otherwise None.
    Example: [ "flop", ["Ah", "Kd", "7c"]]
    """
    if not old_state:
        return [new_state.current_street, new_state.board_cards]
    elif not new_state:
        return old_state.current_street, old_state.board_cards
    elif old_state and new_state:
        if old_state.current_street != new_state.current_street:
            old_cards = old_state.board_cards if old_state.board_cards else []
            new_cards = new_state.board_cards if new_state.board_cards else []
            added_cards = new_cards[len(old_cards) :]
            return [new_state.current_street, added_cards]
    return None


def update_game_state(
    game_id: str, state: State, new_action_log: Optional[str] = None
) -> GameState:
    """Updates the game state from the pokerkit state and returns a dictionary."""
    previous_game_state = game_states.get(game_id)
    actions_log = list(previous_game_state.actions_log) if previous_game_state else []
    main_log = list(previous_game_state.main_log) if previous_game_state else []

    if new_action_log:
        actions_log.append(new_action_log)

    actor_index = state.actor_index
    players = []
    for i in range(state.player_count):
        player = Player(
            player_id=f"player_{i}",
            stack=state.stacks[i],
            current_bet_in_round=state.bets[i],
            cards=_to_card_str((state.hole_cards[i] if state.hole_cards else [])),
            status=(
                "folded"
                if not state.hole_cards or not state.hole_cards[i]
                else "active"
            ),
            is_dealer=(i == 0),
            is_small_blind=(i == 1),
            is_big_blind=(i == 2),
        )
        players.append(player)

    board_cards_flat = []
    if state.board_cards:
        for street_cards in state.board_cards:
            board_cards_flat.extend(_to_card_str(street_cards))

    # Log new board cards
    previous_board_cards = (
        list(previous_game_state.board_cards) if previous_game_state else []
    )
    if len(board_cards_flat) > len(previous_board_cards):
        new_cards = board_cards_flat[len(previous_board_cards) :]
        actions_log.append("".join(new_cards))

    current_street_name = _get_street_name(state)
    current_bet_amount = max(state.bets) if state.bets else 0
    winnings_dict = None

    if not state.status and game_id in initial_player_stack_sizes:
        winnings_dict = {}
        for i in range(state.player_count):
            player_id = f"player_{i}"
            if player_id in initial_player_stack_sizes[game_id]:
                initial_stack = initial_player_stack_sizes[game_id][player_id]
                winnings_amount = state.stacks[i] - initial_stack
                winnings_dict[player_id] = winnings_amount

    game_state_obj = GameState(
        hand_id=game_id,
        players=players,
        board_cards=board_cards_flat,
        pot=state.total_pot_amount,
        active_player_id=f"player_{actor_index}" if actor_index is not None else None,
        current_street=current_street_name,
        current_bet=current_bet_amount,
        winnings=winnings_dict,
        actions_log=actions_log,
        main_log=main_log,  # Pass the preserved main_log
    )
    game_states[game_id] = game_state_obj

    return game_state_obj


def _get_street_name(state: State) -> str:
    """Determines the current street name based on the state."""
    current_street_name = "preflop"  # Default to preflop
    if state.street is not None:
        if state.street == state.streets[0]:
            current_street_name = "preflop"
        elif state.street == state.streets[1]:
            current_street_name = "flop"
        elif state.street == state.streets[2]:
            current_street_name = "turn"
        elif state.street == state.streets[3]:
            current_street_name = "river"
    return current_street_name


def create_new_hand(stack_size: int, player_count: int) -> GameState:
    """Creates a new poker hand and initializes its state."""
    game_id = str(uuid.uuid4())
    automations = (
        Automation.ANTE_POSTING,
        Automation.BET_COLLECTION,
        Automation.BLIND_OR_STRADDLE_POSTING,
        Automation.CARD_BURNING,
        Automation.HOLE_DEALING,
        Automation.BOARD_DEALING,
        Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
        Automation.HAND_KILLING,
        Automation.CHIPS_PUSHING,
        Automation.CHIPS_PULLING,
    )

    raw_starting_stacks = [stack_size] * player_count

    state = NoLimitTexasHoldem.create_state(
        automations=automations,  # type: ignore
        ante_trimming_status=False,
        raw_antes=0,
        raw_blinds_or_straddles=bet_size,
        min_bet=bet_size[1],
        raw_starting_stacks=raw_starting_stacks,
        player_count=player_count,
    )

    active_games[game_id] = state
    # Store initial stack size for each player individually
    initial_player_stack_sizes[game_id] = {
        f"player_{i}": stack_size for i in range(player_count)
    }

    game_state = update_game_state(game_id, state)

    Logger.log_start_hand(game_state, list(bet_size))

    return game_state


def get_game_state(game_id: str) -> Optional[GameState]:
    """Retrieves the current state of a game."""
    return game_states.get(game_id)


def get_player_hole_cards(game_id: str, player_id: str) -> Optional[List[str]]:
    """Retrieves the hole cards for a specific player."""
    state = active_games.get(game_id)
    if not state:
        return None
    try:
        player_index = int(player_id.split("_")[1])
        return _to_card_str(state.hole_cards[player_index])
    except (ValueError, IndexError):
        return None


def get_player_actions(state: State, player_index: int) -> List[Dict[str, Any]]:
    """Gets the available actions for a player."""
    actions = []
    if state.actor_index != player_index:
        return actions

    if state.can_check_or_call():
        amount = state.checking_or_calling_amount
        if amount == 0:
            actions.append({"action": "check"})
        else:
            actions.append({"action": "call", "amount": amount})

    if state.can_fold():
        actions.append({"action": "fold"})

    if state.can_complete_bet_or_raise_to():
        min_raise = state.min_completion_betting_or_raising_to_amount
        max_raise = state.max_completion_betting_or_raising_to_amount
        actions.append(
            {
                "action": "raise",
                "min_amount": min_raise,
                "max_amount": max_raise,
            }
        )

    return actions


def perform_action(
    game_id: str, player_id: str, action: str, amount: Optional[int] = None
) -> GameState:
    """
    Performs a player action and updates the game state.
    Raises ValueError or UserWarning on failure.
    """
    state = active_games.get(game_id)
    if not state:
        raise ValueError(f"Game with ID {game_id} not found.")

    try:
        player_index = int(player_id.split("_")[1])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid player ID: {player_id}")

    if state.actor_index != player_index:
        raise UserWarning(
            f"Player {player_id} is not the active player. Current active player is player_{state.actor_index}."
        )

    log_entry = None
    try:
        if action == "fold":
            log_entry = "f"
            state.fold()
        elif action == "check":
            if max(state.bets) > 0:
                raise UserWarning(
                    "Cannot 'check' when there is an active bet. You must 'call', 'raise', or 'fold'."
                )

            log_entry = "x"
            state.check_or_call()
        elif action == "call":
            if max(state.bets) == 0:
                raise UserWarning(
                    "Cannot 'call' when there is no bet to call. Use 'check' or 'bet'."
                )

            log_entry = "c"
            state.check_or_call()

        elif action == "bet":
            if amount is None:
                raise ValueError("Amount must be specified for bet action.")

            if max(state.bets) > 0:
                raise UserWarning(
                    "Cannot 'bet' when there is already a bet in the round. Use 'raise' or 'call'."
                )

            if amount < (state.min_completion_betting_or_raising_to_amount or 0):
                raise UserWarning(
                    f"Bet amount must be at least {state.min_completion_betting_or_raising_to_amount}."
                )

            if amount > bet_size[1] and amount % bet_size[1] != 0:
                raise UserWarning(
                    f"Bet amount must be in increments of {bet_size[1]} chips."
                )

            log_entry = f"b{amount}"
            state.complete_bet_or_raise_to(amount)
        elif action == "raise":
            if amount is None:
                raise ValueError("Amount must be specified for raise action.")

            if max(state.bets) == 0:
                raise UserWarning(
                    "Cannot 'raise' when there is no bet to raise. Use 'bet'"
                )

            log_entry = f"r{amount}"
            state.complete_bet_or_raise_to(amount)
        elif action == "all_in":
            log_entry = "allin"
            state.complete_bet_or_raise_to(state.stacks[player_index])
        else:
            raise ValueError(f"Invalid action: {action}")
    except (ValueError, UserWarning) as e:
        raise UserWarning(f"Action failed: {str(e)}") from e

    previous_game_state = game_states.get(game_id)

    updated_state = update_game_state(game_id, state, new_action_log=log_entry)
    Logger.log_action(updated_state, player_id, action, amount)

    if previous_game_state is not None:
        street_change = _detect_street_change(previous_game_state, updated_state)

        if street_change:
            Logger.log_street_change(updated_state, street_change[0], street_change[1])

    if updated_state.winnings:
        Logger.log_game_ended(updated_state, previous_game_state.pot if previous_game_state else 0)

    return updated_state
