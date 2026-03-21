import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk
from pydantic import BaseModel
from sqlalchemy import Column, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.core.encryption import decrypt_value
from app.models.conversation import Conversation
from app.models.llm_provider import LLMProvider
from app.models.message import Message
from app.models.user import User

router = APIRouter(dependencies=[Depends(get_current_user)])

# SQLAlchemy column references for ordering (mypy can't resolve SQLModel field descriptors)
_conv_updated_at: Column[Any] = Conversation.updated_at  # type: ignore[assignment]
_msg_created_at: Column[Any] = Message.created_at  # type: ignore[assignment]


# ---------- Schemas ----------


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationRead(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime
    updated_at: datetime


class ConversationUpdate(BaseModel):
    title: str


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


class ChatStreamRequest(BaseModel):
    content: str  # user message text


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
    return [
        ConversationRead(
            id=c.id,
            title=c.title,
            user_id=c.user_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in conversations
    ]


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
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return ConversationRead(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MessageRead]:
    # Verify ownership
    conv = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,  # type: ignore[arg-type]
            Conversation.user_id == current_user.id,  # type: ignore[arg-type]
        )
    )
    if conv.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

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
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,  # type: ignore[arg-type]
            Conversation.user_id == current_user.id,  # type: ignore[arg-type]
        )
    )
    conversation = result.scalars().first()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conversation.title = data.title
    conversation.updated_at = datetime.now(UTC)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return ConversationRead(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,  # type: ignore[arg-type]
            Conversation.user_id == current_user.id,  # type: ignore[arg-type]
        )
    )
    conversation = result.scalars().first()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

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
) -> AsyncGenerator[str, None]:
    try:
        client = AsyncOpenAI(base_url=base_url, api_key=api_key or "no-key")
        full_content = ""
        response = await client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            stream=True,
        )
        # response is AsyncStream[ChatCompletionChunk] when stream=True
        stream: Any = response
        chunk: ChatCompletionChunk
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_content += text
                yield f"data: {json.dumps({'type': 'token', 'delta': text})}\n\n"

        # After stream completes, persist assistant message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,
        )
        session.add(assistant_msg)
        await session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)  # type: ignore[arg-type]
            .values(updated_at=datetime.now(UTC))
        )
        await session.commit()
        await session.refresh(assistant_msg)
        yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg.id})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/{conversation_id}/stream")
async def stream_chat(
    conversation_id: int,
    data: ChatStreamRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    # Verify conversation belongs to current user
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,  # type: ignore[arg-type]
            Conversation.user_id == current_user.id,  # type: ignore[arg-type]
        )
    )
    conversation = result.scalars().first()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

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

    return StreamingResponse(
        _token_generator(
            messages=openai_messages,
            base_url=provider.base_url,
            api_key=api_key,
            model=model_name,
            conversation_id=conversation_id,
            session=session,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
