import { render } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock navigator.serviceWorker
const mockRegister = vi.fn(() => Promise.resolve({} as ServiceWorkerRegistration));

beforeEach(() => {
  vi.resetAllMocks();
  Object.defineProperty(navigator, "serviceWorker", {
    value: { register: mockRegister },
    writable: true,
    configurable: true,
  });
});

import { ServiceWorkerRegister } from "../components/sw-register";

describe("ServiceWorkerRegister", () => {
  it("renders null (no visible UI)", () => {
    const { container } = render(<ServiceWorkerRegister />);
    expect(container.innerHTML).toBe("");
  });

  it("registers /sw.js on mount", async () => {
    render(<ServiceWorkerRegister />);
    // useEffect runs asynchronously
    await vi.waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith("/sw.js", {
        scope: "/",
        updateViaCache: "none",
      });
    });
  });
});
