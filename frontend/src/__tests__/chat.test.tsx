import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ---------- Mocks (must be before component imports) ----------

const mockGetConversations = vi.fn();
const mockCreateConversation = vi.fn();
const mockRenameConversation = vi.fn();
const mockDeleteConversation = vi.fn();

vi.mock("@/lib/chat-api", () => ({
  getConversations: (...args: unknown[]) => mockGetConversations(...args),
  createConversation: (...args: unknown[]) => mockCreateConversation(...args),
  renameConversation: (...args: unknown[]) => mockRenameConversation(...args),
  deleteConversation: (...args: unknown[]) => mockDeleteConversation(...args),
  getMessages: vi.fn().mockResolvedValue([]),
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

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// ---------- Component imports (after mocks) ----------

import { ConversationList } from "@/components/chat/ConversationList";
import { ChatInput } from "@/components/chat/ChatInput";
import { MessageBubble } from "@/components/chat/MessageBubble";

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

// ---------- ConversationList Tests ----------

describe("ConversationList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders conversations from API", async () => {
    mockGetConversations.mockResolvedValue([
      {
        id: 1,
        title: "Chat about React",
        user_id: 1,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
      {
        id: 2,
        title: "Python discussion",
        user_id: 1,
        created_at: "2026-01-02T00:00:00Z",
        updated_at: "2026-01-02T00:00:00Z",
      },
    ]);

    render(<ConversationList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Chat about React")).toBeInTheDocument();
    });
    expect(screen.getByText("Python discussion")).toBeInTheDocument();
  });

  it("shows empty state when no conversations", async () => {
    mockGetConversations.mockResolvedValue([]);

    render(<ConversationList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/no conversations yet/i)).toBeInTheDocument();
    });
  });

  it("renders New Chat button", async () => {
    mockGetConversations.mockResolvedValue([]);

    render(<ConversationList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /new chat/i }),
      ).toBeInTheDocument();
    });
  });
});

// ---------- ChatInput Tests ----------

describe("ChatInput", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls onSend with text on Enter key", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/type a message/i);
    await user.type(textarea, "Hello world");
    await user.keyboard("{Enter}");

    expect(onSend).toHaveBeenCalledWith("Hello world");
  });

  it("does not send on Shift+Enter (adds newline instead)", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/type a message/i);
    await user.type(textarea, "Line one");
    await user.keyboard("{Shift>}{Enter}{/Shift}");

    expect(onSend).not.toHaveBeenCalled();
  });

  it("does not send when disabled", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} disabled />);

    const textarea = screen.getByPlaceholderText(/type a message/i);
    // textarea is disabled, so type won't work - verify the state
    expect(textarea).toBeDisabled();
  });

  it("clears input after sending", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(
      /type a message/i,
    ) as HTMLTextAreaElement;
    await user.type(textarea, "Hello");
    await user.keyboard("{Enter}");

    expect(textarea.value).toBe("");
  });

  it("does not send empty messages", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByPlaceholderText(/type a message/i);
    await user.click(textarea);
    await user.keyboard("{Enter}");

    expect(onSend).not.toHaveBeenCalled();
  });
});

// ---------- MessageBubble Tests ----------

describe("MessageBubble", () => {
  it("renders user message with user styling", () => {
    const { container } = render(
      <MessageBubble role="user" content="Hello from user" />,
    );
    expect(screen.getByText("Hello from user")).toBeInTheDocument();
    // User messages are right-aligned
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("justify-end");
  });

  it("renders assistant message with assistant styling", () => {
    const { container } = render(
      <MessageBubble role="assistant" content="Hello from assistant" />,
    );
    expect(screen.getByText("Hello from assistant")).toBeInTheDocument();
    // Assistant messages are left-aligned
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("justify-start");
  });

  it("shows streaming cursor when isStreaming is true", () => {
    const { container } = render(
      <MessageBubble role="assistant" content="Streaming..." isStreaming />,
    );
    // The streaming cursor is a span with animate-pulse
    const cursor = container.querySelector(".animate-pulse");
    expect(cursor).toBeInTheDocument();
  });

  it("does not show streaming cursor when isStreaming is false", () => {
    const { container } = render(
      <MessageBubble role="assistant" content="Done" isStreaming={false} />,
    );
    const cursor = container.querySelector(".animate-pulse");
    expect(cursor).not.toBeInTheDocument();
  });

  it("renders user messages as plain text (no markdown)", () => {
    const { container } = render(
      <MessageBubble role="user" content="**bold text**" />,
    );
    // User messages use <p> not markdown renderer, so no <strong>
    const paragraph = container.querySelector("p");
    expect(paragraph).toBeInTheDocument();
    expect(paragraph?.textContent).toBe("**bold text**");
  });
});
