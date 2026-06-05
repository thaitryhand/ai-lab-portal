"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, type Variants } from "framer-motion";
import { ArrowRight, ExternalLink, Eye, EyeOff, ShieldCheck } from "lucide-react";

import { AdminFormField, AdminInput } from "@/components/admin/admin-form";
import { adminCardClass, adminDisplayTitleClass, adminEyebrowClass, adminLoginFieldClass } from "@/components/admin/admin-ui";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const easeOut = [0.16, 1, 0.3, 1] as const;

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: easeOut } },
};

export function AdminLoginScreen() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    const form = e.currentTarget;
    const formData = new FormData(form);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      const res = await fetch("/api/auth/sign-in/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, callbackURL: "/admin", rememberMe: false }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data?.error || data?.message || "Invalid credentials");
        return;
      }

      const data = await res.json();
      router.push(data.url || "/admin");
    } catch {
      setError("Login failed. Check credentials and try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="relative flex min-h-dvh flex-col bg-vellum-background">
      {/* Ambient bg */}
      <div aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_45%_at_85%_0%,color-mix(in_srgb,var(--color-story-green)_10%,transparent),transparent_60%)]" />

      <div className="relative mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-6 sm:px-8 sm:py-8">
        {/* Header */}
        <motion.header className="flex items-center justify-between" variants={fadeUp} initial="hidden" animate="visible">
          <div className="flex items-center gap-3">
            <div className="h-6 w-0.5 rounded-full bg-brand/50" aria-hidden />
            <div>
              <p className={adminEyebrowClass}>AI Lab Portal</p>
              <p className="text-sm font-medium text-foreground">Admin CMS</p>
            </div>
          </div>
          <Link
            className="inline-flex h-[calc(var(--spacing)*8)] items-center gap-1.5 rounded-full border border-border/50 bg-card/70 px-3.5 text-xs font-semibold text-muted-foreground backdrop-blur-sm transition-colors hover:border-brand/25 hover:text-brand"
            href="/"
          >
            View site
            <ExternalLink className="size-3" aria-hidden />
          </Link>
        </motion.header>

        {/* Main */}
        <motion.div
          className="flex flex-1 items-center justify-center py-8"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.06, delayChildren: 0.08 } } }}
          initial="hidden"
          animate="visible"
        >
          <div className="grid w-full max-w-4xl items-center gap-10 lg:grid-cols-[1.2fr_1fr] lg:gap-14">
            {/* Copy */}
            <motion.div className="max-w-md space-y-6" variants={fadeUp}>
              <div className="space-y-3">
                <p className={cn(adminEyebrowClass, "text-brand")}>
                  <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-brand align-middle" />
                  Protected workspace
                </p>
                <h1 className={cn(adminDisplayTitleClass, "text-[2.5rem] leading-[0.95] sm:text-5xl lg:text-[3rem]")}>
                  Publish with
                  <br />
                  <span className="text-brand">intention</span>
                </h1>
                <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
                  Every piece of content passes through human review before it reaches the public surface.
                </p>
              </div>

              <ul className="space-y-2 border-l-2 border-brand/20 pl-4">
                {["Editorial review at every step", "Client-ready showcases", "Pipeline-to-publish workflow"].map((item) => (
                  <li key={item} className="text-sm leading-6 text-foreground/85">
                    {item}
                  </li>
                ))}
              </ul>

              <div className="flex items-center gap-3 rounded-full border border-border/40 bg-card/50 px-4 py-3">
                <ShieldCheck className="size-5 shrink-0 text-brand" aria-hidden />
                <p className="text-xs leading-relaxed text-muted-foreground">
                  Access is limited to trusted operators.
                </p>
              </div>
            </motion.div>

            {/* Card */}
            <motion.div variants={fadeUp}>
              <div className={cn(adminCardClass, "px-7 py-9 sm:px-9 sm:py-10")}>
                <div className="mb-8 space-y-2">
                  <p className={adminEyebrowClass}>Sign in</p>
                  <h2 className="text-xl font-semibold tracking-[-0.02em] text-foreground">Admin access</h2>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    Use the credentials configured for this environment.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <AdminFormField htmlFor="email" label="Email">
                    <AdminInput
                      autoComplete="email"
                      autoFocus
                      className={adminLoginFieldClass}
                      disabled={isSubmitting}
                      id="email"
                      name="email"
                      placeholder="you@company.com"
                      required
                      type="email"
                    />
                  </AdminFormField>

                  <AdminFormField htmlFor="password" label="Password">
                    <div className="relative">
                      <AdminInput
                        autoComplete="current-password"
                        className={cn(adminLoginFieldClass, "pr-10")}
                        disabled={isSubmitting}
                        id="password"
                        name="password"
                        required
                        type={showPassword ? "text" : "password"}
                      />
                      <button
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        className="absolute right-1 top-1/2 flex size-9 -translate-y-1/2 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50"
                        disabled={isSubmitting}
                        onClick={() => setShowPassword((v) => !v)}
                        type="button"
                      >
                        {showPassword ? <EyeOff className="size-[18px]" aria-hidden /> : <Eye className="size-[18px]" aria-hidden />}
                      </button>
                    </div>
                  </AdminFormField>

                  {error && (
                    <motion.p
                      initial={{ opacity: 0, y: -6 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-foreground"
                      role="alert"
                    >
                      {error}
                    </motion.p>
                  )}

                  <Button className="w-full" disabled={isSubmitting} type="submit" variant="brand">
                    {isSubmitting ? "Signing in..." : "Sign in"}
                    {!isSubmitting && <ArrowRight className="size-4" aria-hidden />}
                  </Button>
                </form>
              </div>
            </motion.div>
          </div>
        </motion.div>

        <motion.p className="text-center text-xs text-muted-foreground/50 lg:text-left" variants={fadeUp} initial="hidden" animate="visible">
          Authenticated publishing surface
        </motion.p>
      </div>
    </div>
  );
}
