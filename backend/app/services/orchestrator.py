"""Orchestrator service — while-loop: LLM call -> tool dispatch -> feed results -> repeat."""

import asyncio
import dataclasses
import json
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI

from app.services.executors.builtin_tools import BUILTIN_TOOL_SCHEMAS
from app.services.executors.registry import ExecutorRegistry
from app.services.run_state import RunStateStore, RunStatus
from app.services.trace_emitter import TraceEmitter


class Orchestrator:
    """Agentic orchestration loop that dispatches tool calls and feeds results back to the LLM."""

    def __init__(
        self,
        registry: ExecutorRegistry,
        tracer: TraceEmitter,
        run_store: RunStateStore,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_iterations: int = 10,
    ) -> None:
        self.registry = registry
        self.tracer = tracer
        self.run_store = run_store
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_iterations = max_iterations
        self._final_content: str = ""

    @property
    def final_content(self) -> str:
        """The final text content produced by the orchestration run."""
        return self._final_content

    def _sse(self, data: dict[str, Any]) -> str:
        """Format a dict as an SSE data line."""
        return f"data: {json.dumps(data)}\n\n"

    async def _llm_call_with_retry(
        self,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Call the LLM with retry and exponential backoff on timeout."""
        delays = [1.0, 2.0, 4.0]
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if tools:
                    kwargs["tools"] = tools

                response = await asyncio.wait_for(
                    client.chat.completions.create(**kwargs),
                    timeout=self.timeout,
                )
                return response
            except TimeoutError as e:
                last_error = e
                if attempt < self.max_retries:
                    await asyncio.sleep(delays[attempt] if attempt < len(delays) else delays[-1])
                continue

        # All retries exhausted
        raise last_error  # type: ignore[misc]

    async def run(
        self,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """Run the orchestration loop, yielding SSE-formatted strings."""
        run_state = self.run_store.create()
        run_id = run_state.run_id
        self.run_store.update_status(run_id, RunStatus.RUNNING)

        current_messages: list[dict[str, Any]] = list(messages)
        iteration = 0

        try:
            while iteration < self.max_iterations:
                self.run_store.increment_iteration(run_id)
                iteration += 1

                # Determine tools to pass: only on first iterations where tool calls are possible
                tools = BUILTIN_TOOL_SCHEMAS if self.registry.available_tools() else None

                try:
                    response = await self._llm_call_with_retry(
                        client, model, current_messages, temperature, max_tokens, tools=tools
                    )
                except TimeoutError:
                    error_msg = f"Timeout after {self.timeout}s on LLM call"
                    error_event = self.tracer.emit_error(error_msg)
                    yield self._sse(
                        {"type": "trace_event", "event": dataclasses.asdict(error_event)}
                    )
                    self.run_store.update_status(run_id, RunStatus.FAILED, error=error_msg)
                    yield self._sse({"type": "error", "message": error_msg})
                    return

                choice = response.choices[0]
                finish_reason = choice.finish_reason

                if finish_reason == "tool_calls" or (
                    hasattr(choice.message, "tool_calls")
                    and choice.message.tool_calls
                    and finish_reason != "stop"
                ):
                    # Append the assistant message with tool calls to history
                    assistant_msg: dict[str, Any] = {
                        "role": "assistant",
                        "content": choice.message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in choice.message.tool_calls
                        ],
                    }
                    current_messages.append(assistant_msg)

                    # Process each tool call
                    for tc in choice.message.tool_calls:
                        tool_name = tc.function.name
                        try:
                            tool_input = json.loads(tc.function.arguments)
                        except (json.JSONDecodeError, TypeError):
                            tool_input = {}

                        # Emit tool_start trace event
                        start_event = self.tracer.emit_tool_start(tool_name, tool_input)
                        yield self._sse(
                            {"type": "trace_event", "event": dataclasses.asdict(start_event)}
                        )

                        # Dispatch to executor with timeout
                        try:
                            result = await asyncio.wait_for(
                                self.registry.dispatch(tool_name, tool_input),
                                timeout=self.timeout,
                            )
                        except TimeoutError:
                            error_msg = f"Timeout after {self.timeout}s on tool: {tool_name}"
                            end_event = self.tracer.emit_tool_end(tool_name, None, error=error_msg)
                            yield self._sse(
                                {"type": "trace_event", "event": dataclasses.asdict(end_event)}
                            )
                            error_trace = self.tracer.emit_error(error_msg)
                            yield self._sse(
                                {"type": "trace_event", "event": dataclasses.asdict(error_trace)}
                            )
                            self.run_store.update_status(run_id, RunStatus.FAILED, error=error_msg)
                            yield self._sse({"type": "error", "message": error_msg})
                            return
                        except KeyError:
                            error_msg = f"No executor registered for tool: {tool_name}"
                            end_event = self.tracer.emit_tool_end(tool_name, None, error=error_msg)
                            yield self._sse(
                                {"type": "trace_event", "event": dataclasses.asdict(end_event)}
                            )
                            # Append error result to messages so LLM can recover
                            current_messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "content": json.dumps({"error": error_msg}),
                                }
                            )
                            continue

                        # Emit tool_end trace event
                        if result.error:
                            end_event = self.tracer.emit_tool_end(
                                tool_name, result.output, error=result.error
                            )
                        else:
                            end_event = self.tracer.emit_tool_end(tool_name, result.output)
                        yield self._sse(
                            {"type": "trace_event", "event": dataclasses.asdict(end_event)}
                        )

                        # Append tool result to messages
                        tool_output = (
                            result.output if result.error is None else {"error": result.error}
                        )
                        current_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": (
                                    json.dumps(tool_output)
                                    if not isinstance(tool_output, str)
                                    else tool_output
                                ),
                            }
                        )

                    # Continue the loop for next LLM call
                    continue

                else:
                    # Text response — final answer
                    content = choice.message.content or ""
                    self._final_content = content

                    # Yield content as a single token chunk
                    if content:
                        yield self._sse({"type": "token", "delta": content})

                    # Emit token generation trace
                    token_event = self.tracer.emit_token_generation(token_count=len(content))
                    yield self._sse(
                        {"type": "trace_event", "event": dataclasses.asdict(token_event)}
                    )

                    self.run_store.update_status(run_id, RunStatus.COMPLETED)
                    return

            # Max iterations exceeded
            error_msg = "max_iterations_exceeded"
            self.run_store.update_status(run_id, RunStatus.FAILED, error=error_msg)
            error_event = self.tracer.emit_error(error_msg)
            yield self._sse({"type": "trace_event", "event": dataclasses.asdict(error_event)})
            yield self._sse({"type": "error", "message": error_msg})

        except Exception as e:
            error_msg = str(e)
            error_event = self.tracer.emit_error(error_msg)
            yield self._sse({"type": "trace_event", "event": dataclasses.asdict(error_event)})
            self.run_store.update_status(run_id, RunStatus.FAILED, error=error_msg)
            yield self._sse({"type": "error", "message": error_msg})
