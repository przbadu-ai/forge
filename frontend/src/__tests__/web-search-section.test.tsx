import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

// ---------- Mocks ----------

vi.mock("@/context/auth-context", () => ({
  useAuth: () => ({
    user: { id: 1, username: "admin", is_active: true, created_at: "" },
    token: "mock-token",
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

vi.mock("@/lib/web-search-api", () => ({
  getWebSearchSettings: vi.fn().mockResolvedValue({
    searxng_base_url: null,
    exa_api_key_set: false,
  }),
  updateWebSearchSettings: vi.fn().mockResolvedValue({
    searxng_base_url: "http://localhost:8888",
    exa_api_key_set: true,
  }),
}));

// ---------- Component imports ----------

import { WebSearchSection } from "@/components/settings/web-search-section";

// ---------- Tests ----------

describe("WebSearchSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders SearXNG URL input after loading", async () => {
    render(<WebSearchSection />);
    const input = await screen.findByLabelText(/searxng base url/i);
    expect(input).toBeInTheDocument();
  });

  it("renders Exa API key input", async () => {
    render(<WebSearchSection />);
    const input = await screen.findByLabelText(/exa api key/i);
    expect(input).toBeInTheDocument();
  });

  it("renders Save button", async () => {
    render(<WebSearchSection />);
    const saveBtn = await screen.findByRole("button", { name: /save/i });
    expect(saveBtn).toBeInTheDocument();
  });

  it("shows description text", async () => {
    render(<WebSearchSection />);
    const desc = await screen.findByText(/configure web search providers/i);
    expect(desc).toBeInTheDocument();
  });
});
