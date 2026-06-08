"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

import { publicEase } from "@/components/public/public-motion";

const stats = [
  { value: "98+", label: "Stories delivered" },
  { value: "306", label: "Backend tests passing" },
  { value: "7", label: "Pipeline stages" },
  { value: "100%", label: "Human review gates" },
];

export interface TourStatsData {
  blogPosts: number;
  showcases: number;
  projects: number;
  newsItems: number;
}

const fallbackStats: TourStatsData = {
  blogPosts: 6,
  showcases: 3,
  projects: 2,
  newsItems: 12,
};

export function TourStats({ data }: { data?: TourStatsData }) {
  const stats = data ?? fallbackStats;
  const statCards = [
    { value: stats.blogPosts.toString(), label: "Blog posts" },
    { value: stats.showcases.toString(), label: "Showcases" },
    { value: stats.projects.toString(), label: "Projects" },
    { value: stats.newsItems.toString(), label: "AI news" },
  ];
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section ref={ref} className="border-y border-[var(--color-book-text-gray)]/10 bg-[var(--color-vellum-background)] py-20">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, ease: publicEase }}
        >
          {statCards.map((stat, i) => (
            <motion.div
              key={stat.label}
              className="text-center"
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.1 * i, ease: publicEase }}
            >
              <p className="font-display text-[clamp(2.5rem,5vw,4rem)] leading-none tracking-[-0.03em] text-[var(--color-story-green)]">
                {stat.value}
              </p>
              <p className="mt-2 text-sm text-[var(--color-muted-text-gray)]">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
