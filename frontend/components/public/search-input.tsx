"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useRef, useState } from "react";

interface SearchInputProps {
  /** Placeholder text */
  placeholder?: string;
  /** Query param name, defaults to "q" */
  paramName?: string;
  /** Debounce delay in ms */
  debounce?: number;
  /** Optional label for screen readers */
  label?: string;
}

export function SearchInput({
  placeholder = "Search…",
  paramName = "q",
  debounce = 300,
  label = "Search",
}: SearchInputProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialValue = searchParams.get(paramName) ?? "";
  const [value, setValue] = useState(initialValue);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setValue(newValue);

      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        const params = new URLSearchParams(searchParams.toString());
        if (newValue) {
          params.set(paramName, newValue);
        } else {
          params.delete(paramName);
        }
        const qs = params.toString();
        router.push(qs ? `?${qs}` : window.location.pathname, { scroll: false });
      }, debounce);
    },
    [router, searchParams, paramName, debounce],
  );

  const handleClear = useCallback(() => {
    setValue("");
    const params = new URLSearchParams(searchParams.toString());
    params.delete(paramName);
    const qs = params.toString();
    router.push(qs ? `?${qs}` : window.location.pathname, { scroll: false });
  }, [router, searchParams, paramName]);

  return (
    <div className="relative w-full max-w-md">
      <label htmlFor={`search-${paramName}`} className="sr-only">
        {label}
      </label>
      <input
        id={`search-${paramName}`}
        type="search"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        className="w-full rounded-lg border border-zinc-200 bg-white px-4 py-2.5 pl-10 text-sm text-zinc-900 placeholder-zinc-400 transition-colors focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-500 dark:focus:ring-zinc-700"
      />
      {/* Search icon */}
      <svg
        className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zinc-400 dark:text-zinc-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
        />
      </svg>
      {/* Clear button */}
      {value && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
          aria-label="Clear search"
        >
          <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
