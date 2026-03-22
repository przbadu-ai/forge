import asyncio
import dataclasses
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import Column, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse, StreamingResponse

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.core.encryption import decrypt_value
from app.models.conversation import Conversation
from app.models.llm_provider import LLMProvider
from app.models.mcp_server import McpServer
from app.models.message import Message
from app.models.settings import AppSettings
from app.models.skill import Skill
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.services.executors import ExecutorRegistry, SkillExecutor, ToolExecutor
from app.services.executors.builtin_tools import BUILTIN_TOOLS
from app.services.executors.mcp_executor import discover_and_register_mcp_tools
from app.services.orchestrator import Orchestrator
from app.services.retrieval_service import format_context_for_prompt, retrieve
from app.services.run_state import RunStateStore
from app.services.trace_emitter import TraceEmitter

router = APIRouter(dependencies=[Depends(get_current_user)])

# SQLAlchemy column references for ordering (mypy can't resolve SQLModel field descriptors)
_conv_updated_at: Column[Any] = Conversation.updated_at  # type: ignore[assignment]
_msg_created_at: Column[Any] = Message.created_at  # type: ignore[assignment]
_msg_content: Column[Any] = Message.content  # type: ignore[assignment]


# ---------- Schemas ----------


class ConversationCreate(BaseModel):
    title: str | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class ConversationRead(BaseModel):
    id: int
    title: str
    user_id: int
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    created_at: datetime
    updated_at: datetime


class ConversationUpdate(BaseModel):
    title: str | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class SourceInfo(BaseModel):
    file_name: str
    chunk_text: str
    score: float


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    trace_data: str | None = None
    sources: list[SourceInfo] | None = None
    created_at: datetime


class ChatStreamRequest(BaseModel):
    content: str  # user message text


# ---------- Helpers ----------


def _conv_to_read(c: Conversation) -> ConversationRead:
    return ConversationRead(
        id=c.id,
        title=c.title,
        user_id=c.user_id,
        system_prompt=c.system_prompt,
        temperature=c.temperature,
        max_tokens=c.max_tokens,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


async def _get_owned_conversation(
    conversation_id: int,
    user_id: int | None,
    session: AsyncSession,
) -> Conversation:
    """Fetch a conversation owned by the user, or raise 404."""
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,  # type: ignore[arg-type]
            Conversation.user_id == user_id,  # type: ignore[arg-type]
        )
    )
    conversation = result.scalars().first()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


async def _get_app_settings(session: AsyncSession) -> AppSettings:
    """Fetch global app settings row, or return defaults."""
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        return AppSettings()
    return settings


