"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type UserSession = {
  user: {
    id: string;
    name: string;
    email: string;
    image?: string | null;
  };
} | null;

type ViewerProfile = {
  userId: string;
  displayName: string;
  avatarUrl: string | null;
  coverUrl: string | null;
} | null;

type SessionContextValue = {
  session: UserSession;
  /** True only while the initial session fetch is in-flight (first mount). */
  loading: boolean;
  profile: ViewerProfile;
  profileLoading: boolean;
  avatarUrl: string | null;
  /** Force a session re-fetch, e.g. after sign-in / sign-out. */
  refresh: () => Promise<void>;
  /** Force a profile re-fetch, e.g. after editing avatar/profile. */
  refreshProfile: () => Promise<void>;
};

type NotificationsContextValue = {
  unreadCount: number;
  refreshUnreadCount: () => Promise<void>;
  setUnreadCount: (updater: number | ((current: number) => number)) => void;
};

const SessionContext = createContext<SessionContextValue | null>(null);
const NotificationsContext = createContext<NotificationsContextValue | null>(null);
const AVATAR_CACHE_PREFIX = "ai-lab-profile-avatar:";
const POLL_INTERVAL_MS = 30_000;

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within <SessionProvider>");
  return ctx;
}

export function useNotifications(): NotificationsContextValue {
  const ctx = useContext(NotificationsContext);
  if (!ctx) throw new Error("useNotifications must be used within <SessionProvider>");
  return ctx;
}

function readCachedAvatar(userId: string): string | null {
  try {
    return window.localStorage.getItem(`${AVATAR_CACHE_PREFIX}${userId}`);
  } catch {
    return null;
  }
}

function writeCachedAvatar(userId: string, avatarUrl: string | null) {
  try {
    const key = `${AVATAR_CACHE_PREFIX}${userId}`;
    if (avatarUrl) window.localStorage.setItem(key, avatarUrl);
    else window.localStorage.removeItem(key);
  } catch {
    // ignore storage errors
  }
}

/**
 * Central viewer state for the public shell.
 *
 * Split session/profile/avatar from notification unread state so notification
 * polling does not re-render the avatar menu every 30 seconds.
 */
export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<UserSession>(null);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<ViewerProfile>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [cachedAvatarUrl, setCachedAvatarUrl] = useState<string | null>(null);
  const [notificationUnreadCount, setNotificationUnreadCount] = useState(0);

  const fetchSession = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/auth/get-session", { cache: "no-store" });
      if (res.ok) {
        const data: UserSession = await res.json();
        setSession(data);
      } else {
        setSession(null);
        setProfile(null);
        setCachedAvatarUrl(null);
        setNotificationUnreadCount(0);
      }
    } catch {
      setSession(null);
      setProfile(null);
      setCachedAvatarUrl(null);
      setNotificationUnreadCount(0);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!session) {
      setProfile(null);
      setCachedAvatarUrl(null);
      return;
    }

    setProfileLoading(true);
    setCachedAvatarUrl(readCachedAvatar(session.user.id));
    try {
      const response = await fetch("/api/profile/me", { cache: "no-store" });
      if (!response.ok) return;
      const data = (await response.json()) as { profile?: ViewerProfile };
      const nextProfile = data.profile ?? null;
      setProfile(nextProfile);
      writeCachedAvatar(session.user.id, nextProfile?.avatarUrl ?? null);
      setCachedAvatarUrl(nextProfile?.avatarUrl ?? null);
    } catch {
      // Keep cached avatar instead of flashing back to initials.
    } finally {
      setProfileLoading(false);
    }
  }, [session]);

  const refreshNotificationUnreadCount = useCallback(async () => {
    if (!session) {
      setNotificationUnreadCount(0);
      return;
    }

    try {
      const response = await fetch("/api/notifications?path=unread-count", { cache: "no-store" });
      if (!response.ok) return;
      const data = (await response.json()) as { count: number };
      setNotificationUnreadCount(data.count);
    } catch {
      // ignore polling errors
    }
  }, [session]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchSession();
  }, [fetchSession]);

  useEffect(() => {
    if (!session) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setProfile(null);
      setCachedAvatarUrl(null);
      setNotificationUnreadCount(0);
      return;
    }

    setCachedAvatarUrl(readCachedAvatar(session.user.id));
    refreshProfile();
    refreshNotificationUnreadCount();
  }, [session, refreshProfile, refreshNotificationUnreadCount]);

  useEffect(() => {
    if (!session) return;
    const intervalId = setInterval(() => {
      refreshNotificationUnreadCount();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(intervalId);
  }, [session, refreshNotificationUnreadCount]);

  const avatarUrl = profile?.avatarUrl ?? cachedAvatarUrl ?? session?.user.image ?? null;

  const sessionValue = useMemo<SessionContextValue>(
    () => ({
      session,
      loading,
      profile,
      profileLoading,
      avatarUrl,
      refresh: fetchSession,
      refreshProfile,
    }),
    [session, loading, profile, profileLoading, avatarUrl, fetchSession, refreshProfile],
  );

  const notificationsValue = useMemo<NotificationsContextValue>(
    () => ({
      unreadCount: notificationUnreadCount,
      refreshUnreadCount: refreshNotificationUnreadCount,
      setUnreadCount: setNotificationUnreadCount,
    }),
    [notificationUnreadCount, refreshNotificationUnreadCount],
  );

  return (
    <SessionContext.Provider value={sessionValue}>
      <NotificationsContext.Provider value={notificationsValue}>
        {children}
      </NotificationsContext.Provider>
    </SessionContext.Provider>
  );
}
