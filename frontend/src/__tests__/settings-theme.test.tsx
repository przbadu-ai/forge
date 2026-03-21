import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";

// ---------- Mocks ----------

const mockSetTheme = vi.fn();

vi.mock("next-themes", () => ({
  useTheme: () => ({
    theme: "light",
    setTheme: mockSetTheme,
  }),
}));

// ---------- Component import (after mocks) ----------

import { ThemeSwitcher } from "@/components/settings/theme-switcher";

// ---------- Tests ----------

describe("ThemeSwitcher", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Light, Dark, and System buttons", () => {
    render(<ThemeSwitcher />);
    expect(screen.getByRole("button", { name: /light/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /dark/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /system/i })).toBeInTheDocument();
  });

  it("calls setTheme with 'dark' when Dark button clicked", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher />);
    await user.click(screen.getByRole("button", { name: /dark/i }));
    expect(mockSetTheme).toHaveBeenCalledWith("dark");
  });

  it("calls setTheme with 'system' when System button clicked", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher />);
    await user.click(screen.getByRole("button", { name: /system/i }));
    expect(mockSetTheme).toHaveBeenCalledWith("system");
  });

  it("has aria-pressed on the active theme button", () => {
    render(<ThemeSwitcher />);
    const lightBtn = screen.getByRole("button", { name: /light/i });
    expect(lightBtn).toHaveAttribute("aria-pressed", "true");

    const darkBtn = screen.getByRole("button", { name: /dark/i });
    expect(darkBtn).toHaveAttribute("aria-pressed", "false");
  });
});
