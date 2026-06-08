---
name: AI Lab Portal
description: Editorial AI Lab platform with Medium-inspired warmth and restrained green accent
colors:
  vellum-background: "#f7f4ed"
  parchment-white: "#ffffff"
  charcoal-black: "#191919"
  inkwell-black: "#242424"
  book-text-gray: "#333333"
  muted-text-gray: "#6b6b6b"
  story-green: "#50b33a"
typography:
  display:
    fontFamily: "gt-super, ui-serif, Georgia, Cambria, Times New Roman, Times, serif"
    fontSize: "clamp(3.5rem, 10vw, 120px)"
    fontWeight: 400
    lineHeight: 0.83
    letterSpacing: "-6.6px"
  body:
    fontFamily: "medium-content-sans-serif-font, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.2
  subheading:
    fontFamily: "sohne, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.43
  heading-sm:
    fontFamily: "sohne, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: 1.54
  caption:
    fontFamily: "sohne, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.27
rounded:
  pill: "1386px"
  pill-alt: "1980px"
  admin-sm: "10px"
  admin-md: "14px"
  admin-lg: "18px"
  admin-xl: "22px"
  admin-2xl: "26px"
  admin-3xl: "32px"
spacing:
  unit: "8px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "48px"
  section: "64px"
components:
  button-primary:
    backgroundColor: "{colors.charcoal-black}"
    textColor: "{colors.parchment-white}"
    rounded: "{rounded.pill}"
    padding: "16px 48px"
  button-primary-hover:
    backgroundColor: "{colors.story-green}"
    textColor: "{colors.parchment-white}"
    rounded: "{rounded.pill}"
    padding: "16px 48px"
  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.charcoal-black}"
    rounded: "{rounded.pill}"
    padding: "16px 48px"
  card-public:
    backgroundColor: "{colors.parchment-white}"
    rounded: "{rounded.admin-md}"
    padding: "{spacing.md}"
  card-admin:
    backgroundColor: "{colors.vellum-background}"
    rounded: "{rounded.admin-lg}"
    padding: "{spacing.lg}"
  input-field:
    backgroundColor: "{colors.parchment-white}"
    textColor: "{colors.inkwell-black}"
    rounded: "{rounded.pill}"
---
# Design System: AI Lab Portal

