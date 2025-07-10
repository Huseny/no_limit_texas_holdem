export const formatPlayerName = (player_id: string): string => {
  const playerNum = Number.parseInt(player_id.split("_")[1]);
  return `Player ${playerNum}`;
};
