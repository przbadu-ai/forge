import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock auth context
vi.mock("@/context/auth-context", () => ({
  useAuth: () => ({
    user: { id: 1, username: "admin", is_active: true, created_at: "" },
    token: "mock-token",
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

import HomePage from "../app/(protected)/page";

describe("Home page", () => {
  it("renders the Forge heading", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { name: /forge/i })).toBeInTheDocument();
  });

  it("shows the signed-in username", () => {
    render(<HomePage />);
    expect(screen.getByText(/signed in as admin/i)).toBeInTheDocument();
  });

  it("renders a sign out button", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("button", { name: /sign out/i })
    ).toBeInTheDocument();
  });
});
