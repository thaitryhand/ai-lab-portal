import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, act } from "@testing-library/react";
import { ReadingProgress } from "./reading-progress";

describe("ReadingProgress", () => {
  beforeEach(() => {
    // Set up a predictable document height
    Object.defineProperty(document.documentElement, "scrollHeight", {
      value: 2000,
      writable: true,
    });
    Object.defineProperty(window, "innerHeight", {
      value: 1000,
      writable: true,
    });
    window.scrollY = 0;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders a progress bar with aria attributes", () => {
    const { getByRole } = render(<ReadingProgress />);
    const bar = getByRole("progressbar", { name: /reading progress/i });
    expect(bar).toBeInTheDocument();
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("starts at 0% progress", () => {
    const { getByRole } = render(<ReadingProgress />);
    const bar = getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "0");
    expect(bar).toHaveStyle({ width: "0%" });
  });

  it("updates progress on scroll", () => {
    const { getByRole } = render(<ReadingProgress />);
    const bar = getByRole("progressbar");

    act(() => {
      window.scrollY = 500;
      window.dispatchEvent(new Event("scroll"));
    });

    // docHeight = 2000 - 1000 = 1000
    // progress = 500 / 1000 * 100 = 50
    expect(bar).toHaveAttribute("aria-valuenow", "50");
    expect(bar).toHaveStyle({ width: "50%" });
  });

  it("caps at 100% progress", () => {
    const { getByRole } = render(<ReadingProgress />);
    const bar = getByRole("progressbar");

    act(() => {
      window.scrollY = 2000;
      window.dispatchEvent(new Event("scroll"));
    });

    expect(Number(bar.getAttribute("aria-valuenow"))).toBeLessThanOrEqual(100);
  });

  it("stays at 0% for zero-height document", () => {
    Object.defineProperty(document.documentElement, "scrollHeight", {
      value: 1000,
      writable: true,
    });

    const { getByRole } = render(<ReadingProgress />);
    const bar = getByRole("progressbar");

    act(() => {
      window.scrollY = 100;
      window.dispatchEvent(new Event("scroll"));
    });

    // docHeight = 1000 - 1000 = 0, so progress stays 0
    expect(bar).toHaveAttribute("aria-valuenow", "0");
  });

  it("removes scroll listener on unmount", () => {
    const removeSpy = vi.spyOn(window, "removeEventListener");
    const { unmount } = render(<ReadingProgress />);
    unmount();
    expect(removeSpy).toHaveBeenCalledWith("scroll", expect.any(Function));
  });
});
