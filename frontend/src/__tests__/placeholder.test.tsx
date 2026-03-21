import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

const mockReplace = vi.fn();

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
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
  it("redirects to /chat", () => {
    render(<HomePage />);
    expect(mockReplace).toHaveBeenCalledWith("/chat");
  });
});
