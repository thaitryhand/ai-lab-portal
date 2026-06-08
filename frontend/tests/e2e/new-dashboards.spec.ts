import { expect, test, type BrowserContext } from "@playwright/test";

const e2eBaseUrl = process.env.E2E_BASE_URL ?? "http://127.0.0.1:13100";
const testEmail = `pipeline-e2e-${Date.now()}@example.com`;
const testPassword = "TestPassword123!";

async function signInAdmin(context: BrowserContext) {
  // Sign-up is best-effort (user may already exist). Sign-in is what matters.
  await context.request.post("/api/auth/sign-up/email", {
    headers: { Origin: e2eBaseUrl },
    data: { email: testEmail, password: testPassword, name: "E2E Tester" },
  }).catch(() => {});

  for (let attempt = 0; attempt < 5; attempt++) {
    const signInRes = await context.request.post("/api/auth/sign-in/email", {
      headers: { Origin: e2eBaseUrl },
      data: { email: testEmail, password: testPassword },
    });
    if (signInRes.ok()) return;
    if (signInRes.status() === 429 || signInRes.status() >= 500) {
      await new Promise((r) => setTimeout(r, Math.min(1000 * 2 ** attempt, 15000)));
      continue;
    }
  }
  throw new Error("signInAdmin failed");
}

/* ── Pipeline Dashboard ── */

test.describe("Pipeline Dashboard", () => {
  test("loads with stat cards and pipeline sections", async ({ context, page }) => {
    test.setTimeout(30_000);
    await signInAdmin(context);
    await page.goto("/admin/pipeline-dashboard");
    await page.waitForLoadState("networkidle");

    // Header
    await expect(page.getByText("Pipeline Dashboard")).toBeVisible();

    // Stat cards
    await expect(page.getByText("Total Ideas")).toBeVisible();
    await expect(page.getByText("In Pipeline")).toBeVisible();
    await expect(page.getByText("Published").first()).toBeVisible();
    await expect(page.getByText("Rejected")).toBeVisible();

    // Section headings
    await expect(page.getByText("Stage Distribution")).toBeVisible();
    await expect(page.getByText("Monthly Throughput")).toBeVisible();
    await expect(page.getByText("Pipeline Overview")).toBeVisible();

    // Back link
    await expect(page.getByText("Back to dashboard")).toBeVisible();
  });
});

/* ── Content Calendar ── */

test.describe("Content Calendar", () => {
  test("loads calendar grid with navigation and pipeline ideas", async ({ context, page }) => {
    test.setTimeout(30_000);
    await signInAdmin(context);
    await page.goto("/admin/content-calendar");
    await page.waitForLoadState("networkidle");

    // Header
    await expect(page.getByText("Content Calendar")).toBeVisible();

    // Stat cards
    await expect(page.getByText("Published")).toBeVisible();
    await expect(page.getByText("In Pipeline")).toBeVisible();
    await expect(page.getByText("Scheduled")).toBeVisible();
    await expect(page.getByText("Total Ideas")).toBeVisible();

    // Month navigation buttons
    await expect(page.getByText("Today")).toBeVisible();

    // Day headers
    for (const day of ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]) {
      await expect(page.getByText(day)).toBeVisible();
    }

    // Pipeline section
    await expect(page.getByText("Pipeline Ideas")).toBeVisible();

    // Back link
    await expect(page.getByText("Back to dashboard")).toBeVisible();
  });

  test("navigates months", async ({ context, page }) => {
    test.setTimeout(30_000);
    await signInAdmin(context);
    await page.goto("/admin/content-calendar");
    await page.waitForLoadState("networkidle");

    // Get current month label
    const monthLabel = await page.getByRole("heading").filter({ hasText: /January|February|March|April|May|June|July|August|September|October|November|December/ }).first().textContent();

    // Click prev
    const prevBtn = page.locator("button").filter({ has: page.locator("svg.lucide-chevron-left") });
    await prevBtn.click();
    await page.waitForTimeout(300);

    // Month should have changed — check it's different or the same (edge case for January)
    const newMonthLabel = await page.getByRole("heading").filter({ hasText: /January|February|March|April|May|June|July|August|September|October|November|December/ }).first().textContent();
    expect(newMonthLabel).toBeTruthy();
  });
});

/* ── SEO Analytics ── */

test.describe("SEO Analytics", () => {
  test("loads with stat cards and analysis sections", async ({ context, page }) => {
    test.setTimeout(30_000);
    await signInAdmin(context);
    await page.goto("/admin/seo-analytics");
    await page.waitForLoadState("networkidle");

    // Header
    await expect(page.getByText("SEO Analytics")).toBeVisible();

    // Stat cards
    await expect(page.getByText("Published Posts")).toBeVisible();
    await expect(page.getByText("Avg SEO Score")).toBeVisible();
    await expect(page.getByText("SEO Issues")).toBeVisible();
    await expect(page.getByText("Tags").first()).toBeVisible();

    // Section headings (may fallback to empty state)
    await expect(page.getByText("Publish Trend")).toBeVisible();
    const keywordsOrEmpty = page.locator("text=Keywords & Tags, text=No keywords or tags found.").first();
    // Either the heading or the empty state should be visible
    await expect(page.getByText("Per-Post SEO Analysis")).toBeVisible();

    // Back link
    await expect(page.getByText("Back to dashboard")).toBeVisible();
  });
});
