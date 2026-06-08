"use client";

import { motion, useInView } from "framer-motion";
import Link from "next/link";
import { useRef } from "react";

import { publicEase, publicStaggerContainer, publicStaggerItem } from "@/components/public/public-motion";

export interface TourExampleItem {
  title: string;
  category: string;
  href: string;
  excerpt: string;
}

const fallbackExamples: TourExampleItem[] = [
  {
    title: "How we built a semi-auto AI blog pipeline",
    category: "Engineering",
    href: "/blog/e2e-golden-path-blog-idea",
    excerpt: "From project context to published post — seven stages, zero manual content writing.",
  },
  {
    title: "Scaling game analytics with embeddings",
    category: "Case Study",
    href: "/showcases/scopelytics",
    excerpt: "How a mobile game studio uses batch scoring pipelines to understand player behavior.",
  },
  {
    title: "AI News: LLM evaluation benchmarks",
    category: "News",
    href: "/ai-news",
    excerpt: "Curated AI news from official sources, heuristically scored and human-reviewed.",
  },
];

export function TourExamples({ examples }: { examples?: TourExampleItem[] }) {
  const items = examples ?? fallbackExamples;
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="tour-examples" className="bg-white py-28">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          ref={ref}
          className="text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: publicEase }}
        >
          <span className="mb-4 inline-block rounded-full border border-[var(--color-story-green)]/30 bg-[var(--color-story-green)]/8 px-4 py-1.5 text-[11px] font-medium tracking-wider uppercase text-[var(--color-story-green)]">
            Live Examples
          </span>
          <h2 className="font-display text-[clamp(2rem,5vw,3.5rem)] leading-[1.05] tracking-[-0.03em] text-[var(--color-charcoal-black)]">
            Real content, real results
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[var(--color-book-text-gray)]">
            Browse published content generated through the AI pipeline — all human-reviewed, all production-ready.
          </p>
        </motion.div>

        <motion.div
          className="mt-16 grid gap-6 md:grid-cols-3"
          variants={publicStaggerContainer}
          initial="hidden"
          animate={isInView ? "show" : "hidden"}
        >
          {items.map((ex) => (
            <motion.div key={ex.href} variants={publicStaggerItem}>
              <Link
                href={ex.href}
                className="group block rounded-2xl border border-[var(--color-book-text-gray)]/10 bg-[var(--color-vellum-background)] p-6 transition-all duration-300 hover:border-[var(--color-story-green)]/30 hover:shadow-sm"
              >
                <span className="inline-block rounded-full bg-[var(--color-story-green)]/10 px-3 py-1 text-[11px] font-medium tracking-wider text-[var(--color-story-green)] uppercase">
                  {ex.category}
                </span>
                <h3 className="mt-4 font-display text-lg leading-snug tracking-tight text-[var(--color-charcoal-black)] transition-colors group-hover:text-[var(--color-story-green)]">
                  {ex.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--color-book-text-gray)]">
                  {ex.excerpt}
                </p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[var(--color-story-green)] transition-colors group-hover:text-[var(--color-charcoal-black)]">
                  Read more →
                </span>
              </Link>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          className="mt-12 text-center"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ delay: 0.6, duration: 0.6 }}
        >
          <Link
            href="/blog"
            className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-story-green)] transition-colors hover:text-[var(--color-charcoal-black)]"
          >
            View all published content →
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
