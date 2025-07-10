import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from app.db.connection import truncate_tables
from app.main import app
from app.core.game_logic import active_games, game_states, initial_player_stack_sizes
from app.db.repository import HandRepository


# Clear in-memory stores before each test to ensure test isolation
@pytest.fixture(autouse=True)
def clear_game_states():
    active_games.clear()
    game_states.clear()
    initial_player_stack_sizes.clear()
    truncate_tables()


@pytest.mark.asyncio
async def test_full_hand_simulation_two_players():
    """
    Tests a complete game simulation with two players,
    ensuring the game progresses, ends, and winnings are calculated correctly.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_payload = {"stack_size": 1000, "player_count": 2}
        response = await ac.post("/api/hands/create", json=create_payload)
        assert response.status_code == 200
        game_state = response.json()
        hand_id = game_state["hand_id"]
        assert hand_id

        seen_players = set()
        action_count = 0

        # Loop through player actions until the hand ends or max actions reached
        # Max 100 actions to avoid infinite loops in case of logic errors
        while game_state.get("active_player_id") and action_count < 100:
            active_player_id = game_state["active_player_id"]
            seen_players.add(active_player_id)

            # Simple strategy: if there's a bet, call; otherwise, check.
            # If cannot check/call, then fold.
            action_type = "call" if game_state["current_bet"] > 0 else "check"
            amount = None

            # Get available actions for the current player to make a more robust decision
            # This would typically involve another API call or a helper function
            # For simplicity in integration test, we'll try common actions.
            # In a real scenario, you'd query /api/hands/{id}/actions for player_id
            # to determine valid actions.

            action_payload = {
                "hand_id": hand_id,
                "action_type": action_type,
                "amount": amount,
                "player_id": active_player_id,
            }

            response = await ac.post("/api/hands/action", json=action_payload)

            # If the action fails (e.g., cannot check/call), try folding
            if response.status_code == 400:
                action_payload["action_type"] = "fold"
                response = await ac.post("/api/hands/action", json=action_payload)

            assert response.status_code == 200, f"Action failed: {response.text}"
            game_state = response.json()
            action_count += 1

        assert not game_state.get("active_player_id"), "Game did not finish."
        assert game_state["winnings"] is not None
        assert isinstance(game_state["winnings"], dict)
        # Sum of winnings should be zero in a closed system
        assert sum(game_state["winnings"].values()) == 0

        # Retrieve completed hand from the repository
        response = await ac.get("/api/hands/")
        assert response.status_code == 200
        hands = response.json()
        assert any(hand["id"] == hand_id for hand in hands)

        response = await ac.get(f"/api/hands/{hand_id}")
        assert response.status_code == 200
        hand = response.json()
        assert hand["id"] == hand_id
        assert hand["game_state"]["winnings"] is not None
        assert len(hand["game_state"]["players"]) == create_payload["player_count"]
        assert (
            len(seen_players) == create_payload["player_count"]
        )  # All players should have had a turn


@pytest.mark.asyncio
async def test_create_hand_invalid_stack_size():
    """Tests hand creation with an invalid (zero or negative) stack size."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/hands/create", json={"stack_size": 0, "player_count": 2}
        )
        assert (
            response.status_code == 422
        )  # Unprocessable Entity due to Pydantic validation
        assert "Input should be greater than 0" in response.json()["detail"][0]["msg"]

        response = await ac.post(
            "/api/hands/create", json={"stack_size": -100, "player_count": 2}
        )
        assert response.status_code == 422
        assert "Input should be greater than 0" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_create_hand_invalid_player_count():
    """Tests hand creation with an invalid player count (less than 2 or more than 6)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/hands/create", json={"stack_size": 1000, "player_count": 1}
        )
        assert response.status_code == 422
        assert (
            "Input should be greater than or equal to 2"
            in response.json()["detail"][0]["msg"]
        )

        response = await ac.post(
            "/api/hands/create", json={"stack_size": 1000, "player_count": 7}
        )
        assert response.status_code == 422
        assert (
            "Input should be less than or equal to 6"
            in response.json()["detail"][0]["msg"]
        )


@pytest.mark.asyncio
async def test_action_on_nonexistent_hand():
    """Tests performing an action on a hand ID that does not exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        non_existent_id = str(uuid.uuid4())
        response = await ac.post(
            "/api/hands/action",
            json={
                "hand_id": non_existent_id,
                "action_type": "check",
                "player_id": "player_0",
            },
        )
        assert response.status_code == 404
        assert "Hand not found." in response.json()["detail"]


