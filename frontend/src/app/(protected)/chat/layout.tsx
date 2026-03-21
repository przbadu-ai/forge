"use client";

import { useParams } from "next/navigation";
import { ConversationList } from "@/components/chat/ConversationList";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams<{ id?: string }>();
  const activeId = params.id ? Number(params.id) : undefined;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r bg-muted/30">
        <ConversationList activeId={activeId} />
      </aside>

      {/* Main content */}
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  );
}
