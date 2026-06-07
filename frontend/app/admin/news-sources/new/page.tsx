import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { ButtonLink } from "@/components/ui/button-link";
import { adminPageStackClass, adminPageTitleClass, adminPanelClass } from "@/components/admin/admin-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";
import { auth } from "@/lib/auth/server";
import { createNewsSourceAction } from "../actions";

export default async function NewNewsSourcePage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  return (
      <div className={adminPageStackClass}>
        <AdminBackLink href="/admin/news-sources">Back to sources</AdminBackLink>
        <h1 className={adminPageTitleClass}>Add news source</h1>
        <form action={createNewsSourceAction} className={cn(adminPanelClass, "grid max-w-xl gap-4 p-6")}>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Name</span>
            <input name="name" required className="rounded-md border border-border bg-background px-3 py-2" />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Type</span>
            <select name="sourceType" className="rounded-md border border-border bg-background px-3 py-2">
              <option value="rss">RSS Feed</option>
              <option value="github">GitHub Releases</option>
              <option value="hackernews">Hacker News (Firebase API)</option>
              <option value="website">Website (Coming soon)</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">URL or identifier</span>
            <input name="url" required className="rounded-md border border-border bg-background px-3 py-2" />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Description</span>
            <textarea name="description" rows={2} className="rounded-md border border-border bg-background px-3 py-2" />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Priority</span>
            <select name="priority" className="rounded-md border border-border bg-background px-3 py-2">
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Crawl every (minutes)</span>
            <input name="crawlFrequency" type="number" defaultValue={360} min={15} className="rounded-md border border-border bg-background px-3 py-2" />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Credibility (0–1)</span>
            <input name="credibility" type="number" step="0.05" min={0} max={1} defaultValue={0.7} className="rounded-md border border-border bg-background px-3 py-2" />
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input name="isEnabled" type="checkbox" defaultChecked />
            Enabled
          </label>
          <div className="flex gap-2">
            <button className={cn(buttonVariants())} type="submit">Save source</button>
            <ButtonLink href="/admin/news-sources" variant="outline">Cancel</ButtonLink>
          </div>
        </form>
      </div>
  );
}
