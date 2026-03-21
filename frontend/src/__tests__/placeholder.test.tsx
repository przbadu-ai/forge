import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Home from "../app/page";

describe("Home page", () => {
  it("renders the Forge heading", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /forge/i })).toBeInTheDocument();
  });
});
