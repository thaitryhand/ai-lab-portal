import { expect, type Page } from "@playwright/test";
import pg from "pg";

const { Client } = pg;

export const e2ePort = process.env.E2E_PORT ?? "13100";
export const e2eOrigin = `http://127.0.0.1:${e2ePort}`;

export const e2eDatabaseUrl =
  process.env.AUTH_DATABASE_URL ??
  "postgresql://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal";

export function uniqueId(prefix: string, workerIndex: number) {
  return `${prefix}-${workerIndex}-${Date.now()}`;
}

export async function dbQuery(query: string, values: unknown[] = []) {
  const client = new Client({ connectionString: e2eDatabaseUrl });
  await client.connect();
  try {
    return await client.query(query, values);
  } finally {
    await client.end();
  }
}

export async function cleanupAdmin(email: string) {
  await dbQuery('delete from session where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from account where "userId" in (select id from "user" where email = $1)', [email]);
  await dbQuery('delete from "user" where email = $1', [email]);
}

export async function signInAdmin(
  context: { request: { post: (url: string, opts: object) => Promise<{ ok: () => boolean; status: () => number; text: () => Promise<string> }> } },
  email: string,
  password: string,
  retries = 5,
) {
  for (let attempt = 0; attempt < retries; attempt++) {
    const signUpResponse = await context.request.post("/api/auth/sign-up/email", {
      headers: { Origin: e2eOrigin },
      data: { email, password, name: "AI Lab Admin" },
    });
    const signInResponse = await context.request.post("/api/auth/sign-in/email", {
      headers: { Origin: e2eOrigin },
      data: { email, password },
    });

    if (signUpResponse.ok() && signInResponse.ok()) return;

    const body = await signUpResponse.text();
    if (signUpResponse.status() === 429 || signUpResponse.status() >= 500) {
      const delay = Math.min(1000 * 2 ** attempt, 15_000);
      await new Promise((r) => setTimeout(r, delay));
      continue;
    }
    expect(signUpResponse.ok(), body).toBeTruthy();
    expect(signInResponse.ok(), await signInResponse.text()).toBeTruthy();
  }
  throw new Error(`signInAdmin failed after ${retries} retries`);
}

/** Click an approve/generate button and wait for async Celery jobs to finish. */
export async function clickPipelineActionAndWait(page: Page, buttonName: RegExp, timeoutMs = 120_000) {
  const urlBefore = page.url();
  await page.getByRole("button", { name: buttonName }).click();

  await expect
    .poll(async () => page.url(), { timeout: timeoutMs })
    .not.toBe(urlBefore);

  // Poller clears taskId/opStatus=queued when the job finishes (avoids reload loop).
  await expect
    .poll(async () => {
      const params = new URL(page.url()).searchParams;
      return params.get("opStatus") !== "queued" && !params.get("taskId");
    }, { timeout: timeoutMs })
    .toBe(true);

  await page.waitForLoadState("load");
}

/** Wait for idea generation poller to land on idea detail (not /new). */
export async function waitForIdeaGenerationRedirect(page: Page, timeoutMs = 120_000) {
  await expect(page).toHaveURL(/\/admin\/blog-ideas\/(?!new)[^/?#]+/, { timeout: timeoutMs });
  await page.waitForLoadState("load");
}
