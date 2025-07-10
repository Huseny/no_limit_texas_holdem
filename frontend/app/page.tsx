"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import type { GameState, CompletedHand } from "@/types/poker";
import { PokerAPI } from "@/lib/api";
import { formatPlayerName } from "@/lib/utils";

const BIG_BLIND = 40;

export default function PokerGame() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [stackSize, setStackSize] = useState(100);
  const [playerCount, setPlayerCount] = useState(6);
  const [isLoading, setIsLoading] = useState(false);
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState(0);
  const [raiseAmount, setRaiseAmount] = useState(BIG_BLIND);
  const [history, setHistory] = useState<CompletedHand[]>([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await PokerAPI.getHandHistory();
        setHistory(data);
      } catch (error) {
        // Handle error silently
        console.error("Failed to fetch hand history:", error);
      }
    };
    fetchHistory();
  }, [historyRefreshTrigger]);

  const startNewHand = async () => {
    try {
      setIsLoading(true);
      const newGameState = await PokerAPI.createHand({
        stack_size: stackSize,
        player_count: playerCount,
      });
      setGameState(newGameState);
      toast.success("New Hand Started", {
        description: `Hand ${newGameState.hand_id.slice(0, 8)} has begun!`,
      });
    } catch (error) {
      toast.error("Error", {
        description:
          error instanceof Error ? error.message : "Failed to start new hand",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const takeAction = async (action: string, amount?: number) => {
    if (!gameState || !gameState.active_player_id) return;

    try {
      setIsLoading(true);
      const updatedGameState = await PokerAPI.takeAction({
        hand_id: gameState.hand_id,
        player_id: gameState.active_player_id,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        action_type: action as any,
        amount,
      });

      setGameState(updatedGameState);

      if (updatedGameState.winnings) {
        toast.info("Hand Complete", {
          description: `Hand ${updatedGameState.hand_id.slice(
            0,
            8
          )} has finished!`,
        });
        setHistoryRefreshTrigger((prev) => prev + 1);
      }
    } catch (error) {
      toast.error("Error", {
        description:
          error instanceof Error ? error.message : "Failed to take action",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const resetGame = () => {
    setGameState(null);
    toast.info("Game Reset", {
      description: "Ready to start a new hand",
    });
  };

  const currentPlayer = gameState?.players.find(
    (p) => p.player_id === gameState.active_player_id
  );

  return (
    <div className="flex h-screen bg-white">
      {/* Left Panel - Playing Field Log */}
      <div className="flex-1 p-4 border-r border-gray-300">
        <h2 className="text-lg font-medium mb-4 text-gray-700">
          Playing field log
        </h2>

        <div className="flex flex-wrap gap-3">
          {/* Stack Controls */}
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm">Stacks</span>
            <Input
              type="number"
              value={stackSize}
              onChange={(e) =>
                setStackSize(Number.parseInt(e.target.value) || 100)
              }
              className="w-20 h-8 text-sm"
              min={10}
              step={10}
              disabled={isLoading}
            />
          </div>

          {/* Player Count Control */}
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm">Players:</span>
            <Input
              type="number"
              value={playerCount}
              onChange={(e) =>
                setPlayerCount(
                  Math.min(6, Math.max(2, Number.parseInt(e.target.value) || 2))
                )
              }
              className="w-16 h-8 text-sm"
              min={2}
              max={6}
              disabled={isLoading}
            />
          </div>

          {gameState ? (
            <>
              <div className="flex items-center gap-2">
                <span className="text-sm">Hand ID:</span>
                <span className="text-sm font-mono text-gray-800">
                  {gameState.hand_id}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm">Current Street:</span>
                <span className="text-sm font-mono text-gray-800">
                  {gameState.current_street}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm">Current Bet:</span>
                <span className="text-sm font-mono text-gray-800">
                  {gameState.current_bet}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm">Pot:</span>
                <span className="text-sm font-mono text-gray-800">
                  {gameState.pot}
                </span>
              </div>
            </>
          ) : (
            <></>
          )}

          <div className="flex items-center gap-2 mb-4">
            <Button
              onClick={gameState ? resetGame : startNewHand}
              disabled={isLoading}
              className="h-8 px-3 text-sm bg-gray-200 hover:bg-gray-300 text-black border border-gray-400"
            >
              {gameState ? "Reset" : "Start"}
            </Button>
          </div>
        </div>

        {/* Game Log */}
        <div className="bg-white border border-gray-300 h-80 p-3 overflow-y-auto font-mono text-xs text-gray-800 mb-4">
          {gameState ? (
            <div className="space-y-1">
              {gameState.main_log.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500">
              No active game. Click Apply to start.
            </div>
          )}
        </div>
        {/* current player */}
        <div className="mb-4">
          <span className="text-sm font-medium">Current Player: </span>
          {currentPlayer ? (
            <span className="text-blue-600">
              {formatPlayerName(currentPlayer.player_id)}
            </span>
          ) : (
            <span className="text-gray-500">No active player</span>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          {gameState && currentPlayer && !gameState.winnings ? (
            <>
              <Button
                onClick={() => takeAction("fold")}
                disabled={isLoading}
                className="h-8 px-4 text-sm bg-blue-400 hover:bg-blue-500 text-white"
              >
                Fold
              </Button>

              {gameState.current_bet === currentPlayer.current_bet_in_round && (
                <Button
                  onClick={() => takeAction("check")}
                  disabled={isLoading}
                  className="h-8 px-4 text-sm bg-green-400 hover:bg-green-500 text-white"
                >
                  Check
                </Button>
              )}

              {gameState.current_bet > currentPlayer.current_bet_in_round && (
                <Button
                  onClick={() => takeAction("call")}
                  disabled={isLoading}
                  className="h-8 px-4 text-sm bg-green-400 hover:bg-green-500 text-white"
                >
                  Call
                </Button>
              )}

              <div className="flex items-center gap-1">
                <Button
                  onClick={() =>
                    setRaiseAmount(
                      Math.max(
                        gameState.current_bet + BIG_BLIND,
                        raiseAmount - BIG_BLIND
                      )
                    )
                  }
                  disabled={isLoading}
                  className="h-8 w-8 text-sm bg-orange-300 hover:bg-orange-400 text-white"
                >
                  -
                </Button>
                <Button
                  onClick={() => takeAction("raise", raiseAmount)}
                  disabled={
                    isLoading ||
                    raiseAmount >
                      currentPlayer.stack + currentPlayer.current_bet_in_round
                  }
                  className="h-8 px-3 text-sm bg-orange-400 hover:bg-orange-500 text-white"
                >
                  Raise to {raiseAmount}
                </Button>
                <Button
                  onClick={() => setRaiseAmount(raiseAmount + BIG_BLIND)}
                  disabled={isLoading}
                  className="h-8 w-8 text-sm bg-orange-300 hover:bg-orange-400 text-white"
                >
                  +
                </Button>
              </div>

              <Button
                onClick={() => takeAction("all_in")}
                disabled={isLoading || currentPlayer.stack === 0}
                className="h-8 px-4 text-sm bg-red-400 hover:bg-red-500 text-white"
              >
                ALL IN
              </Button>
            </>
          ) : (
            <div className="text-gray-500 text-sm">
              {gameState?.winnings ? "Hand Complete" : "No actions available"}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Hand History */}
      <div className="w-96 p-4 bg-gray-100">
        <h2 className="text-lg font-medium mb-4 text-gray-700">Hand history</h2>

        <div className="space-y-3 h-96 overflow-y-auto">
          {history.length === 0 ? (
            <div className="text-gray-500 text-sm">No completed hands yet</div>
          ) : (
            history.map((hand) => {
              const gameState = hand.game_state;

              const winnings = gameState.winnings
                ? Object.entries(gameState.winnings)
                    .map(([playerId, amount]) => {
                      return `${formatPlayerName(playerId)}: ${
                        amount > 0 ? "+" : ""
                      }${amount}`;
                    })
                    .join("; ")
                : "";

              const initialStack =
                gameState.players[0].stack -
                (gameState.winnings?.[gameState.players[0].player_id] || 0);

              return (
                <div
                  key={hand.id}
                  className="bg-blue-100 border border-blue-300 p-3 rounded text-xs font-mono"
                >
                  <div>Hand #{hand.id}</div>
                  <div>
                    Stack {initialStack}; Dealer:{" "}
                    {gameState.players.find((p) => p.is_dealer)?.player_id ||
                      "N/A"}
                    , Small blind:{" "}
                    {gameState.players.find((p) => p.is_small_blind)
                      ?.player_id || "N/A"}
                    , Big blind:{" "}
                    {gameState.players.find((p) => p.is_big_blind)?.player_id ||
                      "N/A"}
                  </div>
                  <div>
                    Hands:{" "}
                    {gameState.players
                      .map((player) => {
                        return `${formatPlayerName(player.player_id)}: ${
                          player.cards
                        }`;
                      })
                      .join("; ")}
                  </div>
                  <div>Actions: {gameState.actions_log.join(":")}</div>
                  <div>Winnings: {winnings}</div>
                </div>
              );
            })
          )}
        </div>
      </div>

      <Toaster />
    </div>
  );
}
