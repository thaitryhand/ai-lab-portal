"use client";

import { motion } from "framer-motion";
import {
  CheckCircle2,
  ExternalLink,
  Loader2,
  Play,
  SkipForward,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import { adminPageStackClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

/* ── Types ── */

interface ProjectOption {
  id: string;
  slug: string;
  title: string;
  description: string;
  published_at: string;
}

interface PipelineStep {
  label: string;
  status: "pending" | "running" | "done" | "skipped" | "failed";
  detail?: string | null;
}

interface PipelineResult {
  run_id: string;
  steps: PipelineStep[];
  idea_id?: string | null;
  blog_slug?: string | null;
  blog_post_id?: string | null;
  admin_url?: string | null;
  public_url?: string | null;
  overall_status: "completed" | "failed";
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:18000";

/* ── Step icon ── */

function StepIcon({ status }: { status: string }) {
  switch (status) {
    case "running":
      return <Loader2 className="size-4 animate-spin text-brand" />;
    case "done":
      return <CheckCircle2 className="size-4 text-emerald-500" />;
    case "skipped":
      return <SkipForward className="size-4 text-amber-500" />;
    case "failed":
      return <XCircle className="size-4 text-red-500" />;
    default:
      return <span className="size-4 rounded-full border-2 border-border/40" />;
  }
}

/* ── Status badge ── */

function StatusBadge({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
        <CheckCircle2 className="size-3.5" />
        Completed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700 dark:bg-red-950/30 dark:text-red-400">
      <XCircle className="size-3.5" />
      Failed
    </span>
  );
}

/* ── Page ── */

export default function PipelineRunnerPage() {
  const [projects, setProjects] = useState<ProjectOption[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);

  // Fetch published projects on mount
  useEffect(() => {
    fetch(`${BACKEND_URL}/public/projects`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: ProjectOption[]) => {
        // The public endpoint returns ProjectSummary which doesn't have `id`
        // Map slug to id fallback
        const mapped = data.map((p) => ({
          ...p,
          id: p.id ?? p.slug,
        }));
        setProjects(mapped);
        if (mapped.length > 0) {
          setSelectedProjectId(mapped[0].id);
        }
      })
      .catch(() => {
        // Fallback: use the default project
        setProjects([]);
      })
      .finally(() => setLoadingProjects(false));
  }, []);

  const handleRun = async () => {
    setRunning(true);
    setResult(null);

    try {
      const res = await fetch("/api/admin/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: selectedProjectId || undefined,
        }),
      });

      if (!res.ok) {
        const errText = await res.text();
        setResult({
          run_id: "error",
          steps: [
            { label: "Request failed", status: "failed", detail: `HTTP ${res.status}: ${errText}` },
          ],
          overall_status: "failed",
        });
        return;
      }

      const data: PipelineResult = await res.json();
      setResult(data);
    } catch (err) {
      setResult({
        run_id: "error",
        steps: [{ label: "Network error", status: "failed", detail: String(err) }],
        overall_status: "failed",
      });
    } finally {
      setRunning(false);
    }
  };

  return (
    <motion.div
      className={cn("space-y-6", adminPageStackClass)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Pipeline Runner</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Run the full seed pipeline: pick a project context, generate an idea, auto-approve
            all gates, and publish to the blog.
          </p>
        </div>
      </div>

      {/* Project picker + Run button */}
      <div className="flex items-end gap-4">
        <div className="flex-1">
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Source project
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            disabled={running || loadingProjects}
            className="w-full rounded-lg border border-border/60 bg-card px-3 py-2.5 text-sm text-foreground shadow-sm transition-colors focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand/30 disabled:opacity-50"
          >
            {loadingProjects ? (
              <option value="">Loading projects…</option>
            ) : projects.length === 0 ? (
              <option value="project_runner_seed">Default: AI Lab Portal</option>
            ) : (
              projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} ({p.slug})
                </option>
              ))
            )}
          </select>
        </div>

        <button
          onClick={handleRun}
          disabled={running}
          className={cn(
            "inline-flex h-[42px] items-center gap-2 rounded-lg px-6 text-sm font-semibold transition-all",
            running
              ? "bg-muted text-muted-foreground cursor-not-allowed"
              : "bg-brand text-white hover:bg-brand/90 hover:scale-[1.02] shadow-sm",
          )}
        >
          {running ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <Play className="size-4" />
              Run Pipeline
            </>
          )}
        </button>
      </div>

      {/* Requirements notice */}
      <div className="rounded-xl border border-amber-200/50 bg-amber-50/50 px-4 py-3 text-xs text-amber-700 dark:border-amber-800/30 dark:bg-amber-950/10 dark:text-amber-400">
        <p className="font-medium mb-1">Requirements</p>
        <p>
          Backend must be running with <code className="text-[10px] font-mono bg-amber-100/50 dark:bg-amber-900/30 px-1 rounded">AI_LAB_LLM_E2E_FAKE=true</code> for inline generation jobs with deterministic responses.
        </p>
      </div>

      {/* Results */}
      {result && (
        <motion.div
          className="space-y-4"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Overall status */}
          <div className="flex items-center gap-3">
            <StatusBadge status={result.overall_status} />
            <span className="text-xs text-muted-foreground">
              Run ID: <code className="font-mono">{result.run_id}</code>
            </span>
          </div>

          {/* Step listing */}
          <div className="rounded-xl border border-border/70 bg-card divide-y divide-border/30">
            {result.steps.map((step, i) => (
              <motion.div
                key={`${step.label}-${i}`}
                className="flex items-center gap-3 px-5 py-3 text-sm"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04, duration: 0.2 }}
              >
                <StepIcon status={step.status} />
                <span
                  className={cn(
                    "flex-1",
                    step.status === "failed" && "text-red-600 dark:text-red-400 font-medium",
                    step.status === "running" && "text-foreground font-medium",
                    step.status === "done" && "text-foreground",
                    step.status === "skipped" && "text-muted-foreground",
                    step.status === "pending" && "text-muted-foreground/60",
                  )}
                >
                  {step.label}
                </span>
                {step.detail && (
                  <span className="text-xs text-muted-foreground font-mono max-w-[300px] truncate">
                    {step.detail}
                  </span>
                )}
              </motion.div>
            ))}
          </div>

          {/* Result links */}
          {result.overall_status === "completed" && (
            <motion.div
              className="rounded-xl border border-emerald-200/50 bg-emerald-50/50 p-4 dark:border-emerald-800/30 dark:bg-emerald-950/10"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.3 }}
            >
              <h3 className="text-sm font-semibold text-emerald-800 dark:text-emerald-300 mb-3">
                Pipeline Complete
              </h3>
              <div className="space-y-2">
                {result.admin_url && (
                  <a
                    href={result.admin_url}
                    className="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400 hover:underline"
                  >
                    <ExternalLink className="size-3.5" />
                    <span>Admin: {result.admin_url}</span>
                  </a>
                )}
                {result.public_url && (
                  <a
                    href={result.public_url}
                    className="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400 hover:underline"
                  >
                    <ExternalLink className="size-3.5" />
                    <span>Public: {result.public_url}</span>
                  </a>
                )}
                {result.idea_id && (
                  <p className="text-xs text-emerald-600 dark:text-emerald-500">
                    Idea ID: {result.idea_id}
                    {result.blog_post_id && <> · Post ID: {result.blog_post_id}</>}
                    {result.blog_slug && <> · Slug: {result.blog_slug}</>}
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Empty state */}
      {!result && !running && (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border/40 py-20 text-center">
          <Play className="size-10 text-muted-foreground/30 mb-3" />
          <p className="text-sm font-medium text-muted-foreground">
            Select a project and run the pipeline
          </p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            The pipeline will: seed project → generate idea → auto-approve all gates → publish to blog.
          </p>
        </div>
      )}
    </motion.div>
  );
}
