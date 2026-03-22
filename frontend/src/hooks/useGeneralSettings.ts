"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/context/auth-context";
import { getGeneralSettings, updateGeneralSettings } from "@/lib/settings-api";
import type { GeneralSettings } from "@/types/chat";

const SETTINGS_KEY = ["general-settings"] as const;

export function useGeneralSettings() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: SETTINGS_KEY,
    queryFn: () => getGeneralSettings(token!),
    enabled: !!token,
  });

  const mutation = useMutation({
    mutationFn: (data: Partial<GeneralSettings>) =>
      updateGeneralSettings(token!, data),
    onSuccess: (updated) => {
      queryClient.setQueryData<GeneralSettings>(SETTINGS_KEY, updated);
    },
  });

  return {
    settings: query.data ?? null,
    isLoading: query.isLoading,
    updateSettings: mutation.mutateAsync,
  };
}