@pytest.mark.asyncio
async def test_action_when_not_active_player():
    """Tests performing an action by a player who is not the active player."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_payload = {"stack_size": 1000, "player_count": 2}
        response = await ac.post("/api/hands/create", json=create_payload)
        assert response.status_code == 200
        game_state = response.json()
        hand_id = game_state["hand_id"]
        active_player_id = game_state["active_player_id"]

        # Determine the inactive player
        inactive_player_id = (
            "player_0" if active_player_id == "player_1" else "player_1"
        )

        # Attempt to perform an action with the inactive player's ID
        response = await ac.post(
            "/api/hands/action",
            json={
                "hand_id": hand_id,
                "action_type": "check",
                "player_id": inactive_player_id,
            },
        )
        assert (
            response.status_code == 400
        )  # Expecting 400 due to UserWarning from game_logic
        assert (
            f"Player {inactive_player_id} is not the active player."
            in response.json()["detail"]
        )


@pytest.mark.asyncio
async def test_action_when_game_is_over():
    """Tests performing an action after the hand has concluded."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_payload = {"stack_size": 1000, "player_count": 2}
        response = await ac.post("/api/hands/create", json=create_payload)
        assert response.status_code == 200
        game_state = response.json()
        hand_id = game_state["hand_id"]

        # Play through the hand until it's over
        action_count = 0
        active_player_id = game_state.get("active_player_id")
        while game_state.get("active_player_id") and action_count < 100:
            active_player_id = game_state["active_player_id"]
            action_payload = {
                "hand_id": hand_id,
                "action_type": "fold",
                "player_id": active_player_id,
            }  # Force players to fold to end quickly
            response = await ac.post("/api/hands/action", json=action_payload)
            assert response.status_code == 200, response.text
            game_state = response.json()
            action_count += 1

        assert not game_state.get("active_player_id"), "Game did not finish."

        # Now try to perform an action on the completed hand
        # Use a dummy player_id as the game is over, it should still be rejected.
        response = await ac.post(
            "/api/hands/action",
            json={"hand_id": hand_id, "action_type": "check", "player_id": "player_0"},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_raise_action_without_amount():
    """Tests attempting a 'raise' action without specifying an amount."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/hands/create", json={"stack_size": 1000, "player_count": 2}
        )
        assert response.status_code == 200
        game_state = response.json()
        hand_id = game_state["hand_id"]
        active_player_id = game_state["active_player_id"]

        # Advance game state to a point where a raise is possible (e.g., after initial blinds)
        # Player 0 (SB) posts 1, Player 1 (BB) posts 2.
        # Player 0's turn to act. They can fold, call (2), or raise.
        # For simplicity, let's assume the first action will allow a raise.

        response = await ac.post(
            "/api/hands/action",
            json={
                "hand_id": hand_id,
                "action_type": "raise",
                "player_id": active_player_id,
            },  # Missing 'amount'
        )
        assert response.status_code == 400  # Bad Request from game_logic.py
        assert "Amount must be specified for raise action." in response.json()["detail"]


@pytest.mark.asyncio
async def test_raise_action_with_invalid_amount():
    """Tests attempting a 'raise' action with an amount that is too low or too high."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/hands/create", json={"stack_size": 1000, "player_count": 2}
        )
        assert response.status_code == 200
        game_state = response.json()
        hand_id = game_state["hand_id"]
        active_player_id = game_state["active_player_id"]

        # Player 0 (SB) posts 1, Player 1 (BB) posts 2. Current bet is 2.
        # Player 0's turn. Min raise to is usually current_bet + previous_raise_amount (which is 2) = 4
        # Let's try to raise to 1 (too low)
        response = await ac.post(
            "/api/hands/action",
            json={
                "hand_id": hand_id,
                "action_type": "raise",
                "amount": 1,
                "player_id": active_player_id,
            },
        )
        assert response.status_code == 400
        assert (
            "Action failed: " in response.json()["detail"]
        )  # General error from pokerkit

        # Try to raise more than player's stack
        player_index = int(active_player_id.split("_")[1])
        player_stack = game_state["players"][player_index]["stack"]
        response = await ac.post(
            "/api/hands/action",
            json={
                "hand_id": hand_id,
                "action_type": "raise",
                "amount": player_stack + 100,
                "player_id": active_player_id,
            },
        )
        assert response.status_code == 400
        assert "Action failed: " in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_all_hands_empty():
    """Tests retrieving all hands when no hands have been completed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/hands/")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_fetch_nonexistent_hand_by_id():
    """Tests fetching a completed hand by an ID that does not exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        non_existent_id = str(uuid.uuid4())
        response = await ac.get(f"/api/hands/{non_existent_id}")
        assert response.status_code == 404
        assert "Hand not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_multiple_hands_creation_and_completion():
    """
    Tests creating and completing multiple hands sequentially,
    and verifies they are all retrievable.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        hand_ids = []
        for _ in range(3):  # Create and complete 3 hands
            create_payload = {"stack_size": 500, "player_count": 2}
            response = await ac.post("/api/hands/create", json=create_payload)
            assert response.status_code == 200
            game_state = response.json()
            hand_id = game_state["hand_id"]
            hand_ids.append(hand_id)

            # Play through the hand until it's over
            action_count = 0
            while game_state.get("active_player_id") and action_count < 100:
                active_player_id = game_state["active_player_id"]
                action_payload = {
                    "hand_id": hand_id,
                    "action_type": "fold",
                    "player_id": active_player_id,
                }
                response = await ac.post("/api/hands/action", json=action_payload)
                assert response.status_code == 200, response.text
                game_state = response.json()
                action_count += 1
            assert not game_state.get("active_player_id")

        # Verify all hands are in the completed hands list
        response = await ac.get("/api/hands/")
        assert response.status_code == 200
        completed_hands = response.json()
        assert len(completed_hands) >= 3  # Could be more if other tests ran first

        retrieved_ids = {hand["id"] for hand in completed_hands}
        for hid in hand_ids:
            assert hid in retrieved_ids

        # Verify individual hand retrieval
        for hid in hand_ids:
            response = await ac.get(f"/api/hands/{hid}")
            assert response.status_code == 200
            assert response.json()["id"] == hid


@pytest.mark.asyncio
async def test_game_flow_with_all_in():
    """
    Simulates a game flow where a player goes all-in,
    and ensures the game handles it correctly.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_payload = {
            "stack_size": 100,
            "player_count": 2,
        }  # Small stack for easy all-in
        response = await ac.post("/api/hands/create", json=create_payload)
        assert response.status_code == 200
        game_state = response.json()
        hand_id = game_state["hand_id"]

        action_count = 0
        while game_state.get("active_player_id") and action_count < 100:
            active_player_id = game_state["active_player_id"]
            player_index = int(active_player_id.split("_")[1])
            player_stack = game_state["players"][player_index]["stack"]
            current_bet = game_state["current_bet"]

            action_type = "call"
            amount = None

            # If current player can go all-in with a raise
            if (
                player_stack > current_bet and player_stack <= current_bet + 20
            ):  # Try to go all-in if small stack
                action_type = "raise"
                amount = player_stack  # Go all-in
            elif current_bet > 0:
                action_type = "call"
            else:
                action_type = "check"

            action_payload = {
                "hand_id": hand_id,
                "action_type": action_type,
                "amount": amount,
                "player_id": active_player_id,
            }
            response = await ac.post("/api/hands/action", json=action_payload)

            if response.status_code == 400:  # If raise failed, try call or fold
                if action_type == "raise":
                    action_payload["action_type"] = "call"
                    response = await ac.post("/api/hands/action", json=action_payload)
                    if response.status_code == 400:
                        action_payload["action_type"] = "fold"
                        response = await ac.post(
                            "/api/hands/action", json=action_payload
                        )
                elif action_type == "check" or action_type == "call":
                    action_payload["action_type"] = "fold"
                    response = await ac.post("/api/hands/action", json=action_payload)

            assert response.status_code == 200, f"Action failed: {response.text}"
            game_state = response.json()
            action_count += 1

        assert not game_state.get(
            "active_player_id"
        ), "Game did not finish after all-in."
        assert game_state["winnings"] is not None
        assert sum(game_state["winnings"].values()) == 0


