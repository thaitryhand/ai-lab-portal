/** Shared editorial styling for public pages (brand register, vellum canvas). */
export const publicPageMainClass = "min-h-screen bg-background text-foreground";

/** Outer gutter — header, main, footer share this horizontal inset */
export const publicShellGutterClass = "px-5 sm:px-10 lg:px-14 xl:px-16";

/** Single page column: same width for header, main, and footer */
export const publicShellContainerClass =
  "relative mx-auto flex min-h-dvh w-full max-w-6xl flex-col pb-20 px-5 sm:px-10 lg:px-14 xl:px-16";

/** Main content spans the full shell width (do not add narrower max-w here) */
export const publicMainWidthClass = "w-full min-w-0";

/** Optional reading measure for long-form body text inside a full-width article */
export const publicProseMeasureClass = "mx-auto w-full max-w-[72ch]";

/** Inner padding for hero panels, CTA bands, and large cards — 8px rhythm from styles/ */
export const publicPanelPaddingClass =
  "px-8 py-12 sm:px-12 sm:py-14 lg:px-16 lg:py-16 xl:px-20 xl:py-18";

/** Compact card padding for landing cards — one step below panel padding */
export const publicLandingCardPaddingClass =
  "p-8 sm:p-9 lg:p-10";

/** Column gap inside split hero / two-column panels */
export const publicPanelGridGapClass = "gap-12 sm:gap-14 lg:gap-20 xl:gap-24";

/** List rows and compact panels — slightly less than hero, still breathable */
export const publicContentInsetClass = "px-8 py-8 sm:px-10 sm:py-9 lg:px-12 lg:py-10";

export const publicAtmosphereClass =
  "pointer-events-none absolute inset-0 overflow-hidden";

export const publicEyebrowClass =
  "text-[11px] font-semibold uppercase tracking-[0.32em] text-brand";

export const publicDisplayTitleClass =
  "font-(family-name:--font-gt-super) font-normal tracking-tighter text-foreground";

/** Article/showcase titles — line-height must stay ≥ ~1.05 when titles wrap (gt-super overflows at 0.95) */
export const publicArticleTitleClass =
  "font-(family-name:--font-gt-super) text-[clamp(2.25rem,5vw,3.75rem)] font-normal leading-[1.08] tracking-tighter text-foreground text-balance sm:leading-[1.1]";

export const publicPageTitleClass =
  "font-(family-name:--font-gt-super) text-5xl font-normal leading-[0.95] tracking-tighter text-foreground sm:text-6xl";

export const publicHeroTitleClass =
  "font-(family-name:--font-gt-super) text-[clamp(2.5rem,5.5vw,4.75rem)] font-normal leading-[0.9] tracking-[-0.055em] text-foreground";

export const publicCardClass = "rounded-3xl border border-border bg-card shadow-sm";

export const publicLeadClass =
  "max-w-2xl text-lg leading-8 text-muted-foreground sm:text-xl sm:leading-[1.65]";

export const publicSectionTitleClass =
  "font-(family-name:--font-gt-super) text-2xl font-normal tracking-[-0.03em] text-foreground sm:text-4xl";

export const publicMetaClass = "text-sm text-muted-foreground";

export const publicPrimaryCtaClass =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full bg-primary px-6 py-3.5 text-sm font-semibold text-primary-foreground! shadow-[0_1px_0_color-mix(in_srgb,var(--foreground)_8%,transparent),0_12px_32px_color-mix(in_srgb,var(--primary)_18%,transparent)] transition-[transform,background-color,box-shadow] duration-200 hover:-translate-y-px hover:bg-primary/92 hover:shadow-[0_1px_0_color-mix(in_srgb,var(--foreground)_8%,transparent),0_16px_40px_color-mix(in_srgb,var(--primary)_22%,transparent)] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 active:translate-y-0";

export const publicSecondaryCtaClass =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full border border-border/90 bg-card/90 px-6 py-3.5 text-sm font-semibold text-foreground backdrop-blur-sm transition-[transform,border-color,background-color] duration-200 hover:-translate-y-px hover:border-brand/35 hover:bg-card focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/30 active:translate-y-0";

export const publicGhostCtaClass =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 py-3.5 text-sm font-semibold text-muted-foreground transition-colors hover:bg-muted/70 hover:text-foreground";

export const publicPillLinkClass = "rounded-full px-5 py-3 text-sm font-semibold";

export const publicListPanelClass =
  "overflow-hidden rounded-3xl border border-border/90 bg-card/95 shadow-[0_24px_64px_color-mix(in_srgb,var(--primary)_6%,transparent)] backdrop-blur-sm";

export const publicListRowClass =
  "group/row relative block border-b border-border/70 px-8 py-8 transition-[background-color,transform] duration-300 last:border-b-0 hover:bg-muted/35 sm:px-10 sm:py-9 lg:px-12 lg:py-10";

export const publicPageStackClass = "flex flex-col gap-16 sm:gap-20 lg:gap-24";

export const publicPageHeroPanelClass =
  "relative overflow-hidden rounded-[2rem] border border-border/80 bg-card/95 shadow-[0_28px_72px_color-mix(in_srgb,var(--primary)_7%,transparent)] backdrop-blur-sm";

export const publicEntryTitleClass =
  "font-(family-name:--font-gt-super) text-2xl font-normal tracking-[-0.03em] text-foreground transition-colors group-hover:text-brand sm:text-3xl";

export const publicEntryExcerptClass = "mt-3 max-w-xl text-base leading-7 text-muted-foreground";

export const publicProseClass =
  "w-full space-y-6 text-lg leading-[1.75] text-foreground [&_strong]:font-semibold";

/** @deprecated Use publicMainWidthClass — kept for imports during migration */
export const publicArticleWidthClass = publicMainWidthClass;

/** @deprecated Use publicMainWidthClass */
export const publicIndexWidthClass = publicMainWidthClass;

export const publicEmptyStateClass =
  "rounded-3xl border border-dashed border-border bg-card/60 px-8 py-16 text-center sm:px-12 lg:px-16";

export const publicBackLinkClass =
  "inline-flex items-center gap-1.5 text-sm font-semibold text-muted-foreground transition-colors hover:text-brand";

export const publicHeroPanelClass =
  "relative overflow-hidden rounded-[2rem] border border-border/80 bg-card/95 shadow-[0_32px_80px_color-mix(in_srgb,var(--primary)_8%,transparent)] backdrop-blur-sm";

export const publicLandingHeaderClass =
  "sticky top-6 z-50 flex items-center justify-between gap-6 rounded-2xl border border-border/80 bg-card/85 px-6 py-4 shadow-[0_8px_32px_color-mix(in_srgb,var(--primary)_6%,transparent)] backdrop-blur-md sm:px-8 sm:py-5 lg:px-10";

/** Vertical rhythm between landing sections */
export const publicLandingSectionGap = "scroll-mt-28";

export const publicLandingStackClass = "flex flex-col gap-24 sm:gap-28 lg:gap-32";

export const publicSectionHeaderBlockClass = "mb-12 sm:mb-14 lg:mb-16";

export const publicSectionIntroGapClass = "mt-4 sm:mt-5";
