"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Bell, Check, CheckCheck } from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

type NotificationSummary = {
  id: string;
  type: "follow" | "comment_reply" | "mention";
  actor_user_id: string;
  actor_email: string | null;
  actor_display_name: string | null;
  resource_id: string;
  resource_type: string;
  read: boolean;
  created_at: string;
};

const POLL_INTERVAL_MS = 30_000;

function timeAgo(createdAt: string): string {
  const now = Date.now();
  const diff = now - new Date(createdAt).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function typeLabel(type: string): string {
  switch (type) {
    case "follow":
      return "followed you";
    case "comment_reply":
      return "replied to your comment";
    case "mention":
      return "mentioned you";
    default:
      return type;
  }
}

export function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationSummary[]>([]);
  const [open, setOpen] = useState(false);
  const mountedRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchUnreadCount = useCallback(async () => {
    if (!mountedRef.current) return;
    try {
      const response = await fetch("/api/notifications?path=unread-count");
      if (response.ok) {
        const data = (await response.json()) as { count: number };
        if (mountedRef.current) setUnreadCount(data.count);
      }
    } catch {
      // ignore polling errors
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
    if (!mountedRef.current) return;
    try {
      const response = await fetch("/api/notifications");
      if (response.ok) {
        const data = (await response.json()) as NotificationSummary[];
        if (mountedRef.current) {
          setNotifications(data);
          setUnreadCount(data.filter((n) => !n.read).length);
        }
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchUnreadCount().catch(() => {});
    intervalRef.current = setInterval(() => {
      fetchUnreadCount().catch(() => {});
    }, POLL_INTERVAL_MS);
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchUnreadCount]);

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (isOpen) {
      fetchNotifications().catch(() => {});
    }
  };

  const handleMarkRead = async (notificationId: string) => {
    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: `${notificationId}/read`, method: "POST" }),
      });
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n)),
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await fetch("/api/notifications", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: "read-all", method: "POST" }),
      });
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch {
      // ignore
    }
  };

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
          className="relative inline-flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Bell className="size-4" aria-hidden />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0" sideOffset={8}>
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <span className="text-sm font-semibold">Notifications</span>
          {notifications.some((n) => !n.read) && (
            <button
              type="button"
              onClick={handleMarkAllRead}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <CheckCheck className="size-3" aria-hidden />
              Mark all read
            </button>
          )}
        </div>
        <div className="max-h-80 overflow-y-auto">
          {notifications.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">No notifications yet</p>
          ) : (
            notifications.map((notification) => (
              <button
                key={notification.id}
                type="button"
                onClick={() => !notification.read && handleMarkRead(notification.id)}
                className={cn(
                  "flex w-full items-start gap-3 border-b border-border px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-muted/50",
                  !notification.read && "bg-accent/30",
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                    notification.read ? "bg-muted" : "bg-brand/20",
                  )}
                >
                  {notification.read ? (
                    <Check className="size-3 text-muted-foreground" aria-hidden />
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-brand" aria-hidden />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className={cn("text-sm", !notification.read && "font-medium")}>
                    <span className="text-foreground">{notification.actor_display_name ?? notification.actor_email ?? "Someone"}</span>{" "}
                    <span className="text-muted-foreground">{typeLabel(notification.type)}</span>
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{timeAgo(notification.created_at)}</p>
                </div>
              </button>
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
