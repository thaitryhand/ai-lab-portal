"use client";

import { useEffect, useState } from "react";
import { Activity, Cpu, Database, HardDrive, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

type HealthData = {
  service: string;
  status: string;
  environment: string;
  database?: string;
  redis?: string;
  celery_workers?: string[];
  celery_worker_count?: number;
  celery_status?: string;
  celery_queues?: Record<string, number>;
};

const statusConfig = {
  ok: { color: "text-emerald-500", bg: "bg-emerald-500/10", ring: "ring-emerald-500/20", label: "Healthy" },
  degraded: { color: "text-amber-500", bg: "bg-amber-500/10", ring: "ring-amber-500/20", label: "Degraded" },
  error: { color: "text-red-500", bg: "bg-red-500/10", ring: "ring-red-500/20", label: "Error" },
  unreachable: { color: "text-red-600", bg: "bg-red-500/10", ring: "ring-red-500/20", label: "Unreachable" },
} as const;

function getStatusInfo(status: string) {
  return statusConfig[status as keyof typeof statusConfig] ?? statusConfig.error;
}

function StatusDot({ status }: { status: string }) {
  const info = getStatusInfo(status);
  return (
    <span
      className={cn(
        "inline-block size-2 rounded-full ring-1",
        info.color.replace("text-", "bg-"),
        info.ring,
      )}
    />
  );
}

export function AdminHealthWidget() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchHealth() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/health");
      if (!res.ok) {
        setHealth(null);
        setError(`HTTP ${res.status}`);
        return;
      }
      const data: HealthData = await res.json();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchHealth();
    const interval = setInterval(fetchHealth, 30_000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const overallStatus = health?.status ?? (error ? "unreachable" : "error");
  const statusInfo = getStatusInfo(overallStatus);

  return (
    <section
      className={cn(
        "rounded-[var(--radius-admin-md)] border border-border/60 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]",
        overallStatus === "ok" && "border-emerald-500/20",
        overallStatus === "degraded" && "border-amber-500/20",
        overallStatus === "unreachable" && "border-red-500/20",
      )}
    >
      <div className="flex items-center justify-between border-b border-border/50 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <Activity className="size-4 text-muted-foreground" aria-hidden />
          <h2 className="text-sm font-semibold text-foreground">System health</h2>
        </div>
        <button
          type="button"
          onClick={fetchHealth}
          disabled={loading}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw className={cn("size-3", loading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {loading && !health ? (
        <div className="flex items-center justify-center px-5 py-10">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground" />
        </div>
      ) : (
        <div className="space-y-3 px-5 py-4">
          {/* Overall status */}
          <div className="flex items-center justify-between rounded-lg bg-muted/20 px-3.5 py-2.5">
            <span className="text-sm font-medium text-foreground">Overall</span>
            <span className={cn("flex items-center gap-1.5 text-sm font-medium", statusInfo.color)}>
              <StatusDot status={overallStatus} />
              {statusInfo.label}
            </span>
          </div>

          {/* Component details */}
          {health && (
            <div className="space-y-1">
              <HealthRow label="API" ok icon={<Cpu className="size-3.5" />} />
              <HealthRow
                label="Database"
                ok={health.database === "connected"}
                detail={health.database}
                icon={<Database className="size-3.5" />}
              />
              <HealthRow
                label="Redis"
                ok={health.redis === "connected"}
                detail={health.redis}
                icon={<HardDrive className="size-3.5" />}
              />
              <HealthRow
                label="Celery workers"
                ok={(health.celery_worker_count ?? 0) > 0}
                detail={
                  health.celery_worker_count != null
                    ? `${health.celery_worker_count} worker${health.celery_worker_count !== 1 ? "s" : ""}`
                    : health.celery_status
                }
                icon={<Cpu className="size-3.5" />}
              />
            </div>
          )}

          {/* Error state */}
          {error && !health && (
            <div className="rounded-lg bg-red-500/10 px-3.5 py-2.5">
              <p className="text-xs text-red-600">Backend unreachable: {error}</p>
            </div>
          )}

          {/* Queue info */}
          {health?.celery_queues && Object.keys(health.celery_queues).length > 0 && (
            <div className="border-t border-border/30 pt-3">
              <p className="mb-1.5 text-xs font-medium text-muted-foreground">Queue depths</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(health.celery_queues).map(([queue, depth]) => (
                  <span
                    key={queue}
                    className="inline-flex items-center gap-1.5 rounded-md border border-border/50 bg-muted/20 px-2.5 py-1 text-xs"
                  >
                    <span className="text-muted-foreground">{queue}</span>
                    <span
                      className={cn(
                        "font-medium tabular-nums",
                        (depth as number) > 0 ? "text-amber-500" : "text-emerald-500",
                      )}
                    >
                      {(depth as number) > 0 ? `${depth} pending` : "0"}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function HealthRow({
  label,
  ok,
  detail,
  icon,
}: {
  label: string;
  ok: boolean;
  detail?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between rounded-md px-3 py-2 text-sm transition-colors hover:bg-muted/10">
      <div className="flex items-center gap-2.5">
        <span className="text-muted-foreground [&>svg]:size-3.5">{icon}</span>
        <span className="text-foreground">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {detail && detail !== "connected" && detail !== "not_available" && ok === false && (
          <span className="text-xs text-muted-foreground/70">{detail}</span>
        )}
        <StatusDot status={ok ? "ok" : "error"} />
      </div>
    </div>
  );
}
