import { createUserBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type Session = { user: { id: string; email: string } };

export type FollowState = {
  userId: string;
  followerCount: number;
  followingCount: number;
  isFollowing: boolean;
};

export type UserProfile = {
  userId: string;
  displayName: string;
  bio: string | null;
  avatarUrl: string | null;
  websiteUrl: string | null;
  githubUrl: string | null;
  linkedinUrl: string | null;
  createdAt: string;
  updatedAt: string;
};

type ApiFollowState = {
  user_id: string;
  follower_count: number;
  following_count: number;
  is_following: boolean;
};

type ApiUserProfile = {
  user_id: string;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  website_url: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  created_at: string;
  updated_at: string;
};

function toFollowState(state: ApiFollowState): FollowState {
  return {
    userId: state.user_id,
    followerCount: state.follower_count,
    followingCount: state.following_count,
    isFollowing: state.is_following,
  };
}

function toProfile(profile: ApiUserProfile): UserProfile {
  return {
    userId: profile.user_id,
    displayName: profile.display_name,
    bio: profile.bio,
    avatarUrl: profile.avatar_url,
    websiteUrl: profile.website_url,
    githubUrl: profile.github_url,
    linkedinUrl: profile.linkedin_url,
    createdAt: profile.created_at,
    updatedAt: profile.updated_at,
  };
}

async function callUser<T>(session: Session, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${backendBaseUrl}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...createUserBoundaryHeaders(session),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`User profile API failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export async function getMyProfile(session: Session): Promise<UserProfile> {
  return toProfile(await callUser<ApiUserProfile>(session, "/public/profile/me"));
}

export async function updateMyProfile(session: Session, payload: Partial<Pick<UserProfile, "displayName" | "bio" | "avatarUrl" | "websiteUrl" | "githubUrl" | "linkedinUrl">>): Promise<UserProfile> {
  return toProfile(
    await callUser<ApiUserProfile>(session, "/public/profile/me", {
      method: "PATCH",
      body: JSON.stringify({
        display_name: payload.displayName,
        bio: payload.bio,
        avatar_url: payload.avatarUrl,
        website_url: payload.websiteUrl,
        github_url: payload.githubUrl,
        linkedin_url: payload.linkedinUrl,
      }),
    }),
  );
}

export async function getPublicProfile(userId: string): Promise<UserProfile | undefined> {
  const response = await fetch(`${backendBaseUrl}/public/profiles/${userId}`, { cache: "no-store" });
  if (response.status === 404) return undefined;
  if (!response.ok) throw new Error(`Failed to fetch profile: ${response.status}`);
  return toProfile((await response.json()) as ApiUserProfile);
}

export async function getFollowState(session: Session, userId: string): Promise<FollowState> {
  return toFollowState(await callUser<ApiFollowState>(session, `/public/profiles/${userId}/follow-state`));
}

export async function followUser(session: Session, userId: string): Promise<FollowState> {
  return toFollowState(await callUser<ApiFollowState>(session, `/public/profiles/${userId}/follow`, { method: "POST" }));
}

export async function unfollowUser(session: Session, userId: string): Promise<FollowState> {
  return toFollowState(await callUser<ApiFollowState>(session, `/public/profiles/${userId}/follow`, { method: "DELETE" }));
}
