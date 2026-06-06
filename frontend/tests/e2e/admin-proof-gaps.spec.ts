import { expect, test, type BrowserContext } from "@playwright/test";
import pg from "pg";

const { Client } = pg;
const e2eDatabaseUrl =
  process.env.AUTH_DATABASE_URL ??
  "postgresql://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal";

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

async function signInAdmin(context: BrowserContext, email: string, password: string, retries = 5) {
  for (let attempt = 0; attempt < retries; attempt++) {
    const signUpResponse = await context.request.post("/api/auth/sign-up/email", {
      headers: { Origin: "http://127.0.0.1:13100" },
      data: { email, password, name: "AI Lab Admin" },
    });
    const signInResponse = await context.request.post("/api/auth/sign-in/email", {
      headers: { Origin: "http://127.0.0.1:13100" },
      data: { email, password },
    });

    if (signUpResponse.ok() && signInResponse.ok()) return;

    const body = await signUpResponse.text();
    // Retry on rate limiting or server errors
    if (signUpResponse.status() === 429 || signUpResponse.status() >= 500) {
      const delay = Math.min(1000 * 2 ** attempt, 15_000);
      console.warn('Sign-in attempt ' + (attempt + 1) + ' failed (' + signUpResponse.status() + '), retrying in ' + delay + 'ms');
      await new Promise((r) => setTimeout(r, delay));
      continue;
    }
    expect(signUpResponse.ok(), body).toBeTruthy();
    expect(signInResponse.ok(), await signInResponse.text()).toBeTruthy();
  }
  throw new Error('signInAdmin failed after ' + retries + ' retries');
}

async function cleanupAdmin(email: string) {
  await dbQuery('delete from session where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from account where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from "user" where email = $1', [email]);
}

