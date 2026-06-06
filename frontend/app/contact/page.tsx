"use client";

import { useState } from "react";

import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
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
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Contact</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl lg:text-5xl">
            Get in touch
          </h1>
          <p className="mt-4 max-w-lg text-base leading-7 text-muted-foreground">
            Have a question, feedback, or interested in working with us? Send us a message and we&apos;ll
            get back to you.
          </p>
        </div>

        {status === "success" ? (
          <div className="rounded-lg border border-green-200 bg-green-50 p-8 text-center dark:border-green-800 dark:bg-green-950/30">
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
          <form onSubmit={handleSubmit} className="flex max-w-lg flex-col gap-6">
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
                placeholder="Your message…"
                rows={6}
                minLength={1}
                maxLength={10000}
              />
            </div>

            {status === "error" && (
              <p className="text-sm text-red-600 dark:text-red-400">
                {errorMessage || "Failed to send message. Please try again."}
              </p>
            )}

            <Button type="submit" disabled={status === "submitting"}>
              {status === "submitting" ? "Sending…" : "Send message"}
            </Button>
          </form>
        )}
      </section>
    </PublicPageShell>
  );
}
