import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { TracePanel } from "@/components/chat/TracePanel";
import type { TraceEvent } from "@/types/chat";

// ---------- Fixtures ----------

const runStartEvent: TraceEvent = {
  id: "evt-1",
  type: "run_start",
  name: "chat_turn",
  status: "running",
  started_at: "2026-03-21T10:00:00.000Z",
  completed_at: null,
};

const tokenEvent: TraceEvent = {
  id: "evt-2",
  type: "token_generation",
  name: "token_generation",
  status: "completed",
  started_at: "2026-03-21T10:00:00.010Z",
  completed_at: "2026-03-21T10:00:01.500Z",
};

const runEndEvent: TraceEvent = {
  id: "evt-3",
  type: "run_end",
  name: "run_end",
  status: "completed",
  started_at: "2026-03-21T10:00:01.500Z",
  completed_at: "2026-03-21T10:00:01.500Z",
};

const errorEvent: TraceEvent = {
  id: "evt-4",
  type: "error",
  name: "error",
  status: "error",
  started_at: "2026-03-21T10:00:00.000Z",
  completed_at: "2026-03-21T10:00:00.100Z",
  error: "LLM connection failed",
};

const sampleEvents: TraceEvent[] = [runStartEvent, tokenEvent, runEndEvent];

// ---------- Tests ----------

describe("TracePanel", () => {
  it("renders collapsed by default", () => {
    render(<TracePanel events={sampleEvents} />);

    // The "Execution Trace" button should be visible
    expect(screen.getByText("Execution Trace")).toBeInTheDocument();

    // Event names should NOT be visible (collapsed)
    expect(screen.queryByText("chat_turn")).not.toBeInTheDocument();
    expect(screen.queryByText("token_generation")).not.toBeInTheDocument();
  });

  it("shows event count badge", () => {
    render(<TracePanel events={sampleEvents} />);

    // Badge shows the count of events
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("expands on click to show event names", async () => {
    const user = userEvent.setup();
    render(<TracePanel events={sampleEvents} />);

    // Click to expand
    await user.click(screen.getByText("Execution Trace"));

    // Event names should now be visible
    expect(screen.getByText("chat_turn")).toBeInTheDocument();
    expect(screen.getByText("token_generation")).toBeInTheDocument();
    expect(screen.getByText("run_end")).toBeInTheDocument();
  });

  it("shows status badges when expanded", async () => {
    const user = userEvent.setup();
    render(<TracePanel events={sampleEvents} />);

    await user.click(screen.getByText("Execution Trace"));

    // Status text should appear
    expect(screen.getByText("running")).toBeInTheDocument();
    // "completed" appears for both tokenEvent and runEndEvent
    expect(screen.getAllByText("completed")).toHaveLength(2);
  });

  it("shows error message for error events", async () => {
    const user = userEvent.setup();
    render(<TracePanel events={[errorEvent]} />);

    await user.click(screen.getByText("Execution Trace"));

    expect(screen.getByText("LLM connection failed")).toBeInTheDocument();
  });

  it("renders without crash when events is empty", () => {
    const { container } = render(<TracePanel events={[]} />);

    // Empty events + no streaming = renders null
    expect(container.firstChild).toBeNull();
  });

  it("shows streaming indicator when isStreaming is true", async () => {
    const user = userEvent.setup();
    render(<TracePanel events={sampleEvents} isStreaming />);

    await user.click(screen.getByText("Execution Trace"));

    expect(screen.getByText("Recording...")).toBeInTheDocument();
  });

  it("collapses again on second click", async () => {
    const user = userEvent.setup();
    render(<TracePanel events={sampleEvents} />);

    // Expand
    await user.click(screen.getByText("Execution Trace"));
    expect(screen.getByText("chat_turn")).toBeInTheDocument();

    // Collapse
    await user.click(screen.getByText("Execution Trace"));
    expect(screen.queryByText("chat_turn")).not.toBeInTheDocument();
  });
});
