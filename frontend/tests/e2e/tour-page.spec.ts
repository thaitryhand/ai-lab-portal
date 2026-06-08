import { expect, test } from "@playwright/test";

const e2eBaseUrl = process.env.E2E_BASE_URL ?? "http://127.0.0.1:13100";

/* ── US-102: Navigation Integration & Hero ── */

test.describe("Tour — Navigation & Hero (US-102)", () => {
  test("has a featured Tour link in the global navigation", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // The Tour link has a featured green pill
    const tourLink = page.locator('nav a[href="/tour"]').first();
    await expect(tourLink).toBeVisible();

    // It should have the green featured styling (contains the word "Tour")
    await expect(tourLink).toContainText("Tour");
  });

  test("navigates to Tour page and shows hero section", async ({ page }) => {
    await page.goto("/tour");
    await page.waitForLoadState("networkidle");

    // Hero section should show the heading "AI Lab in Action"
    await expect(page.locator("h1")).toContainText("AI Lab");
    await expect(page.locator("h1")).toContainText("Action");

    // Hero should have CTA buttons (scroll-to-section buttons)
    await expect(page.getByText("Watch the pipeline").first()).toBeVisible();
    await expect(page.getByText("See live examples").first()).toBeVisible();

    // The page title should indicate it's a tour
    await expect(page).toHaveTitle(/Tour/);
  });
});

/* ── US-101: Pipeline — Stage Cards ── */

test.describe("Tour — Pipeline Stages (US-100)", () => {
  test("renders all 7 pipeline stage cards", async ({ page }) => {
    await page.goto("/tour");
    await page.waitForLoadState("networkidle");

    // Pipeline section: look for stage cards
    const pipelineSection = page.locator("section").filter({ hasText: /Pipeline|Stage|Flow/ }).first();
    await expect(pipelineSection).toBeVisible();

    // Verify stage labels are present (7 stages)
    const stages = ["Project Context", "Idea Generation", "Outline", "Draft Writer", "Technical Review", "Marketing Metadata", "Publish"];
    for (const stage of stages) {
      await expect(page.getByText(stage, { exact: false }).first()).toBeVisible();
    }
  });
});

/* ── US-101: Stats Counter & Live Examples ── */

test.describe("Tour — Stats & Examples (US-101)", () => {
  test("shows stats section with content counts", async ({ page }) => {
    await page.goto("/tour");
    await page.waitForLoadState("networkidle");

    // Stats section should show counts for blog posts, showcases, projects, news
    // These use animated counters — at minimum the stat labels should be visible
    const statLabels = ["Blog Posts", "Showcases", "Projects", "AI News"];
    for (const label of statLabels) {
      await expect(page.getByText(label, { exact: false }).first()).toBeVisible();
    }
  });

  test("shows content examples section", async ({ page }) => {
    await page.goto("/tour");
    await page.waitForLoadState("networkidle");

    // Examples section heading
    await expect(page.getByText("Real content, real results", { exact: false })).toBeVisible();

    // Example cards should be visible (links to blog/showcases/projects)
    const exampleCards = page.locator("section#tour-examples a");
    const count = await exampleCards.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test("shows CTA section at the bottom", async ({ page }) => {
    await page.goto("/tour");
    await page.waitForLoadState("networkidle");

    // CTA section
    await expect(page.getByText("Ready to build your").first()).toBeVisible();
    await expect(page.getByText("Start a project")).toBeVisible();
    await expect(page.getByText("Explore the Lab")).toBeVisible();
  });
});
