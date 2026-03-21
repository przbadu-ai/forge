import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FileUpload } from "@/components/chat/file-upload";

// Mock useAuth
vi.mock("@/context/auth-context", () => ({
  useAuth: () => ({ token: "test-token" }),
}));

describe("FileUpload", () => {
  it("renders upload area", () => {
    render(<FileUpload />);
    expect(
      screen.getByText(/Drag and drop a file, or click to browse/)
    ).toBeInTheDocument();
  });

  it("shows supported file types", () => {
    render(<FileUpload />);
    expect(screen.getByText(/Supported: PDF, DOCX, TXT, MD/)).toBeInTheDocument();
  });

  it("has a choose file button", () => {
    render(<FileUpload />);
    expect(screen.getByRole("button", { name: /choose file/i })).toBeInTheDocument();
  });

  it("has a hidden file input", () => {
    render(<FileUpload />);
    const input = screen.getByLabelText("Upload file");
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("type", "file");
  });
});
