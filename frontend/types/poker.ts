export interface Player {
  player_id: string;
  stack: number;
  cards: string[];
  current_bet_in_round: number;
  status: string;
  position: string;
  is_dealer?: boolean;
  is_small_blind?: boolean;
  is_big_blind?: boolean;
}

export interface GameState {
  hand_id: string;
  players: Player[];
  active_player_id: string | null;
  pot: number;
  current_street: string;
  current_bet: number;
  board_cards: string[];
  main_log: string[];
  actions_log: string[];
  winnings: Record<string, number> | null;
}

export interface CompletedHand {
  id: string;
  game_state: GameState;
}

export interface HandHistory {
  hand_id: string;
  stack_size: number;
  dealer: number;
  small_blind: number;
  big_blind: number;
  player_hands: Record<number, string[]>;
  actions: string;
  winnings: Record<number, number>;
  board_cards: string[];
}

export interface CreateHandRequest {
  stack_size: number;
  player_count: number;
}

export interface ActionRequest {
  hand_id: string;
  player_id: string;
  action_type: "fold" | "check" | "call" | "raise" | "all_in";
  amount?: number;
}

export interface ActionLogEntry {
  player: string;
  action: string;
  amount?: number;
  street: string;
}
