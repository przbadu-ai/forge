import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ProviderRead } from "@/lib/providers-api";

// ---------- Mocks (must be before component imports) ----------

const mockListProviders = vi.fn();
const mockCreateProvider = vi.fn();
const mockDeleteProvider = vi.fn();
const mockTestConnection = vi.fn();

vi.mock("@/lib/providers-api", () => ({
  listProviders: (...args: unknown[]) => mockListProviders(...args),
  createProvider: (...args: unknown[]) => mockCreateProvider(...args),
  updateProvider: vi.fn(),
  deleteProvider: (...args: unknown[]) => mockDeleteProvider(...args),
  testConnection: (...args: unknown[]) => mockTestConnection(...args),
}));

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

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// ---------- Component import (after mocks) ----------

import { ProvidersSection } from "@/components/settings/providers-section";

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

const SAMPLE_PROVIDERS: ProviderRead[] = [
  {
    id: 1,
    name: "Ollama",
    base_url: "http://localhost:11434/v1",
    models: ["llama3", "mistral"],
    is_default: true,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "OpenAI",
    base_url: "https://api.openai.com/v1",
    models: ["gpt-4"],
    is_default: false,
    created_at: "2026-01-02T00:00:00Z",
  },
];

// ---------- Tests ----------

describe("ProvidersSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty state when no providers", async () => {
    mockListProviders.mockResolvedValue([]);
    render(<ProvidersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/no providers yet/i)).toBeInTheDocument();
    });
  });

  it("renders provider cards when providers exist", async () => {
    mockListProviders.mockResolvedValue(SAMPLE_PROVIDERS);
    render(<ProvidersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Ollama")).toBeInTheDocument();
    });
    expect(screen.getByText("OpenAI")).toBeInTheDocument();
  });

  it("shows add form on Add Provider button click", async () => {
    mockListProviders.mockResolvedValue([]);
    const user = userEvent.setup();
    render(<ProvidersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/no providers yet/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /add provider/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/add provider/i, {
          selector: "[data-slot='card-title']",
        })
      ).toBeInTheDocument();
    });
  });

  it("renders Add Provider button in non-empty state", async () => {
    mockListProviders.mockResolvedValue(SAMPLE_PROVIDERS);
    render(<ProvidersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /add provider/i })
      ).toBeInTheDocument();
    });
  });
});
