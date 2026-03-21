import { apiFetch } from "@/lib/api";
import type { Conversation, Message } from "@/types/chat";

export async function getConversations(
  token: string,
): Promise<Conversation[]> {
  const res = await apiFetch("/api/v1/chat/conversations", token);
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return res.json() as Promise<Conversation[]>;
}

export async function createConversation(
  token: string,
): Promise<Conversation> {
  const res = await apiFetch("/api/v1/chat/conversations", token, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to create conversation");
  return res.json() as Promise<Conversation>;
}

export async function getMessages(
  token: string,
  conversationId: number,
): Promise<Message[]> {
  const res = await apiFetch(
    `/api/v1/chat/conversations/${conversationId}/messages`,
    token,
  );
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json() as Promise<Message[]>;
}

export async function renameConversation(
  token: string,
  id: number,
  title: string,
): Promise<Conversation> {
  const res = await apiFetch(`/api/v1/chat/conversations/${id}`, token, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to rename conversation");
  return res.json() as Promise<Conversation>;
}

export async function deleteConversation(
  token: string,
  id: number,
): Promise<void> {
  const res = await apiFetch(`/api/v1/chat/conversations/${id}`, token, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
}
