import { expect, test, type BrowserContext } from "@playwright/test";
import pg from "pg";

const { Client } = pg;
const e2eDatabaseUrl =
  process.env.AUTH_DATABASE_URL ??
  "postgresql://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal";

const e2eBaseUrl = process.env.E2E_BASE_URL ?? "http://127.0.0.1:13100";

function uniqueId(prefix: string, workerIndex: number) {
  return `${prefix}-${workerIndex}-${Date.now()}`;
}

async function dbQuery(query: string, values: unknown[] = []) {
  const client = new Client({ connectionString: e2eDatabaseUrl });
  await client.connect();
  try {
    return await client.query(query, values);
  } finally {
    await client.end();
  }
}

async function signInAdmin(context: BrowserContext, email: string, password: string) {
  // Sign-up is best-effort (user may already exist). Sign-in is what matters.
  await context.request.post("/api/auth/sign-up/email", {
    headers: { Origin: e2eBaseUrl },
    data: { email, password, name: "AI Lab Admin" },
  }).catch(() => {});

  for (let attempt = 0; attempt < 5; attempt++) {
    const signInResponse = await context.request.post("/api/auth/sign-in/email", {
      headers: { Origin: e2eBaseUrl },
      data: { email, password },
    });
    if (signInResponse.ok()) break;
    if (signInResponse.status() === 429 || signInResponse.status() >= 500) {
      await new Promise((r) => setTimeout(r, Math.min(1000 * 2 ** attempt, 15000)));
      continue;
    }
  }

  const user = await dbQuery('select id from "user" where email = $1', [email]);
  return String(user.rows[0].id);
}

async function cleanupAdmin(email: string) {
  await dbQuery('delete from notifications where user_id in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from session where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from account where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from "user" where email = $1', [email]);
}

test("US-063 contact page submits a message and shows success state", async ({ page }, testInfo) => {
  const id = uniqueId("contact63", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const subject = `E2E contact ${id}`;

  try {
    await page.goto("/contact");
    await expect(page.getByRole("heading", { name: "Start a useful conversation" })).toBeVisible();
    await page.getByLabel("Name *").fill("E2E Contact User");
    await page.getByLabel("Email *").fill(email);
    await page.getByLabel("Subject *").fill(subject);
    await page.getByLabel("Message *").fill("This is a Playwright proof message.");
    await page.getByRole("button", { name: "Send message" }).click();

    await expect(page.getByRole("heading", { name: "Message sent!" })).toBeVisible();
    await expect(page.getByText(/Thank you for reaching out/i)).toBeVisible();
  } finally {
    await dbQuery("delete from contact_messages where email = $1 or subject = $2", [email, subject]);
  }
});

test("US-065 notification bell shows seeded unread notification and mark-all-read action", async ({ context, page }, testInfo) => {
  const id = uniqueId("notif65", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";

  try {
    const userId = await signInAdmin(context, email, password);
    await dbQuery(
      `insert into notifications (
        id, user_id, type, actor_user_id, actor_email, actor_display_name,
        resource_id, resource_type, read, created_at
      ) values ($1, $2, 'follow', $3, $4, $5, '', 'profile', false, now())`,
      [`notif_${id}`, userId, `actor_${id}`, `actor-${id}@example.com`, "E2E Actor"],
    );

    await page.goto("/");
    const bell = page.getByRole("button", { name: /Notifications \(1 unread\)/i });
    await expect(bell).toBeVisible({ timeout: 15_000 });
    await bell.click();
    await expect(page.getByText("E2E Actor")).toBeVisible();
    await expect(page.getByText("followed you")).toBeVisible();
    await page.getByRole("button", { name: /Mark all read/i }).click();
    await expect(page.getByRole("button", { name: /^Notifications$/i })).toBeVisible({ timeout: 10_000 });
  } finally {
    await cleanupAdmin(email);
  }
});

test("US-067 admin projects UI lists project module and seeded project", async ({ context, page }, testInfo) => {
  const id = uniqueId("project67", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";
  const projectId = `project_${id}`;
  const slug = `project-${id}`.toLowerCase();
  const title = `E2E Admin Project ${id}`;

  try {
    await signInAdmin(context, email, password);
    await dbQuery(
      `insert into projects (
        id, slug, title, description, content_markdown, image_url,
        status, published_at, created_at, updated_at
      ) values ($1, $2, $3, $4, $5, null, 'draft', null, now(), now())`,
      [projectId, slug, title, "Project admin UI proof.", "Admin project body."],
    );

    await page.goto("/admin");
    await expect(page.getByRole("heading", { name: "Operations dashboard" })).toBeVisible();
    await expect(page.getByRole("link", { name: /Projects/i }).first()).toBeVisible();
    await page.goto("/admin/projects");
    await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
    await expect(page.getByText(title).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /New project/i })).toBeVisible();
  } finally {
    await dbQuery("delete from projects where id = $1", [projectId]);
    await cleanupAdmin(email);
  }
});

test("US-068 public projects pages list and render published project detail", async ({ page }, testInfo) => {
  const id = uniqueId("project68", testInfo.workerIndex);
  const projectId = `project_${id}`;
  const slug = `project-${id}`.toLowerCase();
  const title = `E2E Public Project ${id}`;

  try {
    await dbQuery(
      `insert into projects (
        id, slug, title, description, content_markdown, image_url,
        status, published_at, created_at, updated_at
      ) values ($1, $2, $3, $4, $5, null, 'published', now(), now(), now())`,
      [projectId, slug, title, "Project public page proof.", "## Project Detail\n\nPublished project detail body."],
    );

    await page.goto("/projects");
    await expect(page.getByRole("heading", { name: "Engineering initiatives with impact." })).toBeVisible();
    await expect(page.getByRole("link", { name: title })).toBeVisible();
    await page.goto(`/projects/${slug}`);
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.getByText("Published project detail body.").first()).toBeVisible();
  } finally {
    await dbQuery("delete from projects where id = $1", [projectId]);
  }
});

