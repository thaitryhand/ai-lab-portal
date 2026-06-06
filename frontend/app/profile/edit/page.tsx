import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ImageUploadField } from "@/components/ui/image-upload-field";
import { auth } from "@/lib/auth/server";
import { getMyProfile } from "@/lib/user/profile";
import { cn } from "@/lib/utils";
import { updateProfileAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function EditProfilePage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");
  const profile = await getMyProfile(session);

  return (
    <PublicPageShell currentPath="/profile">
      <div className={cn(publicMainWidthClass, "flex flex-col gap-8 pb-12")}>
        {/* ── Header ── */}
        <div>
          <PublicBackLink href="/profile">Profile</PublicBackLink>
          <div className="mt-5 space-y-1.5">
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Edit profile
            </h1>
            <p className="text-sm text-muted-foreground">
              Update your public display name, bio, avatar, cover image, and links.
            </p>
          </div>
        </div>

        {/* ── Form ── */}
        <form action={updateProfileAction} className="space-y-10">
          {/* ── Section: Profile media ── */}
          <section className="rounded-2xl border border-border/80 bg-card shadow-sm">
            <div className="px-8 py-8 sm:px-10 sm:py-10">
              <div className="mb-6 flex flex-col gap-1.5 border-b border-border/60 pb-5">
                <p className="text-base font-semibold text-foreground">Profile media</p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  Keep the page clean: upload avatar and cover from focused dialogs.
                </p>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <ImageUploadField
                  name="avatarUrl"
                  initialUrl={profile.avatarUrl ?? undefined}
                  aspectClass="aspect-square"
                  roundedClass="rounded-full"
                  label="Avatar"
                  description="Your compact identity mark across comments, posts, and profile cards."
                  placeholder="https://example.com/avatar.png"
                  hint="Square image recommended. JPG, PNG, WebP, GIF, or AVIF. Max 10MB."
                  variant="avatar"
                />
                <ImageUploadField
                  name="coverUrl"
                  initialUrl={profile.coverUrl ?? undefined}
                  aspectClass="aspect-video"
                  roundedClass="rounded-xl"
                  label="Cover image"
                  description="A 16:9 visual hero shown cleanly at the top of your profile."
                  placeholder="https://example.com/cover.png"
                  hint="16:9 image recommended. Screenshots and hero visuals work best."
                  variant="cover"
                />
              </div>
            </div>
          </section>

          {/* ── Section: Profile Info ── */}
          <section className="rounded-2xl border border-border/80 bg-card shadow-sm">
            <div className="px-8 pt-8 pb-8 sm:px-10 sm:pt-10 sm:pb-10">
              <div className="mb-8 pb-6 border-b border-border/60">
                <p className="text-base font-semibold text-foreground">Profile information</p>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  Your name and bio appear on your public profile page.
                </p>
              </div>

              <div className="space-y-6">
                <div className="space-y-1.5">
                  <label htmlFor="displayName" className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
                    Display name <span className="text-destructive">*</span>
                  </label>
                  <Input
                    id="displayName"
                    name="displayName"
                    required
                    defaultValue={profile.displayName}
                    maxLength={120}
                    placeholder="Your display name"
                    className="h-11 text-sm"
                  />
                  <p className="text-xs text-muted-foreground/70">
                    Your public-facing name — can be a real name or alias.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="bio" className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
                    Bio
                  </label>
                  <textarea
                    id="bio"
                    name="bio"
                    defaultValue={profile.bio ?? ""}
                    maxLength={2000}
                    rows={5}
                    placeholder="Tell us a bit about yourself…"
                    className="min-h-[140px] w-full resize-none rounded-xl border border-border/80 bg-background px-5 py-4 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground/50 transition-colors focus:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/10"
                  />
                  <div className="flex justify-end">
                    <span className="text-xs tabular-nums text-muted-foreground">
                      {(profile.bio ?? "").length} / 2000
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ── Section: Social Links ── */}
          <section className="rounded-2xl border border-border/80 bg-card shadow-sm">
            <div className="px-8 pt-8 pb-8 sm:px-10 sm:pt-10 sm:pb-10">
              <div className="mb-8 pb-6 border-b border-border/60">
                <p className="text-base font-semibold text-foreground">Social links</p>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  Add links to your online presence across the web.
                </p>
              </div>

              <div className="grid gap-6">
                <div className="space-y-1.5">
                  <label htmlFor="websiteUrl" className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
                    Website
                  </label>
                  <div className="relative">
                    <GlobeIcon className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground/40" />
                    <Input
                      id="websiteUrl"
                      name="websiteUrl"
                      type="url"
                      defaultValue={profile.websiteUrl ?? ""}
                      placeholder="https://example.com"
                      className="h-11 pl-11 text-sm"
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="githubUrl" className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
                    GitHub
                  </label>
                  <div className="relative">
                    <GithubIcon className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground/40" />
                    <Input
                      id="githubUrl"
                      name="githubUrl"
                      type="url"
                      defaultValue={profile.githubUrl ?? ""}
                      placeholder="https://github.com/username"
                      className="h-11 pl-11 text-sm"
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="linkedinUrl" className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
                    LinkedIn
                  </label>
                  <div className="relative">
                    <LinkedinIcon className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground/40" />
                    <Input
                      id="linkedinUrl"
                      name="linkedinUrl"
                      type="url"
                      defaultValue={profile.linkedinUrl ?? ""}
                      placeholder="https://linkedin.com/in/username"
                      className="h-11 pl-11 text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ── Submit ── */}
          <div className="flex items-center justify-between rounded-2xl border border-border/40 bg-card/50 px-8 py-5 sm:px-10">
            <a
              href="/profile"
              className="text-sm font-medium text-muted-foreground underline underline-offset-2 decoration-border/50 transition-colors hover:text-foreground hover:decoration-foreground/30"
            >
              Cancel
            </a>
            <Button
              type="submit"
              className="rounded-full px-10 h-12 font-medium shadow-sm"
            >
              Save changes
            </Button>
          </div>
        </form>
      </div>
    </PublicPageShell>
  );
}

// ── Inline SVG icons ──

function GlobeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function GithubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  );
}

function LinkedinIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}
