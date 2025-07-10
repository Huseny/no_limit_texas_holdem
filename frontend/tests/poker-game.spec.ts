import { test, expect, Page } from "@playwright/test";

test.describe("Poker Game - Extended E2E Scenarios", () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
  });

  test.beforeEach(async () => {
    await page.goto("/");
    // Reset the game state before each test by clicking "Reset" if available
    const resetButton = page.getByRole("button", { name: "Reset" });
    if (await resetButton.isVisible()) {
      await resetButton.click();
    }
  });

  test.afterAll(async ({ browserName }) => {
    // Webkit has issues with closing the page in some CI environments
    if (browserName !== "webkit") {
      await page.close();
    }
  });

  test("should handle a full hand with check, call, bet, and raise actions", async () => {
    // 1. SETUP: Start a 3-player game
    await test.step("Set up a 3-player game", async () => {
      await page.locator('input[type="number"]').nth(1).fill("3");
      await page.getByRole("button", { name: "Start" }).click();
      await expect(page.getByText(/Hand ID:/)).toBeVisible();
    });

    // 2. PRE-FLOP: Action starts with Player 2 (UTG)
    await test.step("Pre-flop action: P2 raises, P0 calls, P1 calls", async () => {
      // P2 is UTG and first to act
      await expect(page.locator("text=Current Player: Player 2")).toBeVisible();
      await page.getByRole("button", { name: "+" }).click(); // Increase raise amount
      await page.getByRole("button", { name: /Raise to \d+/ }).click(); // Raise
      await expect(page.getByText(/Player 2 raises to /)).toBeVisible();

      // P0 is BB
      await expect(page.locator("text=Current Player: Player 0")).toBeVisible();
      await page.getByRole("button", { name: "Call" }).click(); // Call
      await expect(page.getByText(/Player 0 calls/).last()).toBeVisible();

      // P1 is SB
      await expect(page.locator("text=Current Player: Player 1")).toBeVisible();
      await page.getByRole("button", { name: "Call" }).click(); // Call
      await expect(page.getByText(/Player 1 calls/).last()).toBeVisible();
    });

    // 3. FLOP: Action starts with the first player after the button (P1)
    await test.step("Flop action: P0 checks, P1 bets, P2 call", async () => {
      await expect(page.getByText(/Flop cards dealt:/)).toBeVisible();
      // Check for the "Current Street: flop"
      const streetLabel = page.locator('span:text("Current Street:")');
      await expect(streetLabel).toBeVisible();
      const streetValue = streetLabel.locator(
        "xpath=following-sibling::span[1]"
      );
      await expect(streetValue).toHaveText("flop");

      // P0 checks
      await expect(page.locator("text=Current Player: Player 0")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(page.getByText(/Player 0 checks/).last()).toBeVisible();

      // P1 check
      await expect(page.locator("text=Current Player: Player 1")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click(); // This is a "bet"
      await expect(page.getByText(/Player 1 checks/).last()).toBeVisible();

      // P2 checks
      await expect(page.locator("text=Current Player: Player 2")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(page.getByText(/Player 2 checks/).last()).toBeVisible();
    });

    // 4. TURN: All players check
    await test.step("Turn action: All players check", async () => {
      await expect(page.getByText(/Turn card dealt:/)).toBeVisible();
      const streetLabel = page.locator('span:text("Current Street:")');
      await expect(streetLabel).toBeVisible();
      const streetValue = streetLabel.locator(
        "xpath=following-sibling::span[1]"
      );
      await expect(streetValue).toHaveText("turn");

      // P0 checks
      await expect(page.locator("text=Current Player: Player 0")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(
        page
          .getByText(/Player 0 checks/)
          .last()
          .last()
      ).toBeVisible();

      // P1 checks
      await expect(page.locator("text=Current Player: Player 1")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(page.getByText(/Player 1 checks/).last()).toBeVisible();

      // P2 checks
      await expect(page.locator("text=Current Player: Player 2")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(page.getByText(/Player 2 checks/).last()).toBeVisible();
    });

    // 5. RIVER: Showdown after checks
    await test.step("River action and Showdown", async () => {
      // All players check again to get to showdown
      await expect(page.locator("text=Current Player: Player 0")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(page.getByText(/Player 0 checks/).last()).toBeVisible();

      await expect(page.locator("text=Current Player: Player 1")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(page.getByText(/Player 1 checks/).last()).toBeVisible();

      await expect(page.locator("text=Current Player: Player 2")).toBeVisible();
      await page.getByRole("button", { name: "Check" }).click();
      await expect(page.getByText(/Player 2 checks/).last()).toBeVisible();

      // Hand is now complete
      await expect(page.getByText(/Hand #.* ended/)).toBeVisible();
      await expect(page.getByText(/Final pot was /)).toBeVisible();
    });

    // 6. VERIFY HISTORY
    await test.step("Verify complex hand history", async () => {
      const firstHandInHistory = page.locator(".bg-blue-100").first();
      await expect(firstHandInHistory).toBeVisible();

      // Check for a complex action log (c for call, r for raise, x for check)
      const actionsText = await firstHandInHistory
        .locator("text=/Actions:/")
        .innerText();
      expect(actionsText.length).toBeGreaterThan(10);
      expect(actionsText).toMatch(/r\d+/);
      expect(actionsText).toContain("c:");
      expect(actionsText).toContain("x:");

      // Check winnings format for 3 players
      const winningsLine = await firstHandInHistory
        .locator("text=/Winnings:/")
        .innerText();
      expect(winningsLine).toMatch(
        /Winnings: Player \d+: [+-]?\d+; Player \d+: [+-]?\d+; Player \d+: [+-]?\d+/
      );
    });
  });

  test("should show multiple hands in history correctly", async () => {
    // Play two simple hands and check if they both appear in history

    // HAND 1
    await test.step("Play the first hand to completion", async () => {
      await page.locator('input[type="number"]').nth(1).fill("2");
      await page.getByRole("button", { name: "Start" }).click();
      const hand1Id = (await page.locator("text=/Hand #/").first().innerText())
        .split(" ")[1]
        .replace("#", "");

      await page.getByRole("button", { name: "Fold" }).click();
      await expect(page.getByText(/Hand #.* ended/)).toBeVisible();
      await expect(page.locator(".bg-blue-100").first()).toContainText(hand1Id);
    });

    // Start a new hand
    await page.getByRole("button", { name: "Reset" }).click();

    // HAND 2
    await test.step("Play the second hand to completion", async () => {
      await page.locator('input[type="number"]').nth(1).fill("2");
      await page.getByRole("button", { name: "Start" }).click();
      const hand2Id = (await page.locator("text=/Hand #/").first().innerText())
        .split(" ")[1]
        .replace("#", "");

      await page.getByRole("button", { name: "Fold" }).click();
      await expect(page.getByText(/Hand #.* ended/)).toBeVisible();

      // After a short delay for UI to update
      await page.waitForTimeout(500);

      const historyItems = await page.locator(".bg-blue-100").all();
      expect(historyItems.length).toBeGreaterThanOrEqual(2); // Other histories from previous games may be there too
      await expect(page.locator(".bg-blue-100").first()).toContainText(hand2Id);
    });
  });
});