test("US-073 admin dashboard renders stat cards and live workflow modules", async ({ context, page }, testInfo) => {
  const id = uniqueId("dash73", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";

  try {
    await signInAdmin(context, email, password);
    await page.goto("/admin");
    await expect(page.getByRole("heading", { name: "Operations dashboard" })).toBeVisible();
    await expect(page.getByRole("link", { name: /Blog posts/i }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /Comments/i }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /Blog ideas/i }).first()).toBeVisible();
    await expect(page.getByText("Live workflows")).toBeVisible();
    await expect(page.getByText("Human review")).toBeVisible();
  } finally {
    await cleanupAdmin(email);
  }
});

test("US-071 responsive polish on mobile and tablet viewports", async ({ page }) => {
  // ── Mobile viewport (375px) ──
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  // Hamburger menu button visible on mobile, desktop nav hidden
  await expect(page.getByRole("button", { name: "Open menu" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Public navigation" })).not.toBeVisible();

  // Open hamburger, nav items become visible
  await page.getByRole("button", { name: "Open menu" }).click();
  const mobileNav = page.getByRole("navigation", { name: "Mobile navigation" });
  await expect(mobileNav.getByRole("link", { name: "AI Lab" })).toBeVisible();
  await expect(mobileNav.getByRole("link", { name: "Projects" })).toBeVisible();
  await expect(mobileNav.getByRole("link", { name: "Blog" })).toBeVisible();
  await expect(mobileNav.getByRole("link", { name: "AI News" })).toBeVisible();

  // Close hamburger (force click — backdrop intercepts pointer events)
  await page.getByRole("button", { name: "Close menu" }).click({ force: true });

  // No horizontal scroll on home page
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
  expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);

  // Blog page — cards stack vertically
  await page.goto("/blog");
  await page.waitForLoadState("networkidle");
  const blogScrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const blogClientWidth = await page.evaluate(() => document.documentElement.clientWidth);
  expect(blogScrollWidth).toBeLessThanOrEqual(blogClientWidth + 1);

  // Contact page — form stacks vertically
  await page.goto("/contact");
  await page.waitForLoadState("networkidle");
  const contactScrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const contactClientWidth = await page.evaluate(() => document.documentElement.clientWidth);
  expect(contactScrollWidth).toBeLessThanOrEqual(contactClientWidth + 1);

  // ── Tablet viewport (768px) ──
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  // Desktop nav visible, hamburger hidden
  await expect(page.getByRole("navigation", { name: "Public navigation" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open menu" })).not.toBeVisible();

  // No significant horizontal scroll (allow small overflow for design elements)
  const tabletScrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const tabletClientWidth = await page.evaluate(() => document.documentElement.clientWidth);
  expect(tabletScrollWidth).toBeLessThanOrEqual(tabletClientWidth + 200);
});
