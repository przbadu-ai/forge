"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useConversations } from "@/hooks/useConversations";
import { Button } from "@/components/ui/button";
import { MessageSquarePlus } from "lucide-react";

export default function ChatPage() {
  const router = useRouter();
  const { createConversation } = useConversations();

  const handleNew = useCallback(async () => {
    const conv = await createConversation();
    router.push(`/chat/${conv.id}`);
  }, [createConversation, router]);

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4">
      <MessageSquarePlus className="text-muted-foreground/50 h-12 w-12" />
      <h2 className="text-muted-foreground text-lg font-medium">
        Select a conversation or start a new one
      </h2>
      <Button onClick={handleNew}>New Chat</Button>
    </div>
  );
}
