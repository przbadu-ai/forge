"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useConversations } from "@/hooks/useConversations";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Plus, Trash2, MessageSquare } from "lucide-react";

interface ConversationListProps {
  activeId?: number;
}

export function ConversationList({ activeId }: ConversationListProps) {
  const router = useRouter();
  const {
    conversations,
    isLoading,
    createConversation,
    renameConversation,
    deleteConversation,
  } = useConversations();

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleNew = useCallback(async () => {
    const conv = await createConversation();
    router.push(`/chat/${conv.id}`);
  }, [createConversation, router]);

  const handleSelect = useCallback(
    (id: number) => {
      router.push(`/chat/${id}`);
    },
    [router],
  );

  const handleDoubleClick = useCallback(
    (id: number, title: string) => {
      setEditingId(id);
      setEditValue(title);
      // Focus after render
      requestAnimationFrame(() => inputRef.current?.focus());
    },
    [],
  );

  const handleRenameSubmit = useCallback(
    async (id: number) => {
      const trimmed = editValue.trim();
      if (trimmed) {
        await renameConversation(id, trimmed);
      }
      setEditingId(null);
    },
    [editValue, renameConversation],
  );

  const handleDelete = useCallback(
    async (e: React.MouseEvent, id: number) => {
      e.stopPropagation();
      if (!window.confirm("Delete this conversation?")) return;
      await deleteConversation(id);
      if (activeId === id) {
        router.push("/chat");
      }
    },
    [activeId, deleteConversation, router],
  );

  return (
    <div className="flex h-full flex-col">
      <div className="p-3">
        <Button
          variant="outline"
          className="w-full justify-start gap-2"
          onClick={handleNew}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-2">
        {isLoading ? (
          <div className="px-3 py-2 text-sm text-muted-foreground">
            Loading...
          </div>
        ) : conversations.length === 0 ? (
          <div className="px-3 py-2 text-sm text-muted-foreground">
            No conversations yet
          </div>
        ) : (
          <div className="space-y-0.5">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={cn(
                  "group flex items-center gap-1 rounded-lg px-3 py-2 text-sm transition-colors cursor-pointer hover:bg-muted",
                  activeId === conv.id && "bg-muted font-medium",
                )}
                onClick={() => handleSelect(conv.id)}
                onDoubleClick={() =>
                  handleDoubleClick(conv.id, conv.title)
                }
              >
                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />

                {editingId === conv.id ? (
                  <input
                    ref={inputRef}
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => void handleRenameSubmit(conv.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        void handleRenameSubmit(conv.id);
                      } else if (e.key === "Escape") {
                        setEditingId(null);
                      }
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="min-w-0 flex-1 rounded border bg-background px-1 py-0.5 text-sm outline-none"
                  />
                ) : (
                  <span className="min-w-0 flex-1 truncate">
                    {conv.title}
                  </span>
                )}

                <button
                  onClick={(e) => void handleDelete(e, conv.id)}
                  className="shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                  aria-label="Delete conversation"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
