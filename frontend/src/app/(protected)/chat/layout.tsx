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
    <div className="flex h-full overflow-hidden">
      {/* Sidebar */}
      <aside className="bg-muted/30 w-64 shrink-0 border-r">
        <ConversationList activeId={activeId} />
      </aside>

      {/* Main content */}
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  );
}
