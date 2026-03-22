import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

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

vi.mock("@/lib/settings-api", () => ({
  getGeneralSettings: vi.fn().mockResolvedValue({
    system_prompt: "You are helpful.",
    temperature: 0.7,
    max_tokens: 4096,
    skill_directories: [],
  }),
  updateGeneralSettings: vi.fn().mockResolvedValue({
    system_prompt: "You are helpful.",
    temperature: 0.7,
    max_tokens: 4096,
    skill_directories: [],
  }),
}));

// ---------- Component imports ----------

import { GeneralSection } from "@/components/settings/GeneralSection";

// ---------- Helpers ----------

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ---------- Tests ----------

describe("GeneralSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders system prompt textarea after loading", async () => {
    render(<GeneralSection />, { wrapper: createWrapper() });

    // Wait for loading to finish
    const textarea = await screen.findByLabelText(/system prompt/i);
    expect(textarea).toBeInTheDocument();
  });

  it("renders temperature slider", async () => {
    render(<GeneralSection />, { wrapper: createWrapper() });

    const slider = await screen.findByLabelText(/temperature/i);
    expect(slider).toBeInTheDocument();
  });

  it("renders max tokens input", async () => {
    render(<GeneralSection />, { wrapper: createWrapper() });

    const input = await screen.findByLabelText(/max tokens/i);
    expect(input).toBeInTheDocument();
  });

  it("renders Save button", async () => {
    render(<GeneralSection />, { wrapper: createWrapper() });

    const saveBtn = await screen.findByRole("button", { name: /save/i });
    expect(saveBtn).toBeInTheDocument();
  });
});
