/**
 * Lightweight event tracking utility.
 *
 * Fires POST /api/track-event for custom user interactions.
 * This is a fire-and-forget helper — errors are silently caught.
 * Uses sessionStorage for session_id (shared with usePageView).
 */

function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let sid = sessionStorage.getItem("pv_session_id");
  if (!sid) {
    sid = crypto.randomUUID();
    sessionStorage.setItem("pv_session_id", sid);
  }
  return sid;
}

export type EventType = "click" | "share" | "comment" | "scroll";

const pendingEvents: Array<{ path: string; eventType: EventType; metadata?: string }> = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

function flushPending() {
  if (pendingEvents.length === 0) return;
  const batch = pendingEvents.splice(0);
  const sessionId = getSessionId();

  for (const evt of batch) {
    fetch("/api/track-event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: evt.path,
        event_type: evt.eventType,
        event_metadata: evt.metadata ?? null,
        session_id: sessionId,
      }),
    }).catch(() => {
      // Silently fail
    });
  }
}

/**
 * Track a user event. Events are batched and flushed every 2 seconds.
 */
export function trackEvent(eventType: EventType, metadata?: string) {
  if (typeof window === "undefined") return;

  pendingEvents.push({
    path: window.location.pathname,
    eventType,
    metadata,
  });

  if (!flushTimer) {
    flushTimer = setTimeout(() => {
      flushTimer = null;
      flushPending();
    }, 2000);
  }
}
