import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

const mockGetDiagnostics = vi.fn().mockResolvedValue({
  services: [
    { name: "LLM: Ollama", status: "ok", latency_ms: 42, error: null },
    { name: "Embedding Model", status: "unconfigured", latency_ms: null, error: null },
    { name: "ChromaDB", status: "error", latency_ms: null, error: "Connection refused" },
  ],
});

vi.mock("@/lib/diagnostics-api", () => ({
  getDiagnostics: (...args: unknown[]) => mockGetDiagnostics(...args),
}));

// ---------- Component imports ----------

import { HealthDiagnostics } from "@/components/settings/health-diagnostics";

// ---------- Tests ----------

describe("HealthDiagnostics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Check Now button", () => {
    render(<HealthDiagnostics />);
    expect(
      screen.getByRole("button", { name: /check now/i }),
    ).toBeInTheDocument();
  });

  it("shows services after clicking Check Now", async () => {
    const user = userEvent.setup();
    render(<HealthDiagnostics />);

    await user.click(screen.getByRole("button", { name: /check now/i }));

    expect(await screen.findByText("LLM: Ollama")).toBeInTheDocument();
    expect(screen.getByText("Embedding Model")).toBeInTheDocument();
    expect(screen.getByText("ChromaDB")).toBeInTheDocument();
  });

  it("shows error messages for failed services", async () => {
    const user = userEvent.setup();
    render(<HealthDiagnostics />);

    await user.click(screen.getByRole("button", { name: /check now/i }));

    expect(await screen.findByText("Connection refused")).toBeInTheDocument();
  });

  it("shows latency for healthy services", async () => {
    const user = userEvent.setup();
    render(<HealthDiagnostics />);

    await user.click(screen.getByRole("button", { name: /check now/i }));

    expect(await screen.findByText("42ms")).toBeInTheDocument();
  });

  it("shows 'Not configured' for unconfigured services", async () => {
    const user = userEvent.setup();
    render(<HealthDiagnostics />);

    await user.click(screen.getByRole("button", { name: /check now/i }));

    expect(await screen.findByText("Not configured")).toBeInTheDocument();
  });
});
