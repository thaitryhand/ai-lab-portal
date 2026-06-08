"use client";

import { motion } from "framer-motion";

import { publicEase } from "@/components/public/public-motion";
import { Button } from "@/components/ui/button";

const pipelineStages = [
  { label: "Project", icon: "📦" },
  { label: "Idea", icon: "💡" },
  { label: "Outline", icon: "📋" },
  { label: "Draft", icon: "✍️" },
  { label: "Review", icon: "🔍" },
  { label: "Marketing", icon: "📢" },
  { label: "Publish", icon: "🚀" },
];

export function TourHero() {
  return (
    <section className="relative min-h-[90vh] flex flex-col items-center justify-center overflow-hidden px-6">
      {/* Decorative background grain */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.03] bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJmIj48ZmVUdXJidWxlbmNlIHR5cGU9ImZyYWN0YWxOb2lzZSIgYmFzZUZyZXF1ZW5jeT0iLjc1Ii8+PC9maWx0ZXI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsdGVyPSJ1cmwoI2YpIiBvcGFjaXR5PSIwIi8+PC9zdmc+')]" />

      <motion.div
        className="relative z-10 mx-auto max-w-4xl text-center"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: publicEase }}
      >
        {/* Eyebrow */}
        <motion.span
          className="mb-6 inline-block rounded-full border border-[var(--color-story-green)]/30 bg-[var(--color-story-green)]/8 px-4 py-1.5 text-[11px] font-medium tracking-wider uppercase text-[var(--color-story-green)]"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: publicEase }}
        >
          AI Lab Portal · Live Demo
        </motion.span>

        {/* Headline */}
        <motion.h1
          className="font-display text-[clamp(2.8rem,8vw,5.5rem)] leading-[0.88] tracking-[-0.04em] text-[var(--color-charcoal-black)]"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.35, ease: publicEase }}
        >
          See the
          <br />
          <span className="text-[var(--color-story-green)]">AI Lab</span> in Action
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-[var(--color-book-text-gray)]"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5, ease: publicEase }}
        >
          Watch how our semi-auto AI pipeline turns a project into a published blog post —
          from idea generation to technical review, marketing metadata, and one-click publish.
        </motion.p>

        {/* CTA buttons */}
        <motion.div
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.65, ease: publicEase }}
        >
          <Button
            size="lg"
            className="rounded-full bg-[var(--color-charcoal-black)] px-10 py-6 text-base text-white transition-all duration-300 hover:bg-[var(--color-story-green)] hover:scale-[1.02]"
            onClick={() => document.getElementById("tour-pipeline")?.scrollIntoView({ behavior: "smooth" })}
          >
            Watch the pipeline →
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="rounded-full border-[var(--color-book-text-gray)]/30 px-10 py-6 text-base text-[var(--color-charcoal-black)] transition-all duration-300 hover:bg-[var(--color-charcoal-black)]/5"
            onClick={() => document.getElementById("tour-examples")?.scrollIntoView({ behavior: "smooth" })}
          >
            See live examples
          </Button>
        </motion.div>
      </motion.div>

      {/* ── Pipeline stage indicator ── */}
      <motion.div
        className="absolute bottom-12 left-1/2 z-10 -translate-x-1/2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.8 }}
      >
        <div className="flex items-center gap-3">
          {pipelineStages.map((stage, i) => (
            <motion.div
              key={stage.label}
              className="flex flex-col items-center gap-1.5"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.4 + i * 0.06, duration: 0.4, ease: publicEase }}
            >
              <div className="flex size-8 items-center justify-center rounded-full border border-[var(--color-book-text-gray)]/20 bg-white/60 text-xs backdrop-blur-sm">
                {stage.icon}
              </div>
              <span className="text-[10px] font-medium tracking-wider text-[var(--color-muted-text-gray)] uppercase">
                {stage.label}
              </span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-4 left-1/2 z-10 -translate-x-1/2"
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        <svg width="16" height="24" viewBox="0 0 16 24" fill="none" className="text-[var(--color-muted-text-gray)]">
          <rect x="1" y="1" width="14" height="22" rx="7" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="8" cy="8" r="2" fill="currentColor" />
        </svg>
      </motion.div>
    </section>
  );
}
