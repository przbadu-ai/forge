import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import OfflinePage from "../app/~offline/page";

describe("Offline fallback page", () => {
  it("renders 'You are offline' heading", () => {
    render(<OfflinePage />);
    expect(screen.getByText("You are offline")).toBeDefined();
  });

  it("renders a Retry button", () => {
    render(<OfflinePage />);
    const button = screen.getByRole("button", { name: /retry/i });
    expect(button).toBeDefined();
  });

  it("uses only inline styles (no className attributes)", () => {
    const { container } = render(<OfflinePage />);
    const allElements = container.querySelectorAll("*");
    for (const el of allElements) {
      expect(el.className).toBe("");
    }
  });

  it("contains Forge branding SVG", () => {
    const { container } = render(<OfflinePage />);
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
