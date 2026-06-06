"use client";

import { useState } from "react";

import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import {
  publicEyebrowClass,
  publicMainWidthClass,
  publicPanelPaddingClass,
} from "@/components/public/public-ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export default function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    setErrorMessage("");

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, subject, message }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail?.[0]?.msg ?? data?.detail ?? "Failed to send message");
      }

      setStatus("success");
      setName("");
      setEmail("");
      setSubject("");
      setMessage("");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : "An unexpected error occurred");
    }
  };

    return (
      <PublicPageShell currentPath="/contact">
        <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
          <PublicPageHero
            description="Send a project question, feedback on the portal, or a collaboration note. Messages stay private until someone from the lab reviews them."
            eyebrow="Contact"
            title="Start a useful conversation."
          />

          {status === "success" ? (
            <div className="rounded-[1.5rem] border border-brand/25 bg-accent p-8 text-center sm:p-10">
              <h2 className="text-xl font-semibold text-green-800 dark:text-green-300">Message sent!</h2>
              <p className="mt-2 text-green-700 dark:text-green-400">
                Thank you for reaching out. We&apos;ll review your message and respond shortly.
            </p>
            <Button
              variant="outline"
              className="mt-6"
              onClick={() => setStatus("idle")}
            >
              Send another message
              </Button>
            </div>
          ) : (
            <div className="grid gap-8 lg:grid-cols-[0.88fr_1.12fr] lg:items-start lg:gap-12">
              <aside className={cn("rounded-[1.5rem] border border-border/80 bg-card/80", publicPanelPaddingClass)}>
                <p className={publicEyebrowClass}>What happens next</p>
                <div className="mt-8 grid gap-6 text-sm leading-7 text-muted-foreground">
                  {[
                    ["01", "We read for fit, context, and urgency before replying."],
                    ["02", "Product and implementation questions get routed to the right owner."],
                    ["03", "No public content ships from this form without explicit review."],
                  ].map(([index, copy]) => (
                    <div key={index} className="flex gap-4 border-t border-border/70 pt-5 first:border-t-0 first:pt-0">
                      <span className="font-(family-name:--font-gt-super) text-2xl leading-none text-brand/75">
                        {index}
                      </span>
                      <p>{copy}</p>
                    </div>
                  ))}
                </div>
              </aside>

              <form
                onSubmit={handleSubmit}
                className={cn("flex flex-col gap-6 rounded-[1.5rem] border border-border/80 bg-card/90", publicPanelPaddingClass)}
              >
                <div className="grid gap-6 sm:grid-cols-2">
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="contact-name">Name *</Label>
                    <Input
                      id="contact-name"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Your name"
                      minLength={1}
                      maxLength={200}
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <Label htmlFor="contact-email">Email *</Label>
                    <Input
                      id="contact-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <Label htmlFor="contact-subject">Subject *</Label>
                  <Input
                    id="contact-subject"
                    required
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="What is this about?"
                    minLength={1}
                    maxLength={500}
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <Label htmlFor="contact-message">Message *</Label>
                  <Textarea
                    id="contact-message"
                    required
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Share the context, goal, and useful links."
                    rows={7}
                    minLength={1}
                    maxLength={10000}
                  />
                </div>

                {status === "error" && (
                  <p className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {errorMessage || "Failed to send message. Please try again."}
                  </p>
                )}

                <Button className="h-11 rounded-full" type="submit" disabled={status === "submitting"}>
                  {status === "submitting" ? "Sending..." : "Send message"}
                </Button>
              </form>
            </div>
          )}
        </section>
      </PublicPageShell>
  );
}
