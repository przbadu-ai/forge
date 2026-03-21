"""Tests for TraceEmitter service."""

import json

from app.services.trace_emitter import TraceEmitter, TraceEvent


def test_trace_event_has_required_fields() -> None:
    """TraceEvent dataclass has all required fields."""
    event = TraceEvent(
        id="test-uuid",
        type="run_start",
        name="chat_turn",
        status="running",
        started_at="2026-01-01T00:00:00+00:00",
    )
    assert event.id == "test-uuid"
    assert event.type == "run_start"
    assert event.name == "chat_turn"
    assert event.status == "running"
    assert event.started_at == "2026-01-01T00:00:00+00:00"
    assert event.completed_at is None
    assert event.input is None
    assert event.output is None
    assert event.error is None
    assert event.metadata is None


def test_emitter_start_run() -> None:
    """start_run() creates a run_start event with status running."""
    emitter = TraceEmitter()
    event = emitter.start_run(name="chat_turn")

    assert event.type == "run_start"
    assert event.name == "chat_turn"
    assert event.status == "running"
    assert event.started_at is not None
    assert event.completed_at is None
    assert len(emitter.events) == 1


def test_emitter_end_run_success() -> None:
    """end_run(success=True) creates a completed run_end event."""
    emitter = TraceEmitter()
    emitter.start_run()
    event = emitter.end_run(success=True)

    assert event.type == "run_end"
    assert event.status == "completed"
    assert event.completed_at is not None
    assert len(emitter.events) == 2


def test_emitter_end_run_failure() -> None:
    """end_run(success=False) creates an error run_end event."""
    emitter = TraceEmitter()
    emitter.start_run()
    event = emitter.end_run(success=False)

    assert event.type == "run_end"
    assert event.status == "error"
    assert event.completed_at is not None


def test_emitter_emit_token_generation() -> None:
    """emit_token_generation() creates a completed token_generation event."""
    emitter = TraceEmitter()
    event = emitter.emit_token_generation(token_count=42)

    assert event.type == "token_generation"
    assert event.name == "token_generation"
    assert event.status == "completed"
    assert event.metadata is not None
    assert event.metadata["token_count"] == 42


def test_emitter_emit_error() -> None:
    """emit_error() creates an error event with error message."""
    emitter = TraceEmitter()
    event = emitter.emit_error("something broke")

    assert event.type == "error"
    assert event.name == "error"
    assert event.status == "error"
    assert event.error == "something broke"
    assert event.completed_at is not None


def test_emitter_to_json_produces_valid_json() -> None:
    """to_json() returns a valid JSON array of event dicts."""
    emitter = TraceEmitter()
    emitter.start_run(name="chat_turn")
    emitter.emit_token_generation(token_count=10)
    emitter.end_run(success=True)

    result = emitter.to_json()
    parsed = json.loads(result)

    assert isinstance(parsed, list)
    assert len(parsed) == 3
    assert parsed[0]["type"] == "run_start"
    assert parsed[1]["type"] == "token_generation"
    assert parsed[2]["type"] == "run_end"


def test_emitter_events_returns_copy() -> None:
    """events property returns a copy, not the internal list."""
    emitter = TraceEmitter()
    emitter.start_run()
    events = emitter.events
    events.clear()
    assert len(emitter.events) == 1


def test_emitter_event_ids_are_unique() -> None:
    """Each event gets a unique UUID id."""
    emitter = TraceEmitter()
    e1 = emitter.start_run()
    e2 = emitter.emit_token_generation(token_count=5)
    e3 = emitter.end_run()

    ids = {e1.id, e2.id, e3.id}
    assert len(ids) == 3


def test_full_trace_lifecycle() -> None:
    """Full lifecycle: start -> tokens -> end produces correct ordered trace."""
    emitter = TraceEmitter()
    emitter.start_run(name="chat_turn")
    emitter.emit_token_generation(token_count=100)
    emitter.end_run(success=True)

    trace = json.loads(emitter.to_json())
    assert [e["type"] for e in trace] == ["run_start", "token_generation", "run_end"]
    assert trace[0]["status"] == "running"
    assert trace[1]["status"] == "completed"
    assert trace[2]["status"] == "completed"
