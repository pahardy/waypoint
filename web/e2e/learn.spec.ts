import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("asking a question streams the answer with a citation chip that opens the source", async ({
  page,
}) => {
  await page.goto("/learn");
  await expect(page.getByText(/educational aid/)).toBeVisible();
  await page.getByLabel("Studying for").selectOption("PSTAR");
  await page.getByLabel("Your question").fill("How long after drinking can I fly?");
  await page.getByRole("button", { name: "Ask" }).click();

  const log = page.getByRole("log", { name: "Conversation" });
  await expect(log).toContainText("You must not fly within 12 hours");
  const chip = page.getByRole("button", { name: "Source: CAR 602.03" });
  await expect(chip).toBeVisible();
  await expect(log.getByText("NON-CANADIAN")).toBeVisible();

  await chip.click();
  const detail = page.getByRole("region", { name: "Source detail: CAR 602.03" });
  await expect(detail).toContainText("Canadian Aviation Regulations");
  await expect(detail).toContainText("2026-10-01");
  await expect(detail).toContainText("within 12 hours after drinking");
});

for (const colorScheme of ["dark", "light"] as const) {
  test(`the chat page has no serious accessibility issues (${colorScheme})`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme });
    await page.goto("/learn");
    await page.getByLabel("Your question").fill("How long after drinking can I fly?");
    await page.getByRole("button", { name: "Ask" }).click();
    await page.getByRole("button", { name: "Source: PHAK p.437" }).click();
    await expect(page.getByRole("region", { name: /Source detail/ })).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    const serious = results.violations.filter((v) =>
      ["serious", "critical"].includes(v.impact ?? ""),
    );
    expect(serious).toEqual([]);
  });
}
