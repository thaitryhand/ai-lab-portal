"use client";

import { motion, useInView } from "framer-motion";
import Link from "next/link";
import { useRef } from "react";

import { publicEase } from "@/components/public/public-motion";

export function TourCta() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section ref={ref} className="relative overflow-hidden bg-[var(--color-charcoal-black)] py-28">
      {/* Decorative grain */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.04] bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJmIj48ZmVUdXJidWxlbmNlIHR5cGU9ImZyYWN0YWxOb2lzZSIgYmFzZUZyZXF1ZW5jeT0iLjc1Ii8+PC9maWx0ZXI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsdGVyPSJ1cmwoI2YpIiBvcGFjaXR5PSIwIi8+PC9zdmc+')]" />

      <div className="relative z-10 mx-auto max-w-3xl px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: publicEase }}
        >
          <span className="mb-4 inline-block rounded-full border border-white/15 bg-white/8 px-4 py-1.5 text-[11px] font-medium tracking-wider text-white/70 uppercase">
            Get Started
          </span>

          <h2 className="font-display text-[clamp(2rem,5vw,3.5rem)] leading-[1.05] tracking-[-0.03em] text-white">
            Ready to build your
            <br />
            <span className="text-[var(--color-story-green)]">AI Lab</span>?
          </h2>

          <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-white/60">
            We turn IT expertise into AI product proof. From pipeline architecture
            to published content — let&rsquo;s show the world what you can build.
          </p>

          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Link
              href="/contact"
              className="inline-flex items-center gap-2 rounded-full bg-[var(--color-story-green)] px-10 py-4 text-sm font-medium text-white transition-all duration-300 hover:bg-white hover:text-[var(--color-charcoal-black)] hover:scale-[1.02]"
            >
              Start a project
            </Link>
            <Link
              href="/lab"
              className="inline-flex items-center gap-2 rounded-full border border-white/20 px-10 py-4 text-sm font-medium text-white/80 transition-all duration-300 hover:border-white/40 hover:text-white"
            >
              Explore the Lab
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
