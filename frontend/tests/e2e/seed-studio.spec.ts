import { expect, test, type BrowserContext } from "@playwright/test";

const e2eBaseUrl = process.env.E2E_BASE_URL ?? "http://127.0.0.1:13100";
const testEmail = `seed-studio-test-${Date.now()}@example.com`;
const testPassword = "TestPassword123!";

async function signInAdmin(context: BrowserContext) {
  // Sign-up is best-effort (user may already exist). Sign-in is what matters.
  await context.request.post("/api/auth/sign-up/email", {
    headers: { Origin: e2eBaseUrl },
    data: { email: testEmail, password: testPassword, name: "Seed Studio Tester" },
  }).catch(() => {});

  for (let attempt = 0; attempt < 5; attempt++) {
    const signInRes = await context.request.post("/api/auth/sign-in/email", {
      headers: { Origin: e2eBaseUrl },
      data: { email: testEmail, password: testPassword },
    });

    if (signInRes.ok()) return;

    const delay = Math.min(1000 * 2 ** attempt, 15_000);
    await new Promise((r) => setTimeout(r, delay));
  }
  throw new Error("signInAdmin failed after retries");
}

test.describe("Admin Seed Studio", () => {
  test("renders content type cards and seeds content successfully", async ({ context, page }) => {
    test.setTimeout(45_000);

    // Sign in and navigate to seed studio
    await signInAdmin(context);
    await page.goto("/admin/seed-studio");
    await page.waitForLoadState("networkidle");

    // Verify page header
    await expect(page.getByText("Seed Studio")).toBeVisible();
    await expect(page.getByText("Populate the platform with demo content")).toBeVisible();

    // Verify 3 content type cards are rendered
    const cardLabels = ["Blog Posts", "Showcases", "Projects"];
    for (const label of cardLabels) {
      await expect(page.getByText(label).first()).toBeVisible();
    }

    // Verify descriptions
    await expect(page.getByText("6 editorial posts about AI agents").first()).toBeVisible();
    await expect(page.getByText("5 client case studies").first()).toBeVisible();
    await expect(page.getByText("4 published projects for AI pipeline").first()).toBeVisible();

    // Click "Seed all content"
    const seedButton = page.getByRole("button", { name: /seed all content/i });
    await expect(seedButton).toBeVisible();
    await seedButton.click();

    // Wait for success state
    await expect(page.getByText(/seeded/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/blog posts? added|all content already exists/i)).toBeVisible();

    // Verify button text changed
    await expect(page.getByRole("button", { name: /seed again/i })).toBeVisible();
  });

  test("dashboard shows Seed Studio module card", async ({ context, page }) => {
    test.setTimeout(30_000);

    await signInAdmin(context);
    await page.goto("/admin");
    await page.waitForLoadState("networkidle");

    // Verify Seed Studio card exists on dashboard
    const seedCard = page.locator("a[href='/admin/seed-studio']").first();
    await expect(seedCard).toBeVisible({ timeout: 10_000 });

    // Click through to verify it works
    await seedCard.click();
    await expect(page).toHaveURL(/\/admin\/seed-studio/);
    await expect(page.getByText("Seed Studio")).toBeVisible();
  });
});
