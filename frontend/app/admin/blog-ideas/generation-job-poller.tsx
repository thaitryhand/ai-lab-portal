"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";

import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";
import { pollGenerationJobAction } from "./actions";

type Props = {
  ideaId: string;
  taskId?: string;
  opStage?: string;
  opStatus?: string;
};

type BannerState = "polling" | "completed" | "failed" | "idle";

const stageLabels: Record<string, string> = {
  idea: "Generating blog idea",
  outline: "Generating outline",
  draft: "Writing draft",
  "technical-review": "Running technical review",
  marketing: "Generating marketing metadata",
  publish: "Publishing to blog",
};

export function GenerationJobPoller({ taskId, opStage, opStatus }: Props) {
  const polling = useRef(false);
  const [banner, setBanner] = useState<BannerState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [attempt, setAttempt] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [stageName, setStageName] = useState("");

  // Elapsed timer
  useEffect(() => {
    if (banner !== "polling") return;
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(interval);
  }, [banner]);

  const startPolling = useCallback(() => {
    if (!taskId || polling.current) return;
    polling.current = true;
    setBanner("polling");
    setElapsed(0);
    setAttempt(1);
    setErrorMsg(null);
    setStageName(stageLabels[opStage ?? ""] ?? "Processing");

    const abort = new AbortController();
    const { signal } = abort;

    const poll = async () => {
      for (let attemptNum = 1; attemptNum <= 60 && !signal.aborted; attemptNum++) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        if (signal.aborted) return;
        setAttempt(attemptNum);
        const job = await pollGenerationJobAction(taskId);
        if (signal.aborted) return;

        if (job.status === "completed") {
          setBanner("completed");
          await new Promise((resolve) => setTimeout(resolve, 1500));
          if (!signal.aborted) window.location.reload();
          return;
        }
        if (job.status === "failed") {
          setBanner("failed");
          setErrorMsg(job.error_message ?? "Generation failed in the worker.");
          polling.current = false;
          return;
        }
      }
      // Timeout after 60 attempts
      setBanner("failed");
      setErrorMsg("Generation timed out after 2 minutes.");
      polling.current = false;
    };

    void poll();
    return () => abort.abort();
  }, [taskId, opStage]);

  // Start on mount if queued
  useEffect(() => {
    if (opStatus === "queued" && taskId) {
      startPolling();
    }
  }, [opStatus, taskId, startPolling]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <AnimatePresence mode="wait">
      {banner === "polling" && (
        <motion.div
          key="polling"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.3 }}
          className="mb-6 rounded-xl border border-sky-200 bg-sky-50/90 p-4 dark:border-sky-900 dark:bg-sky-950/20"
        >
          <div className="flex items-start gap-3">
            <Loader2 className="mt-0.5 size-5 animate-spin text-sky-600 dark:text-sky-400" aria-hidden />
            <div className="grid min-w-0 flex-1 gap-1">
              <p className="text-sm font-semibold text-sky-900 dark:text-sky-200">
                {stageName}
              </p>
              <p className="truncate text-xs text-sky-700/70 dark:text-sky-300/70">
                Running · {formatTime(elapsed)} · Attempt {attempt}
              </p>
              {/* Progress bar */}
              <div className="mt-2 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-sky-200/50 dark:bg-sky-800/30">
                <motion.div
                  className="h-full rounded-full bg-sky-500 dark:bg-sky-400"
                  animate={{ x: ["-100%", "100%"] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                  style={{ width: "40%" }}
                />
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {banner === "completed" && (
        <motion.div
          key="completed"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.3 }}
          className="mb-6 rounded-xl border border-emerald-200 bg-emerald-50/90 p-4 dark:border-emerald-900 dark:bg-emerald-950/20"
        >
          <div className="flex items-center gap-3">
            <CheckCircle2 className="size-5 text-emerald-600 dark:text-emerald-400" aria-hidden />
            <p className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">
              {stageName} completed! Reloading…
            </p>
          </div>
        </motion.div>
      )}

      {banner === "failed" && (
        <motion.div
          key="failed"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.3 }}
          className="mb-6 rounded-xl border border-red-200 bg-red-50/90 p-4 dark:border-red-900 dark:bg-red-950/20"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 size-5 text-red-600 dark:text-red-400" aria-hidden />
            <div className="grid min-w-0 flex-1 gap-1">
              <p className="text-sm font-semibold text-red-900 dark:text-red-200">
                {stageName} failed
              </p>
              {errorMsg && (
                <p className="text-xs leading-relaxed text-red-700/80 dark:text-red-300/80">
                  {errorMsg}
                </p>
              )}
              <button
                onClick={startPolling}
                className={cn(buttonVariants({ variant: "secondary", size: "sm" }), "mt-2 w-fit gap-1.5")}
              >
                <RefreshCw className="size-3.5" aria-hidden />
                Retry
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
