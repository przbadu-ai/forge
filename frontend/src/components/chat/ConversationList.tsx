"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { useConversations } from "@/hooks/useConversations";
import { searchConversations } from "@/lib/chat-api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Plus, Trash2, MessageSquare, Search } from "lucide-react";
import type { Conversation } from "@/types/chat";

interface ConversationListProps {
  activeId?: number;
}

export function ConversationList({ activeId }: ConversationListProps) {
  const router = useRouter();
  const { token } = useAuth();
  const {
    conversations,
    isLoading,
    createConversation,
    renameConversation,
    deleteConversation,
  } = useConversations();

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Conversation[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults(null);
      return;
    }

    const timer = setTimeout(async () => {
      if (!token) return;
      setIsSearching(true);
      try {
        const results = await searchConversations(token, searchQuery);
        setSearchResults(results);
      } catch {
        setSearchResults(null);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, token]);

  const displayConversations = searchResults ?? conversations;

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

      {/* Search input */}
      <div className="px-3 pb-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="pl-8"
            aria-label="Search conversations"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2">
        {isLoading || isSearching ? (
          <div className="px-3 py-2 text-sm text-muted-foreground">
            Loading...
          </div>
        ) : displayConversations.length === 0 ? (
          <div className="px-3 py-2 text-sm text-muted-foreground">
            {searchQuery.length >= 2
              ? "No conversations found"
              : "No conversations yet"}
          </div>
        ) : (
          <div className="space-y-0.5">
            {displayConversations.map((conv) => (
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
