import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PublicEmptyState } from "./public-empty-state";

describe("PublicEmptyState", () => {
  it("renders title and description", () => {
    render(
      <PublicEmptyState
        title="No articles found"
        description="Try adjusting your search."
      />,
    );
    expect(screen.getByText("No articles found")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your search.")).toBeInTheDocument();
  });

  it("renders default file icon", () => {
    const { container } = render(
      <PublicEmptyState title="Empty" description="Nothing here yet." />,
    );
    // Default icon is FileText from lucide-react (renders as SVG)
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("accepts custom icon", () => {
    render(
      <PublicEmptyState
        title="Custom"
        description="Custom icon"
        icon={<span data-testid="custom-icon">🔍</span>}
      />,
    );
    expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
  });
});
