import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Avatar } from "./public-avatar";

describe("Avatar", () => {
  it("renders first letter when no image is provided", () => {
    render(<Avatar name="Alice" />);
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("renders initial from first letter of name", () => {
    render(<Avatar name="bob" />);
    expect(screen.getByText("B")).toBeInTheDocument();
  });

  it("renders fallback '?' when name is null", () => {
    render(<Avatar name={null} />);
    expect(screen.getByText("?")).toBeInTheDocument();
  });

  it("renders fallback '?' when name is empty", () => {
    render(<Avatar name="" />);
    expect(screen.getByText("?")).toBeInTheDocument();
  });

  it("renders image when src is provided", () => {
    const { container } = render(<Avatar src="/avatar.png" name="Alice" />);
    const img = container.querySelector("img");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/avatar.png");
    expect(img).toHaveAttribute("alt", "");
  });

  it("applies size class", () => {
    render(<Avatar name="Test" size="lg" />);
    const el = screen.getByText("T");
    expect(el.className).toContain("h-14");
    expect(el.className).toContain("w-14");
  });

  it("applies default size sm when not specified", () => {
    render(<Avatar name="Test" />);
    const el = screen.getByText("T");
    expect(el.className).toContain("h-8");
    expect(el.className).toContain("w-8");
  });
});
