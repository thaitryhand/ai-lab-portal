import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PublicBackLink } from "./public-back-link";

describe("PublicBackLink", () => {
  it("renders a link with the given href and children", () => {
    render(<PublicBackLink href="/blog">Back to Blog</PublicBackLink>);
    const link = screen.getByRole("link", { name: /back to blog/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/blog");
  });

  it("renders an icon", () => {
    render(<PublicBackLink href="/">Home</PublicBackLink>);
    const link = screen.getByRole("link");
    expect(link).toBeInTheDocument();
    // Should have an SVG icon (ArrowLeft)
    expect(link.querySelector("svg")).toBeInTheDocument();
  });
});
