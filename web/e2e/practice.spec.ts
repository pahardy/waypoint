import AxeBuilder from "@axe-core/playwright";
import { type Page, expect, test } from "@playwright/test";

async function answerAll(page: Page, count: number) {
  for (let i = 0; i < count; i++) {
    const question = page.getByRole("group", { name: `Question ${i + 1} of ${count}` });
    await question.getByRole("radio").first().check();
  }
  await expect(page.getByText(`${count} of ${count} answered`)).toBeVisible();
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

test("completing a 10-question quiz shows the score and topic breakdown", async ({
  page,
}) => {
  await page.goto("/practice");
  await page.getByRole("region", { name: "PSTAR topic quiz" }).getByRole("button", { name: "Start quiz" }).click();
  await expect(page).toHaveURL(/\/practice\/[0-9a-f-]{36}$/);
  await expect(page.getByText("OFFICIAL").first()).toBeVisible();
  await answerAll(page, 10);
  await page.getByRole("button", { name: "Submit answers" }).click();

  await expect(page).toHaveURL(/\/results\/[0-9a-f-]{36}$/);
  await expect(page.getByText(/^\d+ \/ 10 \(\d+%\)$/)).toBeVisible();
  await expect(page.getByText(/90% PSTAR pass mark/)).toBeVisible();
  const breakdown = page.getByRole("table", { name: "By topic" });
  await expect(breakdown.getByRole("row").nth(1)).toBeVisible();
  await expect(page.getByRole("region", { name: "Question review" }).getByRole("listitem")).toHaveCount(10);
});

test("a topic quiz draws only from that topic", async ({ page }) => {
  await page.goto("/practice");
  const quiz = page.getByRole("region", { name: "PSTAR topic quiz" });
  await quiz.getByLabel("Topic").selectOption({ label: "Aviation Occurrences (5)" });
  await quiz.getByRole("button", { name: "Start quiz" }).click();
  await answerAll(page, 5);
  await page.getByRole("button", { name: "Submit answers" }).click();
  const breakdown = page.getByRole("table");
  await expect(breakdown.getByRole("row")).toHaveCount(2);
  await expect(breakdown).toContainText("Aviation Occurrences");
});

test("the mock exam shows the unverified time limit and a timer", async ({ page }) => {
  await page.goto("/practice");
  const mock = page.getByRole("region", { name: "PSTAR mock exam" });
  await expect(mock).toContainText("Time limit 90 minutes");
  await expect(mock.getByText("UNVERIFIED")).toBeVisible();
  await mock.getByRole("button", { name: "Start mock exam" }).click();
  await expect(page.getByRole("timer", { name: "Time remaining" })).toHaveText(/^1:(30|29):\d\d$/);
  await expect(page.getByText("0 of 50 answered")).toBeVisible();
});

test("the PPAER mock exam has a 3-hour timer and results by subject", async ({ page }) => {
  await page.goto("/practice");
  const mock = page.getByRole("region", { name: "PPAER mock exam" });
  await expect(mock).toContainText("Time limit 180 minutes");
  await expect(mock).toContainText("25 questions from each subject");
  await mock.getByRole("button", { name: "Start mock exam" }).click();
  await expect(page.getByRole("timer", { name: "Time remaining" })).toHaveText(/^(3:00|2:59):\d\d$/);
  await expect(page.getByText("0 of 100 answered")).toBeVisible();
  await expect(page.getByText("PRACTICE").first()).toBeVisible();
  await page.getByRole("button", { name: "Submit answers" }).click();

  await expect(page.getByText(/^Fail: below the 60% PPAER pass mark/)).toBeVisible();
  const subjects = page.getByRole("table", { name: "By subject" });
  await expect(subjects.getByRole("row")).toHaveCount(5);
  await expect(subjects).toContainText("Meteorology");
});

for (const colorScheme of ["dark", "light"] as const) {
  test(`practice and results pages have no serious accessibility issues (${colorScheme})`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme });
    await page.goto("/practice");
    const quiz = page.getByRole("region", { name: "PSTAR topic quiz" });
    await expect(quiz.getByRole("button", { name: "Start quiz" })).toBeVisible();
    await expectNoSeriousIssues(page);
    await quiz.getByRole("button", { name: "Start quiz" }).click();
    await answerAll(page, 10);
    await expectNoSeriousIssues(page);
    await page.getByRole("button", { name: "Submit answers" }).click();
    await expect(page.getByRole("table")).toBeVisible();
    await expectNoSeriousIssues(page);
  });
}