> Derived from `styles/DESIGN.md` (Medium-inspired style reference) and `docs/product/style-guide.md`.
> Token values verified against `frontend/app/theme.css`.
> This file follows the [Google Stitch DESIGN.md format](https://stitch.withgoogle.com/docs/design-md/format/)
> for compatibility with AI design tools. For the full original reference, see `styles/DESIGN.md`.

## 1. Overview

**Creative North Star: "The Editorial Workshop"**

A warm, writing-forward platform where content is the hero and the interface steps back. Inspired by Medium's editorial warmth — vellum canvas, ink-black typography, minimal chrome, and a single restrained green accent. The design signals credibility through restraint: generous whitespace, pill-shaped actions, and a type-driven hierarchy that makes long-form content inviting to read.

The admin surface extends the same philosophy into a tool context: clean, transparent, state-visible. No dark dashboards, no glass effects, no AI clichés. The platform's design quality is itself a product credential.

**Key Characteristics:**
- Warm vellum (`#f7f4ed`) as the primary canvas — not cool gray, not pure white
- Editorial serif display type paired with warm sans-serif body
- Pill-radius buttons as the consistent interactive affordance
- Single green accent (`#50b33a`) reserved for brand emphasis — rare, intentional
- Flat surfaces by default; shadows only as state-driven responses
- Admin shell uses the same editorial tokens, tuned for tool clarity

## 2. Colors

Warm editorial palette rooted in a vellum-cream base with ink-black text and a single reserved green accent. The palette is restrained by design: one accent color, few surfaces, minimal chrome.

### Primary
- **Inkwell Black** (#242424): Primary body text and UI labels. The reading anchor.
- **Charcoal Black** (#191919): Primary button fills, display headlines, and high-emphasis surfaces.

### Neutral
- **Vellum Background** (#f7f4ed): Primary page canvas. Warm, off-white, the foundation of the editorial feel.
- **Parchment White** (#ffffff): Secondary surfaces — cards, containers, admin panels.
- **Book Text Gray** (#333333): Borders, secondary text, structural lines.
- **Muted Text Gray** (#6b6b6b): Captions, metadata, muted labels.

### Accent
- **Story Green** (#50b33a): The single brand accent. Used for hover states, selected indicators, success signals, and rare brand moments. Never exceeds ~5% of any given screen.

### Named Rules
**The One Voice Rule.** The green accent appears on ≤5% of any given screen. Its rarity is the point. If green is everywhere, the brand has no voice.

**The No Neon Rule.** No purple gradients, electric blues, or AI-neon colors. The palette stays anchored in the physical world: paper, ink, book cloth.

## 3. Typography

**Display Font:** GT Super (ui-serif, Georgia, Cambria, Times New Roman, Times, serif)
**Body Font:** Medium Content Sans-Serif (ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif)
**UI Font:** Sohne (ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif)
**Mono Font:** SF Mono / Fira Code / Cascadia Code (ui-monospace, monospace)

**Character:** Editorial elegance meets tool readability. GT Super gives display headlines a distinctive magazine weight — substantial, readable, never decorative. The body stack is warm and highly legible at reading size. Sohne handles UI labels, navigation, and subheadings with a clean, slightly condensed presence.

### Hierarchy
- **Display** (400, clamp(3.5rem, 10vw, 120px), 0.83, -6.6px tracking): Hero headlines and section titles. Generous scale, tight leading.
- **Heading Small** (400, 22px, 1.54): Section sub-headers, card titles.
- **Subheading** (400, 20px, 1.43): Article summaries, list item titles.
- **Body** (400, 16px, 1.2): Primary reading text. Cap line length at 65–75ch.
- **Caption** (400, 13px, 1.27): Metadata, timestamps, secondary labels.

### Named Rules
**The No Weight Crutch Rule.** All text is regular (400) weight by default. Hierarchy is achieved through scale, tracking, and spacing — not heavier weights. No bold body text.

## 4. Elevation

Flat by default. Surfaces sit on the vellum canvas through color contrast (parchment-white cards on vellum), not shadows. Depth is conveyed through tonal layering, not elevation.

Shadows, when they appear, are a response to interaction state:
- **Hover lift** — `0 4px 24px rgba(0,0,0,0.12)` on interactive cards and buttons
- **Dropdown / popover** — `0 8px 32px rgba(0,0,0,0.15)` for menus and floating panels

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only as a response to state (hover, elevation, focus). No ambient shadows on static content.

## 5. Components

### Buttons
- **Shape:** Pill radius (1386px / 1980px — effectively full-round).
- **Primary:** Charcoal-black fill, white text, 16px 48px padding. Hover transitions to Story Green fill.
- **Ghost:** Transparent background, charcoal-black text, pill radius. Hover adds subtle background tint.
- **State transitions:** 200ms ease-out on background-color and transform. No bounce, no elastic.

### Cards / Containers
- **Public cards:** Parchment-white background, admin-md radius (14px), 16px internal padding. Flat at rest.
- **Admin cards:** Vellum-background surface (slightly tonal), admin-lg radius (18px), 24px internal padding.
- **Border:** None on public cards; 1px solid Book Text Gray on admin cards for structural separation.

### Inputs / Fields
- **Style:** Parchment-white background, pill radius, 1px solid Book Text Gray border.
- **Focus:** Border shifts to Charcoal Black. No glow, no ring offset.
- **Padding:** 12px 16px internal.

### Navigation (admin shell)
- **Style:** Text-based navigation using Sohne UI font, regular weight.
- **Default:** Muted Text Gray. Hover: Inkwell Black. Active: Charcoal Black.
- **Mobile:** Collapsible sidebar with smooth expand/collapse transition.

### Navigation (public)
- **Style:** Minimal top bar with vellum background. Links in Book Text Gray.
- **Active page:** Underline indicator, Inkwell Black text.
- **CTA button:** Pill-shaped, Charcoal Black fill.

### Chips / Tags
- **Style:** Vellum-background fill, Book Text Gray text, pill radius.
- **Selected:** Charcoal Black fill, white text.
- **Dismissible:** Small × icon at trailing edge.

## 6. Do's and Don'ts

### Do:
- **Do** use warm vellum (#f7f4ed) as the primary page background.
- **Do** keep buttons pill-shaped (1386px+ radius).
- **Do** reserve Story Green for rare accent moments — hover states, success signals, brand emphasis.
- **Do** use scale and tracking for typographic hierarchy — not weight.
- **Do** prefer tonal layering (cream cards on vellum) over shadows.
- **Do** keep public surfaces content-forward with minimal chrome.
- **Do** make admin state visible — loading, empty, error, pending approval.
- **Do** use 65–75ch max line length for body content.

### Don't:
- **Don't** use purple gradients, neon accents, or glassmorphism.
- **Don't** use dark mode as default for admin or public surfaces.
- **Don't** use heavy shadows, glossy cards, or dense chrome on public pages.
- **Don't** exceed ~5% green accent coverage on any screen.
- **Don't** use bold or semibold font weights for hierarchy.
- **Don't** use side-stripe borders (border-left/right >1px as colored accents).
- **Don't** use gradient text (background-clip: text).
- **Don't** use the hero-metric template (big number, small label, gradient).
- **Don't** use identical card grids with icon + heading + text repeated endlessly.
- **Don't** use em dashes — use commas, colons, or periods instead.