@pytest.mark.asyncio
async def test_invalid_action_type_pydantic_error():
    """
    Tests the API's response to an invalid action type,
    ensuring Pydantic validation catches it.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/hands/create", json={"stack_size": 1000, "player_count": 2}
        )
        assert response.status_code == 200
        hand_id = response.json()["hand_id"]
        active_player_id = response.json()["active_player_id"]

        response = await ac.post(
            "/api/hands/action",
            json={
                "hand_id": hand_id,
                "action_type": "invalid_action",
                "player_id": active_player_id,
            },
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("action_type" in e["loc"] for e in errors)
        assert any(
            "Input should be 'fold', 'check', 'call', 'raise', 'bet' or 'all_in'" in e["msg"]
            for e in errors
        )


@pytest.mark.asyncio
async def test_missing_hand_id_in_action_request():
    """Tests performing an action with a missing hand_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/hands/action",
            json={"action_type": "check", "player_id": "player_0"},  # Missing hand_id
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("hand_id" in (e["loc"]) for e in errors)
        assert any("Field required" in e["msg"] for e in errors)


@pytest.mark.asyncio
async def test_missing_player_id_in_action_request():
    """Tests performing an action with a missing player_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/hands/create", json={"stack_size": 1000, "player_count": 2}
        )
        assert response.status_code == 200
        hand_id = response.json()["hand_id"]

        response = await ac.post(
            "/api/hands/action",
            json={"hand_id": hand_id, "action_type": "check"},  # Missing player_id
        )
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("player_id" in str(e["loc"]) for e in errors)
        assert any("Field required" in e["msg"] for e in errors)


@pytest.mark.asyncio
async def test_get_hand_by_id_after_multiple_actions():
    """
    Tests retrieving a hand by ID after it has gone through several actions
    but before it's completed.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_payload = {"stack_size": 1000, "player_count": 2}
        response = await ac.post("/api/hands/create", json=create_payload)
        assert response.status_code == 200
        game_state = response.json()
        hand_id = game_state["hand_id"]

        # Perform a few actions
        for _ in range(3):
            active_player_id = game_state["active_player_id"]
            action_type = "call" if game_state["current_bet"] > 0 else "check"
            action_payload = {
                "hand_id": hand_id,
                "action_type": action_type,
                "player_id": active_player_id,
            }
            response = await ac.post("/api/hands/action", json=action_payload)
            assert response.status_code == 200
            game_state = response.json()

        # Now retrieve the hand by ID
        response = await ac.get(f"/api/hands/{hand_id}")
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["detail"] == "Hand not found"
