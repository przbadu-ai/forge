import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock the auth context
const mockLogin = vi.fn();
vi.mock("@/context/auth-context", () => ({
  useAuth: () => ({
    login: mockLogin,
    token: null,
    user: null,
    isLoading: false,
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  useSearchParams: () => ({ get: () => null }),
}));

import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders username and password fields", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("calls login with entered credentials on submit", async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/username/i), "admin");
    await user.type(screen.getByLabelText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("admin", "secret");
    });
  });

  it("redirects to / on successful login", async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/username/i), "admin");
    await user.type(screen.getByLabelText(/password/i), "changeme");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/");
    });
  });

  it("shows error message on login failure", async () => {
    mockLogin.mockRejectedValueOnce(
      new Error("Incorrect username or password")
    );
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/username/i), "admin");
    await user.type(screen.getByLabelText(/password/i), "wrong");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Incorrect username or password"
      );
    });
  });

  it("disables submit button while login is pending", async () => {
    let resolveLogin!: () => void;
    mockLogin.mockReturnValueOnce(
      new Promise<void>((res) => {
        resolveLogin = res;
      })
    );
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/username/i), "admin");
    await user.type(screen.getByLabelText(/password/i), "changeme");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /signing in/i })
      ).toBeDisabled();
    });
    resolveLogin();
  });
});
