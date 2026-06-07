import { Suspense } from "react";
import { headers } from "next/headers";
import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import {
  Briefcase,
  Code,
  Globe,
  Pencil,
  Settings,
  Bookmark,
  FileEdit,
  CalendarDays,
} from "lucide-react";

import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { auth } from "@/lib/auth/server";
import { getMyProfile } from "@/lib/user/profile";
import { cn } from "@/lib/utils";
import { ProfileContextSync } from "./profile-context-sync";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");
  const profile = await getMyProfile(session);

  const joinDate = profile.createdAt
    ? new Date(profile.createdAt).toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      })
    : null;

  const socialLinks = [
    { url: profile.websiteUrl, icon: Globe, label: "Website" },
    { url: profile.githubUrl, icon: Code, label: "GitHub" },
    { url: profile.linkedinUrl, icon: Briefcase, label: "LinkedIn" },
  ].filter((s) => s.url);

  return (
    <PublicPageShell currentPath="/profile">
      <Suspense fallback={null}>
        <ProfileContextSync />
      </Suspense>
      <div className={cn(publicMainWidthClass, "flex flex-col gap-8 px-3 pb-12 pt-6 sm:px-0 sm:pt-8")}>
        {/* ── Profile Header Card ── */}
        <div className="overflow-hidden rounded-[2rem] border border-border/80 bg-card shadow-sm">
          {/* Cover */}
          {profile.coverUrl ? (
            <div className="bg-[#171310] px-6 pt-6 sm:px-10 sm:pt-8 lg:px-14">
              <div className="relative mx-auto aspect-video max-w-5xl overflow-hidden rounded-xl bg-muted shadow-2xl shadow-black/20 ring-1 ring-white/10">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={profile.coverUrl}
                  alt=""
                  className="h-full w-full object-cover"
                />
              </div>
            </div>
          ) : (
            <div className="relative aspect-video max-h-130 w-full bg-linear-to-br from-brand/15 via-brand/5 to-brand/25" />
          )}

          <div className="px-6 pb-8 sm:px-10 sm:pb-10 lg:px-14">
            <div className="mx-auto max-w-5xl">
            {/* Avatar + Edit button */}
            <div className="flex items-end justify-between -mt-12 sm:-mt-14">
              <div className="relative h-24 w-24 sm:h-28 sm:w-28 overflow-hidden rounded-full ring-4 ring-background bg-muted shadow-md">
                {profile.avatarUrl ? (
                  <Image
                    src={profile.avatarUrl}
                    alt=""
                    width={128}
                    height={128}
                    className="h-full w-full object-cover"
                    unoptimized
                  />
                ) : (
                  <span className="flex h-full w-full items-center justify-center bg-linear-to-br from-brand/80 to-brand text-4xl sm:text-5xl font-bold text-brand-foreground select-none">
                    {profile.displayName[0]?.toUpperCase() ?? "?"}
                  </span>
                )}
              </div>
              <Link
                href="/profile/edit"
                className={cn(
                  buttonVariants({ variant: "outline", size: "sm" }),
                  "rounded-full gap-1.5 bg-background/60 backdrop-blur-sm shadow-sm hover:bg-background/90"
                )}
              >
                <Pencil className="size-3.5" />
                <span>Edit profile</span>
              </Link>
            </div>

            {/* Info */}
            <div className="mt-5 space-y-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  {profile.displayName}
                </h1>
                {joinDate && (
                  <p className="mt-1.5 flex items-center gap-1.5 text-sm text-muted-foreground">
                    <CalendarDays className="size-3.5" aria-hidden />
                    Joined {joinDate}
                  </p>
                )}
              </div>

              {profile.bio && (
                <p className="max-w-prose whitespace-pre-wrap text-sm leading-7 text-foreground/80">
                  {profile.bio}
                </p>
              )}

              {socialLinks.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {socialLinks.map(({ url, icon: Icon, label }) => (
                    <a
                      key={label}
                      href={url!}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-muted/40 px-3.5 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:border-border hover:bg-muted hover:text-foreground"
                    >
                      <Icon className="size-3.5" />
                      {label}
                    </a>
                  ))}
                </div>
              )}
            </div>
            </div>
          </div>
        </div>

        {/* ── Quick Actions ── */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <Link
            href="/bookmarks"
            className="group flex items-center gap-4 rounded-xl border border-border/80 bg-card p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-brand/25 hover:shadow-md"
          >
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent text-brand transition-colors group-hover:bg-brand/15">
              <Bookmark className="size-4" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground">Bookmarks</p>
              <p className="mt-0.5 text-xs text-muted-foreground">View saved posts</p>
            </div>
          </Link>
          <Link
            href="/blog/new"
            className="group flex items-center gap-4 rounded-xl border border-border/80 bg-card p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-brand/25 hover:shadow-md"
          >
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent text-brand transition-colors group-hover:bg-brand/15">
              <FileEdit className="size-4" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground">Write a post</p>
              <p className="mt-0.5 text-xs text-muted-foreground">Create new article</p>
            </div>
          </Link>
          <Link
            href="/profile/edit"
            className="group flex items-center gap-4 rounded-xl border border-border/80 bg-card p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:border-brand/25 hover:shadow-md"
          >
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent text-brand transition-colors group-hover:bg-brand/15">
              <Settings className="size-4" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground">Settings</p>
              <p className="mt-0.5 text-xs text-muted-foreground">Edit your profile</p>
            </div>
          </Link>
        </div>
      </div>
    </PublicPageShell>
  );
}
