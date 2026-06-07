import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SkeletonCard, SkeletonCardGrid } from "./skeleton-card";

// Mock the Skeleton component since it uses cn (Tailwind)
vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={className} />
  ),
}));

describe("SkeletonCard", () => {
  it("renders skeleton placeholders", () => {
    const { container } = render(<SkeletonCard />);
    const skeletons = container.querySelectorAll('[data-testid="skeleton"]');
    expect(skeletons.length).toBe(4);
  });
});

describe("SkeletonCardGrid", () => {
  it("renders default count of skeleton cards", () => {
    render(<SkeletonCardGrid />);
    // Default count = 6, each card has 4 skeletons = 24 total
    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBe(24);
  });

  it("renders custom count of skeleton cards", () => {
    render(<SkeletonCardGrid count={3} />);
    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBe(12);
  });
});
