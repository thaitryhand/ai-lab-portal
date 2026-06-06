import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  Check,
  ExternalLink,
  MessageSquare,
  ShieldAlert,
  ThumbsUp,
  X,
} from "lucide-react";

import { AdminEmptyState } from "@/components/admin/admin-empty-state";
import { AdminListActionForm } from "@/components/admin/admin-list-actions";
import { buttonVariants } from "@/components/ui/button-variants";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

import { approveCommentAction, rejectCommentAction } from "./actions";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminComment = {
  id: string;
  post_id: string;
  post_title: string;
  user_id: string;
  user_email: string | null;
  user_name: string | null;
  content: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
};

async function listComments() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/blog-comments`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (!response.ok)
    throw new Error(`Failed to fetch comments: ${response.status}`);
  return (await response.json()) as AdminComment[];
}

/** Strip HTML tags for safe plain-text display. */
function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, "").trim();
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatRelativeDate(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return formatDate(dateStr);
}

/* ── Status config ── */
const statusConfig = {
  pending: {
    label: "Pending",
    dot: "bg-amber-500",
    border: "border-amber-500/25",
    bg: "bg-amber-50 dark:bg-amber-950/20",
    text: "text-amber-700 dark:text-amber-300",
    icon: ShieldAlert,
  },
  approved: {
    label: "Approved",
    dot: "bg-emerald-500",
    border: "border-emerald-500/25",
    bg: "bg-emerald-50 dark:bg-emerald-950/20",
    text: "text-emerald-700 dark:text-emerald-300",
    icon: ThumbsUp,
  },
  rejected: {
    label: "Rejected",
    dot: "bg-red-500",
    border: "border-red-500/25",
    bg: "bg-red-50 dark:bg-red-950/20",
    text: "text-red-700 dark:text-red-300",
    icon: X,
  },
};

function StatusBadge({ status }: { status: AdminComment["status"] }) {
  const cfg = statusConfig[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium",
        cfg.border,
        cfg.bg,
        cfg.text,
      )}
    >
      <cfg.icon className="size-3" aria-hidden />
      {cfg.label}
    </span>
  );
}

/** Get a user's initial for the avatar */
function getInitial(name: string | null, email: string | null): string {
  if (name) return name.charAt(0).toUpperCase();
  if (email) return email.charAt(0).toUpperCase();
  return "?";
}

export default async function AdminBlogCommentsPage() {
  const comments = await listComments();

  const counts = {
    total: comments.length,
    pending: comments.filter((c) => c.status === "pending").length,
    approved: comments.filter((c) => c.status === "approved").length,
    rejected: comments.filter((c) => c.status === "rejected").length,
  };

  const summaryCards = [
    {
      label: "Total",
      value: counts.total,
      color: "bg-muted-foreground",
      text: "bg-card",
    },
    {
      label: "Pending",
      value: counts.pending,
      color: "bg-amber-500",
      text: "bg-amber-50 dark:bg-amber-950/20 text-amber-700 dark:text-amber-300",
    },
    {
      label: "Approved",
      value: counts.approved,
      color: "bg-emerald-500",
      text: "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300",
    },
    {
      label: "Rejected",
      value: counts.rejected,
      color: "bg-red-500",
      text: "bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-300",
    },
  ];

  return (
    <div className={adminPageStackClass}>
      <AdminListToolbar
        description="Comments on blog posts from registered users. Approve or reject pending items."
        eyebrow="Blog"
        title="Comments"
      />

      {/* ── Summary strip ── */}
      {comments.length > 0 && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {summaryCards.map((card) => (
            <div
              key={card.label}
              className={cn(
                "flex items-center gap-3 rounded-[var(--radius-admin-md)] border border-border/60 px-4 py-3 shadow-[0_1px_2px_rgba(0,0,0,0.02)]",
                card.text,
              )}
            >
              <span
                className={cn(
                  "flex size-8 items-center justify-center rounded-[var(--radius-admin-sm)] bg-white text-xs font-semibold tabular-nums shadow-[0_1px_2px_rgba(0,0,0,0.04)] ring-1 ring-border/20 dark:bg-card",
                )}
              >
                {card.value}
              </span>
              <span className="text-xs font-medium">{card.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Comments list ── */}
      {comments.length === 0 ? (
        <AdminEmptyState
          description="No comments yet. Comments will appear once users start engaging with blog posts."
          icon={<MessageSquare className="size-6" aria-hidden />}
          title="No comments"
        />
      ) : (
        <div className="rounded-[var(--radius-admin-md)] border border-border/60 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          {comments.map((comment) => {
            const initial = getInitial(comment.user_name, comment.user_email);

            return (
              <div
                key={comment.id}
                className={cn(
                  "group border-b border-border/40 px-5 py-4 transition-colors last:border-b-0 hover:bg-muted/10",
                  comment.status === "pending" &&
                    "border-l-2 border-l-amber-400/60",
                )}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  {/* Left: avatar + info */}
                  <div className="flex min-w-0 flex-1 gap-3">
                    {/* Avatar */}
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground shadow-[0_1px_2px_rgba(0,0,0,0.06)]">
                      {initial}
                    </span>

                    <div className="min-w-0 flex-1 space-y-1.5">
                      {/* User row */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-foreground">
                          {comment.user_name || "Anonymous"}
                        </span>
                        {comment.user_email && (
                          <span className="text-xs text-muted-foreground">
                            {comment.user_email}
                          </span>
                        )}
                        <span className="text-[10px] text-muted-foreground/60">
                          {formatRelativeDate(comment.created_at)}
                        </span>
                      </div>

                      {/* Content — stripped of HTML tags */}
                      <p className="line-clamp-3 text-sm leading-relaxed text-foreground/85">
                        {stripHtml(comment.content)}
                      </p>

                      {/* Post reference — link to admin editor (slugs aren't available in comment data) */}
                      <a
                        href={`/admin/blog/${comment.post_id}/edit`}
                        className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors hover:text-brand"
                      >
                        <ExternalLink className="size-3" aria-hidden />
                        View post in editor
                      </a>
                    </div>
                  </div>

                  {/* Right: status + actions */}
                  <div className="flex shrink-0 flex-col items-end gap-2 sm:min-w-32">
                    <StatusBadge status={comment.status} />

                    <div className="flex flex-wrap items-center gap-1.5 opacity-60 transition-opacity group-hover:opacity-100 lg:opacity-40">
                      {comment.status === "pending" && (
                        <>
                          <AdminListActionForm action={approveCommentAction}>
                            <input
                              name="commentId"
                              type="hidden"
                              value={comment.id}
                            />
                            <button
                              className={buttonVariants({
                                variant: "brand",
                                size: "xs",
                              })}
                              type="submit"
                            >
                              <Check className="size-3" aria-hidden />
                              Approve
                            </button>
                          </AdminListActionForm>
                          <AdminListActionForm action={rejectCommentAction}>
                            <input
                              name="commentId"
                              type="hidden"
                              value={comment.id}
                            />
                            <button
                              className={buttonVariants({
                                variant: "outline",
                                size: "xs",
                              })}
                              type="submit"
                            >
                              <X className="size-3" aria-hidden />
                              Reject
                            </button>
                          </AdminListActionForm>
                        </>
                      )}
                      {comment.status === "approved" && (
                        <AdminListActionForm action={rejectCommentAction}>
                          <input
                            name="commentId"
                            type="hidden"
                            value={comment.id}
                          />
                          <button
                            className={buttonVariants({
                              variant: "ghost",
                              size: "xs",
                            })}
                            type="submit"
                          >
                            <X className="size-3" aria-hidden />
                            Remove
                          </button>
                        </AdminListActionForm>
                      )}
                      {comment.status === "rejected" && (
                        <AdminListActionForm action={approveCommentAction}>
                          <input
                            name="commentId"
                            type="hidden"
                            value={comment.id}
                          />
                          <button
                            className={buttonVariants({
                              variant: "ghost",
                              size: "xs",
                            })}
                            type="submit"
                          >
                            <Check className="size-3" aria-hidden />
                            Restore
                          </button>
                        </AdminListActionForm>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
