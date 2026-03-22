import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

vi.mock("@/lib/skills-api", () => ({
  listSkills: () => Promise.resolve([]),
}));

// ---------- Component imports ----------

import { ChatInput } from "@/components/chat/ChatInput";

// ---------- Helpers ----------

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ---------- Tests ----------

describe("ChatInput — streaming toggle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Send button when isStreaming=false", () => {
    render(<ChatInput onSend={vi.fn()} isStreaming={false} />, {
      wrapper: createWrapper(),
    });

    expect(
      screen.getByRole("button", { name: /send message/i })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /stop generation/i })
    ).not.toBeInTheDocument();
  });

  it("renders Stop button when isStreaming=true", () => {
    render(<ChatInput onSend={vi.fn()} isStreaming={true} onStop={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    expect(
      screen.getByRole("button", { name: /stop generation/i })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /send message/i })
    ).not.toBeInTheDocument();
  });

  it("calls onStop when Stop button is clicked", async () => {
    const onStop = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={vi.fn()} isStreaming={true} onStop={onStop} />, {
      wrapper: createWrapper(),
    });

    const stopBtn = screen.getByRole("button", { name: /stop generation/i });
    await user.click(stopBtn);

    expect(onStop).toHaveBeenCalledOnce();
  });

  it("renders Send button by default (no isStreaming prop)", () => {
    render(<ChatInput onSend={vi.fn()} />, { wrapper: createWrapper() });

    expect(
      screen.getByRole("button", { name: /send message/i })
    ).toBeInTheDocument();
  });
});
