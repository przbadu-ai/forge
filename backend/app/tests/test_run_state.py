"""Unit tests for RunState lifecycle transitions."""

import uuid

from app.services.run_state import RunStateStore, RunStatus


def test_create_returns_created_state() -> None:
    """create() returns RunState with status=CREATED and a valid UUID run_id."""
    store = RunStateStore()
    state = store.create()

    assert state.status == RunStatus.CREATED
    # Verify it's a valid UUID
    uuid.UUID(state.run_id)
    assert state.iteration == 0
    assert state.error is None


def test_update_status_to_running() -> None:
    """update_status(run_id, RUNNING) changes status to RUNNING."""
    store = RunStateStore()
    state = store.create()

    store.update_status(state.run_id, RunStatus.RUNNING)
    updated = store.get(state.run_id)

    assert updated is not None
    assert updated.status == RunStatus.RUNNING


def test_update_status_to_failed_with_error() -> None:
    """update_status(run_id, FAILED, error='boom') sets status=FAILED and error='boom'."""
    store = RunStateStore()
    state = store.create()

    store.update_status(state.run_id, RunStatus.FAILED, error="boom")
    updated = store.get(state.run_id)

    assert updated is not None
    assert updated.status == RunStatus.FAILED
    assert updated.error == "boom"


def test_increment_iteration() -> None:
    """increment_iteration(run_id) increments iteration counter from 0 to 1."""
    store = RunStateStore()
    state = store.create()
    assert state.iteration == 0

    store.increment_iteration(state.run_id)
    updated = store.get(state.run_id)

    assert updated is not None
    assert updated.iteration == 1


def test_get_unknown_id_returns_none() -> None:
    """get(unknown_id) returns None."""
    store = RunStateStore()
    result = store.get("nonexistent-id")
    assert result is None


def test_delete_then_get_returns_none() -> None:
    """delete(run_id) then get(run_id) returns None."""
    store = RunStateStore()
    state = store.create()
    run_id = state.run_id

    store.delete(run_id)
    assert store.get(run_id) is None


def test_multiple_concurrent_states_independent() -> None:
    """Multiple concurrent RunStates don't interfere with each other."""
    store = RunStateStore()
    state1 = store.create()
    state2 = store.create()

    store.update_status(state1.run_id, RunStatus.RUNNING)
    store.update_status(state2.run_id, RunStatus.FAILED, error="err")

    s1 = store.get(state1.run_id)
    s2 = store.get(state2.run_id)

    assert s1 is not None
    assert s1.status == RunStatus.RUNNING
    assert s1.error is None

    assert s2 is not None
    assert s2.status == RunStatus.FAILED
    assert s2.error == "err"
