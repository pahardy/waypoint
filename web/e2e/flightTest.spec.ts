import AxeBuilder from "@axe-core/playwright";
import { type Page, expect, test } from "@playwright/test";

async function expectNoSeriousIssues(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const serious = results.violations.filter((v) =>
    ["serious", "critical"].includes(v.impact ?? ""),
  );
  expect(serious).toEqual([]);
}

/** One single-item exercise per project, so parallel runs on the shared
 * database never edit the same row. */
const ITEMS = {
  desktop: { exercise: "Ex. 21 Precautionary Landing", title: "Precautionary Landing" },
  phone: { exercise: "Ex. 11 Slow Flight", title: "Slow Flight" },
} as const;

test("a reviewed mark and note are kept after a reload", async ({ page }, testInfo) => {
  const { exercise: name, title } = ITEMS[testInfo.project.name as keyof typeof ITEMS];
  const note = `Ask about this item (${Date.now()})`;
  await page.goto("/flight-test");
  const exercise = page.getByRole("region", { name });
  await exercise.getByText(title, { exact: true }).click();
  await expect(exercise.getByText(/^Aim: To /)).toBeVisible();

  const reviewed = exercise.getByLabel("Reviewed");
  if (await reviewed.isChecked()) {
    await reviewed.uncheck();
    await expect(exercise.getByText("TO REVIEW")).toBeVisible();
  }
  await reviewed.check();
  await expect(exercise.getByText("REVIEWED", { exact: true })).toBeVisible();
  const saved = page.waitForResponse((r) => r.request().method() === "PUT" && r.ok());
  await exercise.getByLabel("Questions for my instructor").fill(note);
  await exercise.getByLabel("Reviewed").focus();
  await saved;

  await page.reload();
  const again = page.getByRole("region", { name });
  await expect(again.getByText("REVIEWED", { exact: true })).toBeVisible();
  await again.getByText(title, { exact: true }).click();
  await expect(again.getByLabel("Questions for my instructor")).toHaveValue(note);
  await expect(page.getByText(/does not mean you are ready for, or will pass/)).toBeVisible();
});

for (const colorScheme of ["dark", "light"] as const) {
  test(`the flight-test page has no serious accessibility issues (${colorScheme})`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme });
    await page.goto("/flight-test");
    const row = page
      .getByRole("region", { name: "Ex. 22 Forced Landing" })
      .getByRole("listitem")
      .filter({ hasText: "Control/Approach" });
    await row.getByText("Control/Approach", { exact: true }).click();
    await expect(row.getByLabel("Reviewed")).toBeVisible();
    await expectNoSeriousIssues(page);
  });
}
