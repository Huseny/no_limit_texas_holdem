import type {
  GameState,
  CompletedHand,
  CreateHandRequest,
  ActionRequest,
} from "@/types/poker";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class PokerAPI {
  static async createHand(request: CreateHandRequest): Promise<GameState> {
    const response = await fetch(`${API_BASE}/api/hands/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = (await response.json()).detail;
      throw new Error(error || `Failed to create hand: ${response.statusText}`);
    }

    return response.json();
  }

  static async takeAction(request: ActionRequest): Promise<GameState> {
    const response = await fetch(`${API_BASE}/api/hands/action`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = (await response.json()).detail;
      throw new Error(error || `Failed to take action: ${response.statusText}`);
    }

    return response.json();
  }

  static async getHandHistory(): Promise<CompletedHand[]> {
    const response = await fetch(`${API_BASE}/api/hands/`);

    if (!response.ok) {
      const error = (await response.json()).detail;
      throw new Error(
        error || `Failed to get hand history: ${response.statusText}`
      );
    }

    return response.json();
  }

  static async getHand(handId: string): Promise<CompletedHand> {
    const response = await fetch(`${API_BASE}/api/hands/${handId}`);

    if (!response.ok) {
      const error = (await response.json()).detail;
      throw new Error(error || `Failed to get hand: ${response.statusText}`);
    }

    return response.json();
  }
}
