import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { McpServerRead } from "@/lib/mcp-api";

// ---------- Mocks (must be before component imports) ----------

const mockListMcpServers = vi.fn();
const mockCreateMcpServer = vi.fn();
const mockUpdateMcpServer = vi.fn();
const mockDeleteMcpServer = vi.fn();
const mockToggleMcpServer = vi.fn();

vi.mock("@/lib/mcp-api", () => ({
  listMcpServers: (...args: unknown[]) => mockListMcpServers(...args),
  createMcpServer: (...args: unknown[]) => mockCreateMcpServer(...args),
  updateMcpServer: (...args: unknown[]) => mockUpdateMcpServer(...args),
  deleteMcpServer: (...args: unknown[]) => mockDeleteMcpServer(...args),
  toggleMcpServer: (...args: unknown[]) => mockToggleMcpServer(...args),
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

import { McpServersSection } from "@/components/settings/mcp-servers-section";

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

const SAMPLE_SERVERS: McpServerRead[] = [
  {
    id: 1,
    name: "filesystem",
    command: "uvx",
    args: ["mcp-server-filesystem", "/home/user"],
    env_vars: {},
    is_enabled: true,
    transport_type: "stdio",
    url: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "github",
    command: "node",
    args: ["dist/index.js"],
    env_vars: { GITHUB_TOKEN: "ghp_xxx" },
    is_enabled: false,
    transport_type: "stdio",
    url: null,
    created_at: "2026-01-02T00:00:00Z",
  },
];

// ---------- Tests ----------

describe("McpServersSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty state when no servers", async () => {
    mockListMcpServers.mockResolvedValue([]);
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/no mcp servers yet/i)).toBeInTheDocument();
    });
  });

  it("renders server cards when servers exist", async () => {
    mockListMcpServers.mockResolvedValue(SAMPLE_SERVERS);
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("filesystem")).toBeInTheDocument();
    });
    expect(screen.getByText("github")).toBeInTheDocument();
  });

  it("shows enabled/disabled badges on server cards", async () => {
    mockListMcpServers.mockResolvedValue(SAMPLE_SERVERS);
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Enabled")).toBeInTheDocument();
    });
    expect(screen.getByText("Disabled")).toBeInTheDocument();
  });

  it("shows transport type badge on server cards", async () => {
    const serversWithTypes: McpServerRead[] = [
      { ...SAMPLE_SERVERS[0], transport_type: "stdio" },
      {
        id: 3,
        name: "remote-sse",
        command: null,
        args: [],
        env_vars: {},
        is_enabled: true,
        transport_type: "sse",
        url: "http://localhost:8080/sse",
        created_at: "2026-01-03T00:00:00Z",
      },
    ];
    mockListMcpServers.mockResolvedValue(serversWithTypes);
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("filesystem")).toBeInTheDocument();
    });
    expect(screen.getByText("stdio")).toBeInTheDocument();
    expect(screen.getByText("SSE")).toBeInTheDocument();
  });

  it("shows add form on Add MCP Server button click", async () => {
    mockListMcpServers.mockResolvedValue([]);
    const user = userEvent.setup();
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/no mcp servers yet/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /add mcp server/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/add mcp server/i, {
          selector: "[data-slot='card-title']",
        })
      ).toBeInTheDocument();
    });
  });

  it("shows URL field when transport type is sse", async () => {
    mockListMcpServers.mockResolvedValue([]);
    const user = userEvent.setup();
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/no mcp servers yet/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /add mcp server/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/add mcp server/i, {
          selector: "[data-slot='card-title']",
        })
      ).toBeInTheDocument();
    });

    // Initially should show Command field (stdio is default)
    expect(screen.getByLabelText(/command/i)).toBeInTheDocument();

    // Click SSE transport type
    await user.click(screen.getByRole("radio", { name: /sse/i }));

    // URL field should appear, Command should be hidden
    await waitFor(() => {
      expect(screen.getByLabelText(/server url/i)).toBeInTheDocument();
    });
    expect(screen.queryByLabelText(/command/i)).not.toBeInTheDocument();
  });

  it("renders toggle switches for each server", async () => {
    mockListMcpServers.mockResolvedValue(SAMPLE_SERVERS);
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("filesystem")).toBeInTheDocument();
    });

    const toggleButtons = screen.getAllByRole("switch");
    expect(toggleButtons.length).toBe(SAMPLE_SERVERS.length);
  });

  it("calls toggleMcpServer when toggle is clicked", async () => {
    mockListMcpServers.mockResolvedValue(SAMPLE_SERVERS);
    mockToggleMcpServer.mockResolvedValue({
      ...SAMPLE_SERVERS[0],
      is_enabled: false,
    });
    const user = userEvent.setup();
    render(<McpServersSection />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("filesystem")).toBeInTheDocument();
    });

    const toggleButtons = screen.getAllByRole("switch");
    await user.click(toggleButtons[0]);

    await waitFor(() => {
      expect(mockToggleMcpServer).toHaveBeenCalledWith("mock-token", 1);
    });
  });
});
