import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { BlogEditor } from "@/components/admin/blog-editor";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { publishAction, saveDraftAction } from "@/app/admin/blog/editor/actions";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "New blog post | AI Lab Portal",
  description: "Create a new blog post for the AI Lab.",
};

export default async function BlogNewPage() {
  const session = await auth.api.getSession({ headers: await headers() });

  if (!session) {
    redirect("/admin/login?redirect=/blog/new");
  }

  return (
    <PublicPageShell>
      <section className={cn(publicMainWidthClass, "flex flex-col gap-8 py-10 sm:py-14")}>
        <BlogEditor publishAction={publishAction} saveDraftAction={saveDraftAction} />
      </section>
    </PublicPageShell>
  );
}
