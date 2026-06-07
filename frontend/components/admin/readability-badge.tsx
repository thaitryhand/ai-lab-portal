"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";

/**
 * Computes a basic Flesch Reading Ease score client-side
 * and displays it alongside the draft content.
 */
function syllableCount(word: string): number {
  const w = word.toLowerCase().replace(/[^a-z]/g, "");
  if (!w) return 0;
  const vowels = "aeiouy";
  let count = 0;
  let prevVowel = false;
  for (const ch of w) {
    const isVowel = vowels.includes(ch);
    if (isVowel && !prevVowel) count++;
    prevVowel = isVowel;
  }
  return Math.max(1, count);
}

function analyzeReadability(text: string) {
  const sentences = text.split(/[.!?]+/).filter(Boolean);
  const words = text.match(/[a-zA-Z]+/g) ?? [];
  if (words.length === 0) return null;

  const avgSentenceLength = words.length / Math.max(sentences.length, 1);
  const totalSyllables = words.reduce((s, w) => s + syllableCount(w), 0);
  const flesch = Math.max(0, Math.min(100,
    206.835 - 1.015 * avgSentenceLength - 84.6 * (totalSyllables / words.length)
  ));

  let level: string;
  if (flesch >= 80) level = "Elementary";
  else if (flesch >= 60) level = "Middle School";
  else if (flesch >= 40) level = "High School";
  else level = "College";

  let label: string;
  if (flesch >= 80) label = "Very easy";
  else if (flesch >= 60) label = "Easy";
  else if (flesch >= 40) label = "Moderate";
  else if (flesch >= 20) label = "Difficult";
  else label = "Very difficult";

  return { flesch: Math.round(flesch), level, label };
}

export function ReadabilityBadge({ text }: { text: string }) {
  const score = useMemo(() => analyzeReadability(text), [text]);
  if (!score) return null;

  const color =
    score.flesch >= 60
      ? "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/30"
      : score.flesch >= 40
        ? "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/30"
        : "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950/30";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
        color,
      )}
      title={`${score.label} · ${score.level}`}
    >
      <span className="font-semibold">{score.flesch}</span>
      <span className="opacity-70">·</span>
      <span>{score.label}</span>
    </span>
  );
}