test("admin blog idea detail shows queued generation job status", async ({ context, page }, testInfo) => {
  const id = uniqueId("idea-job", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";
  const ideaId = `idea_${id}`;
  const taskId = `task_${id}`;

  await signInAdmin(context, email, password);
  await dbQuery(
    `
    insert into blog_ideas (
      id, title, angle, target_reader, article_goal, positioning_notes,
      source, source_project_context, status, outline_sections,
      created_at, updated_at
    )
    values ($1, $2, $3, $4, $5, $6, 'manual', null, 'approved', '[]', now(), now())
    `,
    [
      ideaId,
      "Queued Generation E2E Proof",
      "AI operations",
      "Engineering leaders",
      "Show generation job polling",
      "[]",
    ],
  );
  await dbQuery(
    `
    insert into blog_generation_jobs (
      id, blog_idea_id, stage, celery_task_id, status, created_at, updated_at
    )
    values ($1, $2, 'outline', $3, 'queued', now(), now())
    `,
    [`genjob_${id}`, ideaId, taskId],
  );

  try {
    await page.goto(
      `/admin/blog-ideas/${ideaId}?opStage=outline&opStatus=queued&taskId=${taskId}&message=Outline%20generation%20started`,
    );

    await expect(page.getByRole("heading", { name: "Queued Generation E2E Proof" })).toBeVisible();
    await expect(page.getByRole("status")).toContainText("Generation queued");
    await expect(page.getByRole("status")).toContainText(`Task: ${taskId}`);
  } finally {
    await dbQuery("delete from blog_generation_jobs where blog_idea_id = $1", [ideaId]);
    await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
    await cleanupAdmin(email);
  }
});

test("admin blog idea detail can extract claim evidence ledger items", async ({ context, page }, testInfo) => {
  const id = uniqueId("idea-claims", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";
  const ideaId = `idea_${id}`;

  await signInAdmin(context, email, password);
  await dbQuery(
    `
    insert into blog_ideas (
      id, title, angle, target_reader, article_goal, positioning_notes,
      source, source_project_context, status, outline_sections,
      draft_markdown, draft_status, created_at, updated_at
    )
    values ($1, $2, $3, $4, $5, $6, 'manual', null, 'approved', '[]', $7, 'approved', now(), now())
    `,
    [
      ideaId,
      "Claim Ledger E2E Proof",
      "AI quality",
      "Technical buyers",
      "Prove claim evidence workflow",
      "[]",
      "The review workflow reduces manual QA time by 40% for 12 users.",
    ],
  );

  try {
    await page.goto(`/admin/blog-ideas/${ideaId}`);
    await expect(page.getByRole("heading", { name: "Claim Ledger E2E Proof" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Extract claims from draft" })).toBeVisible();

    await page.getByRole("button", { name: "Extract claims from draft" }).click();
    await expect(page.getByText("reduces manual QA time by 40%").first()).toBeVisible();
  } finally {
    await dbQuery("delete from blog_claims where blog_idea_id = $1", [ideaId]);
    await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
    await cleanupAdmin(email);
  }
});

test("admin can create and view a news source", async ({ context, page }, testInfo) => {
  const id = uniqueId("news-source", testInfo.workerIndex);
  const email = `${id}@example.com`;
  const password = "test-admin-password-123456";
  const sourceName = `E2E News Source ${id}`;
  const sourceUrl = `https://example.com/${id}.xml`;

  await signInAdmin(context, email, password);

  try {
    await page.goto("/admin/news-sources/new");
    await expect(page.getByRole("heading", { name: "Add news source" })).toBeVisible();
    await page.getByRole("textbox", { name: "Name" }).first().fill(sourceName);
    await page.getByRole("textbox", { name: /URL/i }).fill(sourceUrl);
    await page.getByLabel("Priority").selectOption("high");
    await page.getByRole("button", { name: "Save source" }).click();

    await expect(page).toHaveURL(/\/admin\/news-sources$/);
    await expect(page.getByRole("heading", { name: "News sources" })).toBeVisible();
    await expect(page.getByText(sourceName)).toBeVisible();
    await expect(page.getByText(sourceUrl)).toBeVisible();
  } finally {
    await dbQuery("delete from news_sources where name = $1", [sourceName]);
    await cleanupAdmin(email);
  }
});


// --- US-026: Blog ideas list CRUD ---

test.describe("US-026: Admin blog ideas list CRUD", () => {
  test("admin can view blog ideas list and approve/reject from list", async ({ context, page }, testInfo) => {
    const id = uniqueId("blogidea", testInfo.workerIndex);
    const email = `${id}@example.com`;
    const password = "test-admin-password-123456";
    const ideaId = `idea_${id}`;
    const title = `Blog Idea List E2E ${id}`;

    await signInAdmin(context, email, password);
    await dbQuery(
      `
      insert into blog_ideas (
        id, title, angle, target_reader, article_goal, positioning_notes,
        source, source_project_context, status, outline_sections,
        created_at, updated_at
      )
      values ($1, $2, $3, $4, $5, $6, 'manual', null, 'pending', '[]', now(), now())
      `,
      [ideaId, title, "E2E test angle", "Developers", "Test approve flow", "[]"],
    );

    try {
      // Visit blog ideas list
      await page.goto("/admin/blog-ideas");
      await expect(page.getByRole("heading", { name: /Blog ideas/i })).toBeVisible();
      await expect(page.getByRole("link", { name: new RegExp(title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), "i") })).toBeVisible();

      // Click the Approve button for this idea
      await page.getByRole("button", { name: "Approve" }).first().click();
      await page.waitForTimeout(500);
    } finally {
      await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
      await cleanupAdmin(email);
    }
  });
});

// --- US-030: AI Blog Agent regenerate polish ---

test.describe("US-030: AI Blog Agent regenerate polish", () => {
  // 1. Rejected draft stage � requires draft_status=rejected + outline_status=approved
  test("admin can see regenerate button for rejected draft stage", async ({ context, page }, testInfo) => {
    const id = uniqueId("regen-draft", testInfo.workerIndex);
    const email = `${id}@example.com`;
    const password = "test-admin-password-123456";
    const ideaId = `idea_${id}`;
    const title = `Regen Draft E2E ${id}`;

    await signInAdmin(context, email, password);
    await dbQuery(
      "insert into blog_ideas (id, title, angle, target_reader, article_goal, positioning_notes, source, source_project_context, status, outline_status, outline_sections, draft_markdown, draft_status, created_at, updated_at) values ($1, $2, $3, $4, $5, $6, 'manual', null, 'pending', 'approved', '[]', $7, 'rejected', now(), now())",
      [ideaId, title, "AI testing", "Developers", "Test regenerate", "[]", "Draft that was rejected"],
    );

    try {
      await page.goto(`/admin/blog-ideas/${ideaId}`);
      await expect(page.getByRole("heading", { name: title })).toBeVisible({ timeout: 10000 });
      await expect(page.getByRole("button", { name: /regenerate draft/i })).toBeVisible();
    } finally {
      await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
      await cleanupAdmin(email);
    }
  });

  // 2. Rejected technical review � button label is "Run review again"
  test("admin can see run review again button after technical review rejected", async ({ context, page }, testInfo) => {
    const id = uniqueId("regen-tech", testInfo.workerIndex);
    const email = `${id}@example.com`;
    const password = "test-admin-password-123456";
    const ideaId = `idea_${id}`;
    const title = `Regen Tech E2E ${id}`;

    await signInAdmin(context, email, password);
    // Need technical_review JSON so the content branch renders (not EmptyState)
    await dbQuery(
      "insert into blog_ideas (id, title, angle, target_reader, article_goal, positioning_notes, source, source_project_context, status, outline_sections, draft_markdown, draft_status, technical_review_status, technical_review, created_at, updated_at) values ($1, $2, $3, $4, $5, $6, 'manual', null, 'pending', '[]', $7, 'approved', 'rejected', $8::jsonb, now(), now())",
      [ideaId, title, "AI pipeline", "Engineers", "Test tech review rejection", "[]", "Draft content", '{"overall_risk":"low","issues":[],"approval_recommendation":"approved"}'],
    );

    try {
      await page.goto(`/admin/blog-ideas/${ideaId}`);
      await expect(page.getByRole("heading", { name: title })).toBeVisible({ timeout: 10000 });
      await expect(page.getByRole("button", { name: /run review again/i })).toBeVisible();
    } finally {
      await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
      await cleanupAdmin(email);
    }
  });

  // 3. Rejected marketing � field is marketing_status (not marketing_review_status)
  test("admin can see regenerate marketing button after marketing rejected", async ({ context, page }, testInfo) => {
    const id = uniqueId("regen-mktg", testInfo.workerIndex);
    const email = `${id}@example.com`;
    const password = "test-admin-password-123456";
    const ideaId = `idea_${id}`;
    const title = `Regen Mktg E2E ${id}`;

    await signInAdmin(context, email, password);
    // Need marketing_metadata JSON so the content branch renders (not EmptyState)
    await dbQuery(
      "insert into blog_ideas (id, title, angle, target_reader, article_goal, positioning_notes, source, source_project_context, status, outline_sections, draft_markdown, draft_status, technical_review_status, marketing_status, marketing_metadata, created_at, updated_at) values ($1, $2, $3, $4, $5, $6, 'manual', null, 'pending', '[]', $7, 'approved', 'approved', 'rejected', $8::jsonb, now(), now())",
      [ideaId, title, "AI content", "Readers", "Test mktg rejection", "[]", "Draft", '{"seo_title":"Test","meta_description":"Test","social_headline":"Test","social_description":"Test"}'],
    );

    try {
      await page.goto(`/admin/blog-ideas/${ideaId}`);
      await expect(page.getByRole("heading", { name: title })).toBeVisible({ timeout: 10000 });
      await expect(page.getByRole("button", { name: /regenerate marketing/i })).toBeVisible();
    } finally {
      await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
      await cleanupAdmin(email);
    }
  });
});

// --- US-032: Publish approved blog idea to CMS ---

test.describe("US-032: Publish approved blog idea to CMS", () => {
  test("admin can see publish button for fully approved idea", async ({ context, page }, testInfo) => {
    const id = uniqueId("publish", testInfo.workerIndex);
    const email = `${id}@example.com`;
    const password = "test-admin-password-123456";
    const ideaId = `idea_${id}`;
    const title = `Publish E2E ${id}`;

    await signInAdmin(context, email, password);
    // Need marketing_metadata + technical_review JSON so content branches render (not EmptyState)
    await dbQuery(
      "insert into blog_ideas (id, title, angle, target_reader, article_goal, positioning_notes, source, source_project_context, status, outline_sections, draft_markdown, draft_status, technical_review_status, technical_review, marketing_status, marketing_metadata, created_at, updated_at) values ($1, $2, $3, $4, $5, $6, 'manual', null, 'approved', '[]', $7, 'approved', 'approved', $8::jsonb, 'approved', $9::jsonb, now(), now())",
      [ideaId, title, "AI deploy", "Ops", "Test publish", "[]", "publishable draft", '{"overall_risk":"low","issues":[],"approval_recommendation":"approved"}', '{"seo_title":"Test","meta_description":"Test","social_headline":"Test","social_description":"Test"}'],
    );

    try {
      await page.goto(`/admin/blog-ideas/${ideaId}`);
      await expect(page.getByRole("heading", { name: title })).toBeVisible({ timeout: 10000 });
      await expect(page.getByRole("button", { name: /publish to blog/i })).toBeVisible();
    } finally {
      await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
      await cleanupAdmin(email);
    }
  });
});

