"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/context/auth-context";
import {
  getConversations,
  createConversation as createConversationApi,
  renameConversation as renameConversationApi,
  deleteConversation as deleteConversationApi,
} from "@/lib/chat-api";
import type { Conversation } from "@/types/chat";

const CONVERSATIONS_KEY = ["conversations"] as const;

export function useConversations() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: CONVERSATIONS_KEY,
    queryFn: () => getConversations(token!),
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: () => createConversationApi(token!),
    onSuccess: (newConversation) => {
      queryClient.setQueryData<Conversation[]>(
        CONVERSATIONS_KEY,
        (old) => (old ? [newConversation, ...old] : [newConversation]),
      );
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) =>
      renameConversationApi(token!, id, title),
    onMutate: async ({ id, title }) => {
      await queryClient.cancelQueries({ queryKey: CONVERSATIONS_KEY });
      const previous =
        queryClient.getQueryData<Conversation[]>(CONVERSATIONS_KEY);
      queryClient.setQueryData<Conversation[]>(CONVERSATIONS_KEY, (old) =>
        old?.map((c) => (c.id === id ? { ...c, title } : c)),
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(CONVERSATIONS_KEY, context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteConversationApi(token!, id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: CONVERSATIONS_KEY });
      const previous =
        queryClient.getQueryData<Conversation[]>(CONVERSATIONS_KEY);
      queryClient.setQueryData<Conversation[]>(CONVERSATIONS_KEY, (old) =>
        old?.filter((c) => c.id !== id),
      );
      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(CONVERSATIONS_KEY, context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
  });

  return {
    conversations: query.data ?? [],
    isLoading: query.isLoading,
    createConversation: createMutation.mutateAsync,
    renameConversation: (id: number, title: string) =>
      renameMutation.mutateAsync({ id, title }),
    deleteConversation: (id: number) => deleteMutation.mutateAsync(id),
    refetch: () => void queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY }),
  };
}
