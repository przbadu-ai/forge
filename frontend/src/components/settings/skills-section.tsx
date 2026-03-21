"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/context/auth-context";
import { listSkills, toggleSkill } from "@/lib/skills-api";
import type { SkillRead } from "@/lib/skills-api";

function SkillRow({
  skill,
  onToggle,
}: {
  skill: SkillRead;
  onToggle: (id: number) => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-md border p-4">
      <div className="space-y-1">
        <p className="text-sm font-medium">{skill.name}</p>
        <p className="text-muted-foreground text-xs">{skill.description}</p>
      </div>
      <Switch
        checked={skill.is_enabled}
        onCheckedChange={() => onToggle(skill.id)}
        aria-label={`Toggle ${skill.name}`}
      />
    </div>
  );
}

export function SkillsSection() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const {
    data: skills,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["skills"],
    queryFn: () => listSkills(token!),
    enabled: !!token,
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => toggleSkill(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });

  function handleToggle(id: number) {
    toggleMutation.mutate(id);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="text-muted-foreground size-6 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-destructive rounded-md bg-destructive/10 p-4 text-sm">
        Failed to load skills: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground text-sm">
        Enable or disable agent skills. Skills allow the AI to perform
        specialized actions during chat.
      </p>

      {skills && skills.length > 0 ? (
        <div className="space-y-3">
          {skills.map((skill) => (
            <SkillRow key={skill.id} skill={skill} onToggle={handleToggle} />
          ))}
        </div>
      ) : (
        <div className="text-muted-foreground rounded-md border border-dashed p-8 text-center text-sm">
          No skills available.
        </div>
      )}
    </div>
  );
}
