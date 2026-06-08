"use client";

import { motion } from "framer-motion";
import {
  BookOpen,
  Briefcase,
  CheckCircle2,
  Eye,
  FlaskConical,
  Loader2,
  Newspaper,
  Sparkles,
} from "lucide-react";
import { useCallback, useState } from "react";

const contentTypes = [
  {
    id: "blog" as const,
    label: "Blog Posts",
    icon: BookOpen,
    description: "6 editorial posts about AI agents, MCP, HITL, observability dashboards",
    color: "text-emerald-600",
    bgColor: "bg-emerald-50 dark:bg-emerald-950/20",
    borderColor: "border-emerald-200/50 dark:border-emerald-800/30",
  },
  {
    id: "showcases" as const,
    label: "Showcases",
    icon: FlaskConical,
    description: "5 client case studies: gaming, HR tech, document processing, support, code review",
    color: "text-sky-600",
    bgColor: "bg-sky-50 dark:bg-sky-950/20",
    borderColor: "border-sky-200/50 dark:border-sky-800/30",
  },
  {
    id: "projects" as const,
    label: "Projects",
    icon: Briefcase,
    description: "4 published projects for AI pipeline idea generation",
    color: "text-purple-600",
    bgColor: "bg-purple-50 dark:bg-purple-950/20",
    borderColor: "border-purple-200/50 dark:border-purple-800/30",
  },
  {
    id: "news_items" as const,
    label: "AI News",
    icon: Newspaper,
    description: "5 ready-to-publish AI news items: GPT-5, Claude 4, MCP adoption, and more",
    color: "text-rose-600",
    bgColor: "bg-rose-50 dark:bg-rose-950/20",
    borderColor: "border-rose-200/50 dark:border-rose-800/30",
  },
];

type SeedState = "idle" | "seeding" | "done" | "error";

export default function SeedStudioPage() {
  const [seedState, setSeedState] = useState<SeedState>("idle");
  const [result, setResult] = useState<{
    blog_posts: number;
    showcases: number;
    projects: number;
    tags: number;
    news_items: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSeed = useCallback(async () => {
    setSeedState("seeding");
    setError(null);
    try {
      const res = await fetch("/admin/seed/all", { method: "POST" });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text.slice(0, 200));
      }
      const data = await res.json();
      setResult(data);
      setSeedState("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Seed failed");
      setSeedState("error");
    }
  }, []);

  const totalSeeded = result
    ? result.blog_posts + result.showcases + result.projects + result.tags + result.news_items
    : 0;

  const seededCount: Record<string, number> = {
    blog: result?.blog_posts ?? 0,
    showcases: result?.showcases ?? 0,
    projects: result?.projects ?? 0,
    news_items: result?.news_items ?? 0,
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
            <Sparkles className="size-5" />
          </span>
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-foreground">
              Seed Studio
            </h1>
            <p className="text-sm text-muted-foreground">
              Populate the platform with demo content for the AI Lab Tour
            </p>
          </div>
        </div>
      </motion.div>

      {/* Content type cards */}
      <motion.div
        className="mt-10 grid gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15, duration: 0.5 }}
      >
        {contentTypes.map((type, i) => {
          const Icon = type.icon;
          return (
            <motion.div
              key={type.id}
              className={`rounded-xl border ${type.borderColor} ${type.bgColor} p-5 transition-all duration-300`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.06, duration: 0.4 }}
            >
              <div className="flex items-start gap-4">
                <span
                  className={`flex size-10 shrink-0 items-center justify-center rounded-lg border ${type.borderColor} bg-white ${type.color}`}
                >
                  <Icon className="size-5" />
                </span>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-semibold text-foreground">
                    {type.label}
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {type.description}
                  </p>
                </div>
                {seedState === "done" && result && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                    <CheckCircle2 className="size-3" />
                    {seededCount[type.id]} seeded
                  </span>
                )}
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Seed button */}
      <motion.div
        className="mt-10"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.4 }}
      >
        <button
          onClick={handleSeed}
          disabled={seedState === "seeding"}
          className="inline-flex items-center gap-2.5 rounded-full bg-foreground px-8 py-3.5 text-sm font-semibold text-background transition-all duration-300 hover:bg-brand hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {seedState === "seeding" ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Seeding content...
            </>
          ) : (
            <>
              <Sparkles className="size-4" />
              {seedState === "done" ? "Seed again (idempotent)" : "Seed all content"}
            </>
          )}
        </button>

        {/* Success message */}
        {seedState === "done" && result && (
          <motion.div
            className="mt-6 rounded-xl border border-emerald-200/50 bg-emerald-50/50 p-5 dark:border-emerald-800/30 dark:bg-emerald-950/10"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center gap-2 text-sm font-medium text-emerald-700 dark:text-emerald-400">
              <CheckCircle2 className="size-4" />
              Seeded {totalSeeded} items
            </div>
            <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
              {result.blog_posts > 0 && <li>• {result.blog_posts} blog posts added</li>}
              {result.showcases > 0 && <li>• {result.showcases} showcases added</li>}
              {result.projects > 0 && <li>• {result.projects} projects added</li>}
              {result.tags > 0 && <li>• {result.tags} tags added</li>}
              {result.news_items > 0 && <li>• {result.news_items} news items added</li>}
              {totalSeeded === 0 && <li>All content already exists (seeding is idempotent)</li>}
            </ul>
          </motion.div>
        )}

        {/* Error message */}
        {seedState === "error" && error && (
          <motion.div
            className="mt-6 rounded-xl border border-red-200/50 bg-red-50/50 p-5 dark:border-red-800/30 dark:bg-red-950/10"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <p className="text-sm font-medium text-red-600 dark:text-red-400">
              Failed to seed content
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{error}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Make sure the backend is running on port 18000 with a valid database connection.
            </p>
          </motion.div>
        )}
      </motion.div>

      {/* Note */}
      <motion.div
        className="mt-10 border-t border-border/60 pt-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.4 }}
      >
        <div className="flex items-start gap-3 rounded-xl border border-dashed border-border/60 bg-muted/20 p-4">
          <Eye className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div className="text-xs leading-relaxed text-muted-foreground">
            <p className="font-medium text-foreground">After seeding</p>
            <p className="mt-1">
              Seeded content appears automatically on the{" "}
              <a href="/tour" className="text-brand underline underline-offset-2 hover:no-underline">
                AI Lab Tour
              </a>{" "}
              page, public blog, showcases, and projects. The seed is <strong>idempotent</strong> —
              running it multiple times will not create duplicates.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
