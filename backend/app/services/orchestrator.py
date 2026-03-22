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
        extra_tool_schemas: list[dict[str, Any]] | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_iterations: int = 10,
    ) -> None:
        self.registry = registry
        self.tracer = tracer
        self.run_store = run_store
        self.extra_tool_schemas = extra_tool_schemas or []
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

    def _build_tool_schemas(self) -> list[dict[str, Any]] | None:
        """Build the combined list of tool schemas (builtin + MCP/extra)."""
        if not self.registry.available_tools():
            return None
        schemas = list(BUILTIN_TOOL_SCHEMAS) + list(self.extra_tool_schemas)
        return schemas if schemas else None

    async def _llm_stream_with_retry(
        self,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Call the LLM with stream=True and retry with exponential backoff on timeout."""
        delays = [1.0, 2.0, 4.0]
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
                if tools:
                    kwargs["tools"] = tools

                stream = await asyncio.wait_for(
                    client.chat.completions.create(**kwargs),
                    timeout=self.timeout,
                )
                return stream
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

                # Build combined tool schemas (builtin + MCP/extra)
                tools = self._build_tool_schemas()

                try:
                    stream = await self._llm_stream_with_retry(
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

                # Consume the stream, accumulating content and tool calls
                content = ""
                finish_reason: str | None = None
                # tool_calls_acc: dict of index -> {id, function: {name, arguments}}
                tool_calls_acc: dict[int, dict[str, Any]] = {}

                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    chunk_finish = chunk.choices[0].finish_reason

                    if chunk_finish:
                        finish_reason = chunk_finish

                    # Accumulate text content and yield tokens immediately
                    if delta.content:
                        content += delta.content
                        yield self._sse({"type": "token", "delta": delta.content})

                    # Accumulate tool call deltas
                    if delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in tool_calls_acc:
                                tool_calls_acc[idx] = {
                                    "id": tc_delta.id or "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            acc = tool_calls_acc[idx]
                            if tc_delta.id:
                                acc["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    acc["function"]["name"] += tc_delta.function.name
                                if tc_delta.function.arguments:
                                    acc["function"]["arguments"] += tc_delta.function.arguments

                # Decide path based on accumulated result
                has_tool_calls = bool(tool_calls_acc)

                if has_tool_calls and finish_reason != "stop":
                    # Tool calls path — dispatch tools and loop
                    tool_calls_list = [tool_calls_acc[i] for i in sorted(tool_calls_acc)]
                    assistant_msg: dict[str, Any] = {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": tool_calls_list,
                    }
                    current_messages.append(assistant_msg)

                    # Process each tool call
                    for tc in tool_calls_list:
                        tool_name = tc["function"]["name"]
                        try:
                            tool_input = json.loads(tc["function"]["arguments"])
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
                                    "tool_call_id": tc["id"],
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
                                "tool_call_id": tc["id"],
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
                    # Text response — final answer (tokens already yielded above)
                    self._final_content = content

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
