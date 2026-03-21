"use client";

import { use } from "react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { useConversations } from "@/hooks/useConversations";

export default function ConversationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const conversationId = Number(id);
  const { refetch } = useConversations();

  return (
    <ChatPanel
      conversationId={conversationId}
      onConversationUpdated={refetch}
    />
  );
}
