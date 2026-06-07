import { expect, test } from "@playwright/test";

import {
  cleanupAdmin,
  clickPipelineActionAndWait,
  dbQuery,
  signInAdmin,
  uniqueId,
  waitForIdeaGenerationRedirect,
} from "./helpers";

const E2E_IDEA_TITLE = "E2E Golden Path Blog Idea";
const E2E_PUBLIC_SLUG = "e2e-golden-path-blog-idea";

test.describe("US-086: AI Blog Agent golden path", () => {
  test.describe.configure({ mode: "serial", timeout: 180_000 });

  test("generate from project → semi-auto pipeline (with SEO audit) → publish → public blog", async ({
    context,
    page,
  }, testInfo) => {
    const id = uniqueId("golden", testInfo.workerIndex);
    const email = `${id}@example.com`;
    const password = "test-admin-password-123456";
    const projectId = `project_${id}`;
    const projectSlug = `e2e-project-${id}`;

    await signInAdmin(context, email, password);

    await dbQuery(
      `
      insert into projects (
        id, slug, title, description, content_markdown, status, published_at, created_at, updated_at
      )
      values ($1, $2, $3, $4, $5, 'published', now(), now(), now())
      `,
      [
        projectId,
        projectSlug,
        `E2E Project ${id}`,
        "Analytics platform for game studios",
        "## Architecture\nUses embeddings and batch scoring pipelines.",
      ],
    );

    let ideaId: string | undefined;

    try {
      await page.goto("/admin/blog-ideas/new");
      await expect(page.getByRole("heading", { name: "New blog idea" })).toBeVisible();

      await page.getByRole("button", { name: "Project", exact: true }).click();
      await page.locator("#contextId").selectOption(projectId);
      await page.getByRole("button", { name: "Generate idea" }).click();

      await waitForIdeaGenerationRedirect(page);
      await expect(page.getByRole("heading", { name: E2E_IDEA_TITLE })).toBeVisible({
        timeout: 30_000,
      });

      const url = page.url();
      ideaId = url.match(/\/admin\/blog-ideas\/([^/?]+)/)?.[1];
      expect(ideaId).toBeTruthy();

      // Gate 1: Approve idea → generate outline
      await clickPipelineActionAndWait(page, /Approve & generate outline/i);
      await expect(page.getByText("Context").first()).toBeVisible({ timeout: 30_000 });

      // Gate 2: Approve outline → generate draft
      await clickPipelineActionAndWait(page, /Approve & generate draft/i);
      await expect(page.getByText("Semi-auto keeps humans in the loop").first()).toBeVisible({
        timeout: 30_000,
      });

      // Gate 3: Approve draft → run technical review
      await clickPipelineActionAndWait(page, /Approve & run review/i);
      await expect(page.getByText("Risk: low").first()).toBeVisible({
        timeout: 30_000,
      });

      // Gate 4: Accept review → generate marketing metadata
      await clickPipelineActionAndWait(page, /Accept & generate marketing/i);
      await expect(page.getByText("SEO Title").first()).toBeVisible({ timeout: 30_000 });

      // Gate 5: Approve marketing → run SEO audit (new stage)
      await clickPipelineActionAndWait(page, /Approve & run SEO audit/i);
      await expect(page.getByText(/SEO Score|Overall Score|Title Analysis/i).first()).toBeVisible({
        timeout: 30_000,
      });

      // Gate 6: Approve SEO audit → extract claims
      await clickPipelineActionAndWait(page, /Approve & extract claims/i);
      await expect(page.getByText(/Claims|No claims in the ledger/i).first()).toBeVisible({
        timeout: 30_000,
      });

      // Gate 7: Publish
      await expect(page.getByRole("button", { name: /Publish to blog/i })).toBeVisible({
        timeout: 15_000,
      });

      const waiveButton = page.getByRole("button", { name: "Waive for publish" });
      if (await waiveButton.isVisible().catch(() => false)) {
        await waiveButton.first().click();
        await page.waitForLoadState("load");
      }

      await page.getByRole("button", { name: /Publish to blog/i }).click();
      await page.waitForLoadState("load");

      await expect(page.getByRole("link", { name: /View public post/i })).toBeVisible({
        timeout: 30_000,
      });

      const publicHref =
        (await page.getByRole("link", { name: /View public post/i }).getAttribute("href")) ??
        `/blog/${new URL(page.url()).searchParams.get("blogSlug") ?? E2E_PUBLIC_SLUG}`;
      expect(publicHref).toMatch(/\/blog\//);

      await page.goto(publicHref);
      await expect(page.getByRole("heading", { name: E2E_IDEA_TITLE })).toBeVisible({
        timeout: 30_000,
      });
      await expect(page.getByText("Semi-auto keeps humans in the loop").first()).toBeVisible();
    } finally {
      if (ideaId) {
        await dbQuery("delete from blog_claims where blog_idea_id = $1", [ideaId]);
        await dbQuery("delete from blog_generation_jobs where blog_idea_id = $1", [ideaId]);
        const postRow = await dbQuery(
          "select published_blog_post_id from blog_ideas where id = $1",
          [ideaId],
        );
        const postId = postRow.rows[0]?.published_blog_post_id as string | undefined;
        if (postId) {
          await dbQuery("delete from blog_posts where id = $1", [postId]);
        }
        await dbQuery("delete from blog_ideas where id = $1", [ideaId]);
      }
      await dbQuery("delete from projects where id = $1", [projectId]);
      await cleanupAdmin(email);
    }
  });
});
