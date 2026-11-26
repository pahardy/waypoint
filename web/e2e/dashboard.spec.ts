import AxeBuilder from "@axe-core/playwright";
import { type Page, expect, test } from "@playwright/test";

/** Submit a 5-question topic quiz unanswered: every item counts as wrong. */
async function failOccurrencesQuiz(page: Page) {
  await page.goto("/practice");
  const quiz = page.getByRole("region", { name: "PSTAR topic quiz" });
  await quiz.getByLabel("Topic").selectOption({ label: "Aviation Occurrences (5)" });
  await quiz.getByRole("button", { name: "Start quiz" }).click();
  await expect(page).toHaveURL(/\/practice\/[0-9a-f-]{36}$/);
  await page.getByRole("button", { name: "Submit answers" }).click();
  await expect(page).toHaveURL(/\/results\/[0-9a-f-]{36}$/);
}

async function expectNoSeriousIssues(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const serious = results.violations.filter((v) =>
    ["serious", "critical"].includes(v.impact ?? ""),
  );
  expect(serious).toEqual([]);
}

const REASON = /\d+ of \d+ correct \(\d+%\), below the 90% pass mark/;

test("after a quiz with wrong answers, the dashboard shows the objective as weak", async ({
  page,
}) => {
  await failOccurrencesQuiz(page);
  await page.goto("/dashboard");
  await expect(page.getByRole("table", { name: "By subject" })).toContainText(
    "Aviation Regulations",
  );
  const recommendations = page.getByRole("region", { name: "Study next" }).getByRole("listitem");
  await expect(recommendations.first()).toContainText(REASON);
  expect(await recommendations.count()).toBeLessThanOrEqual(5);
  await page.getByText(/^All weak objectives \(\d+\)$/).click();
  const weak = page.locator("details li").filter({ hasText: "Aviation Occurrences" });
  await expect(weak).toContainText(REASON);
  await expect(page.getByText(/educational aid/i).first()).toBeVisible();
});

test("Start quiz on a recommendation opens a quiz on that objective only", async ({ page }) => {
  await failOccurrencesQuiz(page);
  await page.goto("/dashboard");
  const first = page.getByRole("region", { name: "Study next" }).getByRole("listitem").first();
  const topic = await first.locator("p").first().textContent();
  await first.getByRole("button", { name: "Start quiz" }).click();
  await expect(page).toHaveURL(/\/practice\/[0-9a-f-]{36}$/);
  await page.getByRole("button", { name: "Submit answers" }).click();
  const breakdown = page.getByRole("table", { name: "By topic" });
  await expect(breakdown.getByRole("row")).toHaveCount(2);
  await expect(breakdown).toContainText(topic ?? "");
});

test("a topic rated low on the results page shows as low confidence", async ({ page }) => {
  await failOccurrencesQuiz(page);
  const saved = page.waitForResponse(
    (r) => r.url().endsWith("/objectives/pstar.regulations.014/confidence") && r.status() === 204,
  );
  await page.getByLabel("Your confidence in Aviation Occurrences").selectOption("low");
  await saved;
  await page.goto("/dashboard");
  await page.getByText(/^All weak objectives \(\d+\)$/).click();
  const weak = page.locator("details li").filter({ hasText: "Aviation Occurrences" });
  await expect(weak).toContainText(/; rated low confidence$/);
});

for (const colorScheme of ["dark", "light"] as const) {
  test(`the dashboard has no serious accessibility issues (${colorScheme})`, async ({ page }) => {
    await page.emulateMedia({ colorScheme });
    await failOccurrencesQuiz(page);
    await page.goto("/dashboard");
    await expect(page.getByRole("table", { name: "By subject" })).toBeVisible();
    await expectNoSeriousIssues(page);
  });
}