# ---------- CRUD Endpoints ----------


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationRead]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)  # type: ignore[arg-type]
        .order_by(_conv_updated_at.desc())
    )
    conversations = result.scalars().all()
    return [_conv_to_read(c) for c in conversations]


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationRead:
    conversation = Conversation(
        title=data.title or "New Conversation",
        user_id=current_user.id,
        system_prompt=data.system_prompt,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return _conv_to_read(conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MessageRead]:
    await _get_owned_conversation(conversation_id, current_user.id, session)

    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)  # type: ignore[arg-type]
        .order_by(_msg_created_at.asc())
    )
    messages = result.scalars().all()
    return [
        MessageRead(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            trace_data=m.trace_data,
            sources=json.loads(m.source_data) if m.source_data else None,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.put("/conversations/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationRead:
    conversation = await _get_owned_conversation(conversation_id, current_user.id, session)

    if data.title is not None:
        conversation.title = data.title
    if data.system_prompt is not None:
        conversation.system_prompt = data.system_prompt
    if data.temperature is not None:
        conversation.temperature = data.temperature
    if data.max_tokens is not None:
        conversation.max_tokens = data.max_tokens

    conversation.updated_at = datetime.now(UTC)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return _conv_to_read(conversation)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    conversation = await _get_owned_conversation(conversation_id, current_user.id, session)

    # Delete messages first (cascade manually for SQLite compatibility)
    await session.execute(
        delete(Message).where(Message.conversation_id == conversation_id)  # type: ignore[arg-type]
    )
    await session.delete(conversation)
    await session.commit()


# ---------- SSE Streaming Endpoint ----------


async def _token_generator(
    messages: list[dict[str, str]],
    base_url: str,
    api_key: str,
    model: str,
    conversation_id: int,
    session: AsyncSession,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncGenerator[str, None]:
    full_content = ""
    sources_data: list[dict[str, Any]] = []
    tracer = TraceEmitter()
    run_event = tracer.start_run(name="chat_turn")
    yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(run_event)})}\n\n"

    try:
        # Prepend system prompt if set
        openai_messages: list[dict[str, Any]] = list(messages)
        if system_prompt:
            openai_messages.insert(0, {"role": "system", "content": system_prompt})

        # RAG: check if user has uploaded files and retrieve relevant context
        file_result = await session.execute(
            select(UploadedFile).where(
                UploadedFile.status == "ready",  # type: ignore[arg-type]
            )
        )
        ready_files = list(file_result.scalars().all())

        if ready_files:
            # Get the user's latest message for retrieval query
            user_query = messages[-1]["content"] if messages else ""
            if user_query:
                app_settings_result = await session.execute(select(AppSettings))
                app_settings_row = app_settings_result.scalars().first()
                emb_base = app_settings_row.embedding_base_url if app_settings_row else None
                emb_model = app_settings_row.embedding_model if app_settings_row else None

                sources_data = await retrieve(
                    query=user_query,
                    top_k=5,
                    embedding_base_url=emb_base,
                    embedding_model=emb_model,
                )

                if sources_data:
                    # Build file name mapping
                    file_names: dict[int, str] = {
                        f.id: f.original_name for f in ready_files if f.id is not None
                    }
                    rag_context = format_context_for_prompt(sources_data, file_names)

                    # Inject RAG context into system message
                    if openai_messages and openai_messages[0]["role"] == "system":
                        openai_messages[0]["content"] += "\n\n" + rag_context
                    else:
                        openai_messages.insert(0, {"role": "system", "content": rag_context})

                    # Emit retrieval trace event
                    retrieval_event = tracer.emit_tool_start(
                        "rag_retrieval",
                        {"query": user_query[:100], "sources_found": len(sources_data)},
                    )
                    yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(retrieval_event)})}\n\n"
                    retrieval_end = tracer.emit_tool_end(
                        "rag_retrieval",
                        {"sources": len(sources_data)},
                    )
                    yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(retrieval_end)})}\n\n"

        client = AsyncOpenAI(base_url=base_url, api_key=api_key or "no-key")

        # Set up executor registry with built-in tools
        registry = ExecutorRegistry()
        tool_executor = ToolExecutor()
        for tool_name in BUILTIN_TOOLS:
            registry.register(tool_name, tool_executor)

        # Discover and register MCP tools from enabled servers
        from app.main import mcp_process_manager

        mcp_result = await session.execute(select(McpServer))
        mcp_servers = list(mcp_result.scalars().all())
        mcp_tool_schemas = await discover_and_register_mcp_tools(
            servers=mcp_servers,
            registry=registry,
            process_manager=mcp_process_manager,
            tracer=tracer,
        )

        # Register enabled skills
        skill_result = await session.execute(
            select(Skill).where(Skill.is_enabled == True)  # type: ignore[arg-type]  # noqa: E712
        )
        enabled_skills = list(skill_result.scalars().all())
        if enabled_skills:
            skill_executor = SkillExecutor(tracer=tracer)
            for skill in enabled_skills:
                registry.register(skill.name, skill_executor)

        orchestrator = Orchestrator(
            registry=registry,
            tracer=tracer,
            run_store=RunStateStore(),
            extra_tool_schemas=mcp_tool_schemas,
        )
        async for sse_line in orchestrator.run(
            client=client,
            model=model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield sse_line

        full_content = orchestrator.final_content

        # Emit run completion trace
        end_event = tracer.end_run(success=True)
        yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(end_event)})}\n\n"

        # Build sources metadata for persistence
        sources_meta: list[dict[str, Any]] = []
        if sources_data:
            file_names_map: dict[int, str] = {}
            for f in ready_files:
                if f.id is not None:
                    file_names_map[f.id] = f.original_name
            for src in sources_data:
                fid = src.get("file_id")
                sources_meta.append(
                    {
                        "file_name": file_names_map.get(fid, f"File {fid}") if fid else "Unknown",
                        "chunk_text": (src.get("chunk_text", ""))[:200],
                        "score": src.get("score", 0.0),
                    }
                )

        # After orchestrator completes, persist assistant message with trace data
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,
            trace_data=tracer.to_json(),
            source_data=json.dumps(sources_meta) if sources_meta else None,
        )
        session.add(assistant_msg)
        await session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)  # type: ignore[arg-type]
            .values(updated_at=datetime.now(UTC))
        )
        await session.commit()
        await session.refresh(assistant_msg)

        done_data: dict[str, Any] = {"type": "done", "message_id": assistant_msg.id}
        if sources_meta:
            done_data["sources"] = sources_meta
        yield f"data: {json.dumps(done_data)}\n\n"
    except (asyncio.CancelledError, GeneratorExit):
        # Client disconnected -- save partial content if any was received
        tracer.end_run(success=False)
        if full_content:
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_content,
                trace_data=tracer.to_json(),
            )
            session.add(assistant_msg)
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)  # type: ignore[arg-type]
                .values(updated_at=datetime.now(UTC))
            )
            await session.commit()
            await session.refresh(assistant_msg)
            yield f"data: {json.dumps({'type': 'stopped', 'message_id': assistant_msg.id})}\n\n"
    except Exception as e:
        # Emit error and end trace events
        error_event = tracer.emit_error(str(e))
        yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(error_event)})}\n\n"
        end_event = tracer.end_run(success=False)
        yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(end_event)})}\n\n"

        # Save partial content on error too
        if full_content:
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_content,
                trace_data=tracer.to_json(),
            )
            session.add(assistant_msg)
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)  # type: ignore[arg-type]
                .values(updated_at=datetime.now(UTC))
            )
            await session.commit()
            await session.refresh(assistant_msg)
            yield f"data: {json.dumps({'type': 'stopped', 'message_id': assistant_msg.id})}\n\n"
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/{conversation_id}/stream")
async def stream_chat(
    conversation_id: int,
    data: ChatStreamRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    conversation = await _get_owned_conversation(conversation_id, current_user.id, session)

    # Persist user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=data.content,
    )
    session.add(user_msg)
    await session.flush()

    # Check if this is the first message -- auto-title
    count_result = await session.execute(
        select(func.count()).where(
            Message.conversation_id == conversation_id  # type: ignore[arg-type]
        )
    )
    msg_count = count_result.scalar_one()
    if msg_count == 1:
        conversation.title = data.content[:50].strip()
        conversation.updated_at = datetime.now(UTC)

    await session.commit()

    # Fetch default LLM provider
    provider_result = await session.execute(
        select(LLMProvider).where(
            LLMProvider.is_default == True  # type: ignore[arg-type]  # noqa: E712
        )
    )
    provider = provider_result.scalars().first()
    if provider is None:

        async def _error_gen() -> AsyncGenerator[str, None]:
            yield (
                "data: "
                + json.dumps({"type": "error", "message": "No default LLM provider configured"})
                + "\n\n"
            )

        return StreamingResponse(
            _error_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Decrypt API key
    api_key = decrypt_value(provider.api_key_encrypted) if provider.api_key_encrypted else ""

    # Parse models list to get first model
    models_list: list[str] = json.loads(provider.models) if provider.models else []
    model_name = models_list[0] if models_list else "default"

    # Build conversation history for openai
    history_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)  # type: ignore[arg-type]
        .order_by(_msg_created_at.asc())
    )
    history = history_result.scalars().all()
    openai_messages = [{"role": m.role, "content": m.content} for m in history]

    # Resolve effective settings (conversation override > global)
    app_settings = await _get_app_settings(session)
    effective_system_prompt = conversation.system_prompt or app_settings.system_prompt
    effective_temperature = (
        conversation.temperature
        if conversation.temperature is not None
        else app_settings.temperature
    )
    effective_max_tokens = (
        conversation.max_tokens if conversation.max_tokens is not None else app_settings.max_tokens
    )

    return StreamingResponse(
        _token_generator(
            messages=openai_messages,
            base_url=provider.base_url,
            api_key=api_key,
            model=model_name,
            conversation_id=conversation_id,
            session=session,
            system_prompt=effective_system_prompt,
            temperature=effective_temperature,
            max_tokens=effective_max_tokens,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------- Regenerate Endpoint ----------


@router.post("/{conversation_id}/regenerate")
async def regenerate(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    await _get_owned_conversation(conversation_id, current_user.id, session)

    # Find last message
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)  # type: ignore[arg-type]
        .order_by(_msg_created_at.desc())
        .limit(1)
    )
    last_msg = result.scalars().first()

    if last_msg is None or last_msg.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assistant message to regenerate",
        )

    await session.delete(last_msg)
    await session.commit()
    return {"status": "ok"}


# ---------- Export Endpoint ----------


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    conversation = await _get_owned_conversation(conversation_id, current_user.id, session)

    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)  # type: ignore[arg-type]
        .order_by(_msg_created_at.asc())
    )
    messages = result.scalars().all()

    export_data = {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "trace_data": json.loads(m.trace_data) if m.trace_data else None,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }

    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="conversation-{conversation_id}.json"'
        },
    )


# ---------- Search Endpoint ----------


@router.get("/search", response_model=list[ConversationRead])
async def search_conversations(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationRead]:
    pattern = f"%{q}%"
    result = await session.execute(
        select(Conversation)
        .join(Message, Message.conversation_id == Conversation.id)  # type: ignore[arg-type]
        .where(
            Conversation.user_id == current_user.id,  # type: ignore[arg-type]
            _msg_content.like(pattern),
        )
        .distinct()
        .order_by(_conv_updated_at.desc())
    )
    conversations = result.scalars().all()
    return [_conv_to_read(c) for c in conversations]
