import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { SkillRead } from "@/lib/skills-api";

// ---------- Mocks (must be before component imports) ----------

const mockListSkills = vi.fn();
const mockToggleSkill = vi.fn();
const mockCreateSkill = vi.fn();
const mockDeleteSkill = vi.fn();
const mockSyncSkills = vi.fn();

vi.mock("@/lib/skills-api", () => ({
  listSkills: (...args: unknown[]) => mockListSkills(...args),
  toggleSkill: (...args: unknown[]) => mockToggleSkill(...args),
  createSkill: (...args: unknown[]) => mockCreateSkill(...args),
  deleteSkill: (...args: unknown[]) => mockDeleteSkill(...args),
  syncSkills: (...args: unknown[]) => mockSyncSkills(...args),
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

import { SkillsSection } from "@/components/settings/skills-section";

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

const SAMPLE_SKILLS: SkillRead[] = [
  {
    id: 1,
    name: "web_search",
    description: "Search the web for current information",
    is_enabled: true,
    config: null,
    source_path: null,
    content: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "code_execution",
    description: "Execute code snippets in a sandboxed environment",
    is_enabled: false,
    config: null,
    source_path: null,
    content: null,
    created_at: "2026-01-02T00:00:00Z",
  },
];

// ---------- Tests ----------

describe("SkillsSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty state when no skills", async () => {
    mockListSkills.mockResolvedValue([]);
    render(<SkillsSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/no skills available/i)).toBeInTheDocument();
    });
  });

  it("renders skill list with names and descriptions", async () => {
    mockListSkills.mockResolvedValue(SAMPLE_SKILLS);
    render(<SkillsSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("web_search")).toBeInTheDocument();
    });
    expect(screen.getByText("code_execution")).toBeInTheDocument();
    expect(
      screen.getByText("Search the web for current information")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Execute code snippets in a sandboxed environment")
    ).toBeInTheDocument();
  });

  it("renders toggle switches for each skill", async () => {
    mockListSkills.mockResolvedValue(SAMPLE_SKILLS);
    render(<SkillsSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("web_search")).toBeInTheDocument();
    });

    const toggleSwitches = screen.getAllByRole("switch");
    expect(toggleSwitches.length).toBe(SAMPLE_SKILLS.length);
  });

  it("calls toggleSkill API when toggle is clicked", async () => {
    mockListSkills.mockResolvedValue(SAMPLE_SKILLS);
    mockToggleSkill.mockResolvedValue({
      ...SAMPLE_SKILLS[0],
      is_enabled: false,
    });
    const user = userEvent.setup();
    render(<SkillsSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("web_search")).toBeInTheDocument();
    });

    const toggleSwitches = screen.getAllByRole("switch");
    await user.click(toggleSwitches[0]);

    await waitFor(() => {
      expect(mockToggleSkill).toHaveBeenCalledWith("mock-token", 1);
    });
  });

  it("shows error state when API fails", async () => {
    mockListSkills.mockRejectedValue(new Error("Network error"));
    render(<SkillsSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/failed to load skills/i)).toBeInTheDocument();
    });
  });
});
