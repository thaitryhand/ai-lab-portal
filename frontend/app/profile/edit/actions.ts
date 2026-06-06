"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth/server";
import { updateMyProfile } from "@/lib/user/profile";

function optionalString(formData: FormData, key: string): string | null {
  const value = formData.get(key);
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export async function updateProfileAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");

  await updateMyProfile(session, {
    displayName: optionalString(formData, "displayName") ?? undefined,
    bio: optionalString(formData, "bio"),
    avatarUrl: optionalString(formData, "avatarUrl"),
    coverUrl: optionalString(formData, "coverUrl"),
    websiteUrl: optionalString(formData, "websiteUrl"),
    githubUrl: optionalString(formData, "githubUrl"),
    linkedinUrl: optionalString(formData, "linkedinUrl"),
  });
  redirect("/profile?profileUpdated=1");
}
