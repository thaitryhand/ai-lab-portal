"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

type TocItem = {
  id: string;
  text: string;
  level: number;
};

/**
 * Extracts headings from the article content and renders a
 * sticky table of contents sidebar. Highlights the active section
 * based on scroll position.
 */
export function TableOfContents({ contentSelector }: { contentSelector: string }) {
  const [items, setItems] = useState<TocItem[]>([]);
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    const article = document.querySelector(contentSelector);
    if (!article) return;

    const headings = article.querySelectorAll("h2, h3, h4");
    const tocItems: TocItem[] = [];

    headings.forEach((h, i) => {
      const id = h.id || `heading-${i}`;
      if (!h.id) h.id = id;
      tocItems.push({
        id,
        text: h.textContent || "",
        level: parseInt(h.tagName[1], 10),
      });
    });

    const rafId = requestAnimationFrame(() => {
      setItems(tocItems);
    });

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
            break;
          }
        }
      },
      { rootMargin: "-80px 0px -80% 0px" },
    );

    headings.forEach((h) => observer.observe(h));
    return () => {
      cancelAnimationFrame(rafId);
      observer.disconnect();
    };
  }, [contentSelector]);

  if (items.length < 2) return null;

  return (
    <nav
      className="hidden xl:block sticky top-24 w-56 shrink-0 max-h-[calc(100vh-8rem)] overflow-y-auto"
      aria-label="Table of contents"
    >
      <p className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wider">
        On this page
      </p>
      <ul className="space-y-1.5">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              className={cn(
                "block text-xs leading-snug py-0.5 transition-colors border-l-2 pl-3",
                activeId === item.id
                  ? "text-brand border-brand font-medium"
                  : "text-muted-foreground border-transparent hover:text-foreground hover:border-border",
              )}
              style={{ paddingLeft: `${0.75 + (item.level - 2) * 0.75}rem` }}
              onClick={(e) => {
                e.preventDefault();
                document.getElementById(item.id)?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              {item.text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
