/**
 * Safe fetch wrapper that returns null on network errors instead of throwing.
 * Use this in all admin server components to gracefully handle backend unavailability.
 */
export async function safeFetch<T>(
  url: string,
  options?: RequestInit,
): Promise<T | null> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}
