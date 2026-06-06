/** Query keys set by pipeline server actions for async job polling. */
export const OPERATIONAL_QUERY_KEYS = [
  "opStage",
  "opStatus",
  "taskId",
  "message",
] as const;

/** Build a URL without operational polling params (preserves e.g. blogSlug). */
export function urlWithoutOperationalQuery(pathname: string, search: string): string {
  const params = new URLSearchParams(search.replace(/^\?/, ""));
  for (const key of OPERATIONAL_QUERY_KEYS) {
    params.delete(key);
  }
  const qs = params.toString();
  return qs ? `${pathname}?${qs}` : pathname;
}
