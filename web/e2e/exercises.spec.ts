import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("completing the scenario shows rubric feedback and survives a reload", async ({
  page,
}) => {
  await page.goto("/exercises");
  await expect(page.getByText("Educational simulation. Not operational guidance.")).toBeVisible();
  await page
    .getByRole("region", { name: "Scenario (PPAER)" })
    .getByRole("button", { name: "Start" })
    .click();
  await expect(page).toHaveURL(/\/exercises\/[0-9a-f-]{36}$/);

  await expect(page.getByText(/synthetic, for training only/).first()).toBeVisible();
  await expect(page.getByText(/Synthetic METAR, not real weather/)).toBeVisible();
  await expect(page.getByText("Stage 1 of 2")).toBeVisible();
  await page.getByRole("textbox").fill("The ceiling is 3,000 ft.");
  await page.getByRole("button", { name: "Submit answer" }).click();

  const first = page.getByRole("region", { name: "Stage 1 feedback" });
  await expect(first.getByText("Score: 100%")).toBeVisible();
  await expect(first.locator("blockquote").first()).toHaveText("The ceiling is 3,000 ft.");

  await page.reload();
  await expect(page.getByRole("region", { name: "Stage 1 feedback" })).toBeVisible();
  await expect(page.getByText("Stage 2 of 2")).toBeVisible();
  await expect(page.getByText(/flight visibility is dropping/)).toBeVisible();

  await page.getByRole("textbox").fill("The visibility ahead is below the minimum.");
  await page.getByRole("button", { name: "Submit answer" }).click();
  await expect(page.getByRole("region", { name: "Stage 2 feedback" })).toBeVisible();
  await expect(page.getByText("Overall score: 100%")).toBeVisible();
  await expect(page.getByText("Educational simulation. Not operational guidance.").first()).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const serious = results.violations.filter((v) =>
    ["serious", "critical"].includes(v.impact ?? ""),
  );
  expect(serious).toEqual([]);
});
