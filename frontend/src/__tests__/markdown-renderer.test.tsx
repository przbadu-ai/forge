import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { MarkdownRenderer } from "@/components/chat/MarkdownRenderer";

describe("MarkdownRenderer", () => {
  it("renders plain text", () => {
    render(<MarkdownRenderer content="Hello world" />);
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("renders bold text as <strong>", () => {
    const { container } = render(
      <MarkdownRenderer content="This is **bold** text" />,
    );
    const strong = container.querySelector("strong");
    expect(strong).toBeInTheDocument();
    expect(strong?.textContent).toBe("bold");
  });

  it("renders code blocks with a pre element", () => {
    const { container } = render(
      <MarkdownRenderer content={'```python\nprint("hi")\n```'} />,
    );
    const pre = container.querySelector("pre");
    expect(pre).toBeInTheDocument();
    const code = container.querySelector("code");
    expect(code).toBeInTheDocument();
  });

  it("sanitizes HTML - no script tags rendered", () => {
    const { container } = render(
      <MarkdownRenderer content='<script>alert("xss")</script>' />,
    );
    // There should be no script elements in the DOM
    const scripts = container.querySelectorAll("script");
    expect(scripts.length).toBe(0);
    // The text "alert" should not be in any executable script
    expect(container.innerHTML).not.toContain("<script>");
  });

  it("renders inline code", () => {
    const { container } = render(
      <MarkdownRenderer content="Use `console.log()` here" />,
    );
    const code = container.querySelector("code");
    expect(code).toBeInTheDocument();
    expect(code?.textContent).toBe("console.log()");
  });

  it("renders links from markdown", () => {
    render(<MarkdownRenderer content="[Click here](https://example.com)" />);
    const link = screen.getByRole("link", { name: "Click here" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "https://example.com");
  });
});
