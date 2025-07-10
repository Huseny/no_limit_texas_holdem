from typing import List, Optional
from app.models.models import GameState


# --- Helper functions for logging ---
class Logger:
    """A utility class for logging actions in the poker game."""

    # --- Hand Start Logging ---
    @staticmethod
    def _add_log_entry(state: GameState, message: str):
        """Internal helper to append a message to the state's main log."""
        state.main_log.append(message)

    @staticmethod
    def _log_start_hand(state: GameState):
        """Logs the start of a new hand."""
        Logger._add_log_entry(state, f"--- Hand #{state.hand_id} started ---")

    @staticmethod
    def _log_end_hand(state: GameState, final_pot_size: int):
        """Logs the end of a hand and the final pot size."""
        Logger._add_log_entry(state, f"Final pot was {final_pot_size}")
        Logger._add_log_entry(state, f"--- Hand #{state.hand_id} ended ---")

    @staticmethod
    def _log_player_dealt_cards(state: GameState, player_id: str, cards: List[str]):
        """Logs cards dealt to a specific player."""
        Logger._add_log_entry(
            state, f"Player {player_id.split("_")[1]} is dealt {''.join(cards)}"
        )

    @staticmethod
    def _log_dealer(state: GameState, player_id: str):
        """Logs who the dealer is."""
        Logger._add_log_entry(state, f"Player {player_id.split("_")[1]} is the dealer")

    @staticmethod
    def _log_small_blind(state: GameState, player_id: str, amount: int):
        """Logs the small blind posting."""
        Logger._add_log_entry(
            state,
            f"Player {player_id.split("_")[1]} posts small blind - {amount} chips",
        )

    @staticmethod
    def _log_big_blind(state: GameState, player_id: str, amount: int):
        """Logs the big blind posting."""
        Logger._add_log_entry(
            state, f"Player {player_id.split("_")[1]} posts big blind - {amount} chips"
        )

    @staticmethod
    def log_start_hand(state: GameState, blinds_amount: List[int] = [1, 2]):
        """Wrapper for all helper functions to log the start of a hand."""
        Logger._log_start_hand(state)
        for player in state.players:
            Logger._log_player_dealt_cards(state, player.player_id, player.cards)

        Logger.log_separator(state)

        if state.players:
            dealer = state.players[0]
            Logger._log_dealer(state, dealer.player_id)
        if len(state.players) > 1:
            small_blind_player = state.players[1]
            Logger._log_small_blind(
                state, small_blind_player.player_id, blinds_amount[0]
            )
        if len(state.players) > 2:
            big_blind_player = state.players[2]
            Logger._log_big_blind(state, big_blind_player.player_id, blinds_amount[1])

        Logger.log_separator(state)

    # --- Street Change Logging ---
    @staticmethod
    def _log_flop_cards(state: GameState, cards: List[str]):
        """Logs the flop cards dealt."""
        Logger._add_log_entry(state, f"Flop cards dealt: {''.join(cards)}")

    @staticmethod
    def _log_turn_card(state: GameState, card: str):
        """Logs the turn card dealt."""
        Logger._add_log_entry(state, f"Turn card dealt: {card}")

    @staticmethod
    def _log_river_card(state: GameState, card: str):
        """Logs the river card dealt."""
        Logger._add_log_entry(state, f"River card dealt: {card}")

    @staticmethod
    def log_street_change(state: GameState, street: str, cards: List[str]):
        """Logs the change of street and the cards dealt."""
        if street == "flop":
            Logger._log_flop_cards(state, cards)
        elif street == "turn":
            Logger._log_turn_card(state, cards[0])
        elif street == "river":
            Logger._log_river_card(state, cards[0])

    # --- Player Actions Logging ---
    @staticmethod
    def _log_action_fold(state: GameState, player_id: str):
        """Logs a player folding."""
        Logger._add_log_entry(state, f"Player {player_id.split("_")[1]} folds")

    @staticmethod
    def _log_action_check(state: GameState, player_id: str):
        """Logs a player checking."""
        Logger._add_log_entry(state, f"Player {player_id.split("_")[1]} checks")

    @staticmethod
    def _log_action_call(state: GameState, player_id: str):
        """Logs a player calling."""
        Logger._add_log_entry(state, f"Player {player_id.split("_")[1]} calls")

    @staticmethod
    def _log_action_bet(state: GameState, player_id: str, amount: int):
        """Logs a player betting."""
        Logger._add_log_entry(state, f"Player {player_id.split("_")[1]} bets {amount}")

    @staticmethod
    def _log_action_raise(state: GameState, player_id: str, total_amount: int):
        """Logs a player raising."""
        Logger._add_log_entry(
            state, f"Player {player_id.split("_")[1]} raises to {total_amount} chips"
        )

    @staticmethod
    def _log_action_all_in(state: GameState, player_id: str):
        """Logs a player going all-in."""
        Logger._add_log_entry(state, f"Player {player_id.split("_")[1]} goes all-in")

    @staticmethod
    def log_action(
        state: GameState, player_id: str, action: str, amount: Optional[int] = None
    ):
        """Wrapper to log a player's action based on action type."""
        action_map = {
            "fold": Logger._log_action_fold,
            "check": Logger._log_action_check,
            "call": Logger._log_action_call,
            "bet": Logger._log_action_bet,
            "raise": Logger._log_action_raise,
            "all_in": Logger._log_action_all_in,
        }
        logger = action_map.get(action.lower())
        if logger:
            if (action.lower() in ["bet", "raise"]) and amount is not None:
                logger(state, player_id, amount)
            else:
                logger(state, player_id)
        else:
            Logger._add_log_entry(state, f"Unknown action '{action}' by Player {player_id.split('_')[1]}")

    # --- Log game ended ---
    @staticmethod
    def log_game_ended(state: GameState, final_pot: int):
        Logger._add_log_entry(state, f"Hand #{state.hand_id} ended")
        Logger._add_log_entry(state, f"Final pot was {final_pot}")

    # --- Generic separator for log formatting ---
    @staticmethod
    def log_separator(state: GameState):
        """Adds a separator line to the log."""
        Logger._add_log_entry(state, "---")
