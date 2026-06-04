"use server";

import { headers } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth/server";
import { followUser, unfollowUser } from "@/lib/user/profile";

export async function followProfileAction(userId: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect(`/login`);
  await followUser(session, userId);
  revalidatePath(`/profiles/${userId}`);
}

export async function unfollowProfileAction(userId: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect(`/login`);
  await unfollowUser(session, userId);
  revalidatePath(`/profiles/${userId}`);
}
