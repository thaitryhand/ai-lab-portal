import { headers } from "next/headers";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { CalendarClientShell } from "@/components/admin/content-calendar/calendar-client-shell";
import type { CalendarData } from "@/components/admin/content-calendar/calendar-client-shell";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

async function getCalendarData(): Promise<CalendarData> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return { published: [], pipeline: [], scheduled: [], month_counts: {} };
  }

  const response = await fetch(
    `${backendBaseUrl}/admin/content-calendar/posts`,
    {
      headers: createAdminBoundaryHeaders({
        user: { id: session.user.id, email: session.user.email },
      }),
      cache: "no-store",
    },
  );

  if (!response.ok) return { published: [], pipeline: [], scheduled: [], month_counts: {} };
  return response.json();
}

export default async function ContentCalendarPage() {
  const data = await getCalendarData();

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <AdminPageHeader
        title="Content Calendar"
        description="Blog post schedule and pipeline overview"
        actions={<AdminBackLink href="/admin">Back to dashboard</AdminBackLink>}
      />
      <CalendarClientShell initialData={data} />
    </div>
  );
}
