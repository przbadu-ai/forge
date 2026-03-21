import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { SourceCitations } from "@/components/chat/source-citations";
import type { SourceCitation } from "@/components/chat/source-citations";

const mockSources: SourceCitation[] = [
  {
    file_name: "report.pdf",
    chunk_text: "The quarterly results showed a 15% increase in revenue...",
    score: 0.92,
  },
  {
    file_name: "notes.txt",
    chunk_text: "Key takeaways from the meeting included...",
    score: 0.78,
  },
];

describe("SourceCitations", () => {
  it("renders nothing when sources are empty", () => {
    const { container } = render(<SourceCitations sources={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders source count button", () => {
    render(<SourceCitations sources={mockSources} />);
    expect(screen.getByText("2 sources")).toBeInTheDocument();
  });

  it("is collapsed by default", () => {
    render(<SourceCitations sources={mockSources} />);
    expect(screen.queryByText("report.pdf")).not.toBeInTheDocument();
  });

  it("expands when clicked", async () => {
    const user = userEvent.setup();
    render(<SourceCitations sources={mockSources} />);

    await user.click(screen.getByRole("button", { name: /toggle source citations/i }));

    expect(screen.getByText("report.pdf")).toBeInTheDocument();
    expect(screen.getByText("notes.txt")).toBeInTheDocument();
  });

  it("shows relevance scores", async () => {
    const user = userEvent.setup();
    render(<SourceCitations sources={mockSources} />);

    await user.click(screen.getByRole("button", { name: /toggle source citations/i }));

    expect(screen.getByText("92% match")).toBeInTheDocument();
    expect(screen.getByText("78% match")).toBeInTheDocument();
  });

  it("shows chunk preview text", async () => {
    const user = userEvent.setup();
    render(<SourceCitations sources={mockSources} />);

    await user.click(screen.getByRole("button", { name: /toggle source citations/i }));

    expect(
      screen.getByText(/The quarterly results showed/)
    ).toBeInTheDocument();
  });

  it("handles single source", () => {
    render(<SourceCitations sources={[mockSources[0]]} />);
    expect(screen.getByText("1 source")).toBeInTheDocument();
  });
});
