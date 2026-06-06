import { cn } from "@/lib/utils";

export function AdminSkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse rounded-[var(--radius-admin-md)] border border-border/60 bg-card p-5", className)}>
      <div className="mb-3 h-4 w-2/5 rounded bg-muted/40" />
      <div className="mb-2 h-3 w-4/5 rounded bg-muted/30" />
      <div className="h-3 w-3/5 rounded bg-muted/30" />
    </div>
  );
}

export function AdminSkeletonStatCard() {
  return (
    <div className="animate-pulse rounded-[var(--radius-admin-md)] border border-border/60 bg-card p-4">
      <div className="mb-2 h-3 w-1/3 rounded bg-muted/30" />
      <div className="mb-1 h-7 w-1/4 rounded bg-muted/40" />
      <div className="h-2.5 w-2/5 rounded bg-muted/20" />
    </div>
  );
}

export function AdminSkeletonListRow() {
  return (
    <div className="animate-pulse border-b border-border/50 px-5 py-4">
      <div className="mb-2 h-4 w-3/5 rounded bg-muted/40" />
      <div className="h-3 w-2/5 rounded bg-muted/30" />
    </div>
  );
}
