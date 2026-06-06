import Image from "next/image";
import Link from "next/link";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { Briefcase, Code, Globe } from "lucide-react";

import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { auth } from "@/lib/auth/server";
import { getFollowState, getPublicProfile } from "@/lib/user/profile";
import { FollowButton } from "./follow-button";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function PublicProfilePage({ params }: { params: Promise<{ userId: string }> }) {
  const { userId } = await params;
  const [profile, session] = await Promise.all([
    getPublicProfile(userId),
    auth.api.getSession({ headers: await headers() }),
  ]);
  if (!profile) notFound();
  const followState = session ? await getFollowState(session, userId).catch(() => undefined) : undefined;
  const isSelf = session?.user.id === userId;

  return (
    <PublicPageShell>
      <section className={cn(publicMainWidthClass, "flex flex-col gap-8 px-3 py-10 sm:px-0 sm:py-14")}>
        <PublicBackLink href="/blog">Blog</PublicBackLink>

        <div className="overflow-hidden rounded-[2rem] border border-border/80 bg-card shadow-sm">
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
            <div className="relative aspect-video max-h-[520px] bg-gradient-to-br from-brand/15 via-brand/5 to-brand/25" />
          )}

          <div className="px-6 pb-8 sm:px-10 sm:pb-10 lg:px-14">
            <div className="mx-auto max-w-5xl">
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
                  <span className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand/80 to-brand text-4xl sm:text-5xl font-bold text-brand-foreground select-none">
                    {profile.displayName[0]?.toUpperCase() ?? "?"}
                  </span>
                )}
              </div>
              {!isSelf &&
                (session ? (
                  <FollowButton userId={userId} isFollowing={Boolean(followState?.isFollowing)} />
                ) : (
                  <Link className={buttonVariants()} href="/login">
                    Sign in to follow
                  </Link>
                ))}
            </div>

            <div className="mt-5 space-y-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  {profile.displayName}
                </h1>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  {followState?.followerCount ?? 0} followers · {followState?.followingCount ?? 0} following
                </p>
              </div>

              {profile.bio && (
                <p className="max-w-prose whitespace-pre-wrap text-sm leading-7 text-foreground/80">
                  {profile.bio}
                </p>
              )}

              {(profile.websiteUrl || profile.githubUrl || profile.linkedinUrl) && (
                <div className="flex flex-wrap gap-2">
                  {profile.websiteUrl && (
                    <a
                      href={profile.websiteUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-muted/40 px-3.5 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:border-border hover:bg-muted hover:text-foreground"
                    >
                      <Globe className="size-3.5" />
                      Website
                    </a>
                  )}
                  {profile.githubUrl && (
                    <a
                      href={profile.githubUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-muted/40 px-3.5 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:border-border hover:bg-muted hover:text-foreground"
                    >
                      <Code className="size-3.5" />
                      GitHub
                    </a>
                  )}
                  {profile.linkedinUrl && (
                    <a
                      href={profile.linkedinUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-muted/40 px-3.5 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:border-border hover:bg-muted hover:text-foreground"
                    >
                      <Briefcase className="size-3.5" />
                      LinkedIn
                    </a>
                  )}
                </div>
              )}
            </div>
            </div>
          </div>
        </div>
      </section>
    </PublicPageShell>
  );
}
