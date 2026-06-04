"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { PenLine } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    if (searchParams.get("registered") === "true") {
      setRegistered(true);
    }
  }, [searchParams]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setRegistered(false);
    setIsSubmitting(true);

    const form = e.currentTarget;
    const formData = new FormData(form);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      const res = await fetch("/api/auth/sign-in/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, callbackURL: "/", rememberMe: false }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data?.error || data?.message || "Invalid credentials");
        return;
      }

      const data = await res.json();
      router.push(data.url || "/");
      router.refresh();
    } catch {
      setError("Login failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[80dvh] max-w-sm flex-col justify-center px-4 py-12">
      <div className="space-y-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand/30 bg-accent text-brand">
            <PenLine className="size-4" aria-hidden />
          </span>
          <span className="text-sm font-semibold text-foreground">AI Lab Portal</span>
        </Link>

        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight">Welcome back</h1>
          <p className="text-sm text-muted-foreground">
            Sign in to react, comment, and bookmark blog posts.
          </p>
        </div>

        {registered && (
          <div className="rounded-xl border border-brand/20 bg-brand/5 px-4 py-3 text-sm text-brand">
            Account created successfully! Sign in below.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium text-foreground">
              Email address
            </label>
            <Input
              autoComplete="email"
              autoFocus
              disabled={isSubmitting}
              id="email"
              name="email"
              placeholder="you@example.com"
              required
              type="email"
              className="h-11"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-foreground">
              Password
            </label>
            <Input
              autoComplete="current-password"
              disabled={isSubmitting}
              id="password"
              name="password"
              required
              type="password"
              className="h-11"
            />
          </div>

          {error && (
            <p className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive" role="alert">
              {error}
            </p>
          )}

          <Button className="h-11 w-full text-sm" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-semibold text-brand underline underline-offset-2 hover:text-brand/80">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function PublicLoginPage() {
  return (
    <div className="min-h-screen bg-background">
      <Suspense fallback={
        <div className="mx-auto flex min-h-[80dvh] max-w-sm flex-col justify-center px-4 py-12">
          <div className="space-y-8">
            <div className="h-10 w-48 animate-pulse rounded-lg bg-muted" />
            <div className="space-y-4">
              <div className="h-8 w-40 animate-pulse rounded bg-muted" />
              <div className="h-4 w-64 animate-pulse rounded bg-muted" />
            </div>
          </div>
        </div>
      }>
        <LoginForm />
      </Suspense>
    </div>
  );
}
