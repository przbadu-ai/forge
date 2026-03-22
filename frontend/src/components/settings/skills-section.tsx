"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Trash2, RefreshCw } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuth } from "@/context/auth-context";
import {
  listSkills,
  toggleSkill,
  createSkill,
  deleteSkill,
  syncSkills,
} from "@/lib/skills-api";
import type { SkillRead, SyncResult } from "@/lib/skills-api";

function SkillRow({
  skill,
  onToggle,
  onDelete,
}: {
  skill: SkillRead;
  onToggle: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="flex items-center justify-between rounded-md border p-4">
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-sm font-medium">{skill.name}</p>
        <p className="text-muted-foreground text-xs">{skill.description}</p>
        {skill.source_path && (
          <p className="text-muted-foreground truncate text-[10px]">
            {skill.source_path}
          </p>
        )}
      </div>
      <div className="ml-4 flex items-center gap-2">
        {confirmDelete ? (
          <div className="flex items-center gap-1">
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                onDelete(skill.id);
                setConfirmDelete(false);
              }}
            >
              Confirm
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setConfirmDelete(false)}
            >
              Cancel
            </Button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmDelete(true)}
            className="text-muted-foreground hover:text-destructive p-1 transition-colors"
            aria-label={`Delete ${skill.name}`}
          >
            <Trash2 className="size-4" />
          </button>
        )}
        <Switch
          checked={skill.is_enabled}
          onCheckedChange={() => onToggle(skill.id)}
          aria-label={`Toggle ${skill.name}`}
        />
      </div>
    </div>
  );
}

export function SkillsSection() {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newInstructions, setNewInstructions] = useState("");
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

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

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSkill(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description: string; content?: string }) =>
      createSkill(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      setShowAddForm(false);
      setNewName("");
      setNewDescription("");
      setNewInstructions("");
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => syncSkills(token!),
    onSuccess: (result: SyncResult) => {
      queryClient.invalidateQueries({ queryKey: ["skills"] });
      setSyncMessage(
        `Discovered ${result.total_discovered} skill(s): ${result.created} created, ${result.updated} updated`
      );
    },
    onError: (err: Error) => {
      setSyncMessage(`Sync failed: ${err.message}`);
    },
  });

  // Auto-dismiss sync message after 4 seconds
  useEffect(() => {
    if (!syncMessage) return;
    const timer = setTimeout(() => setSyncMessage(null), 4000);
    return () => clearTimeout(timer);
  }, [syncMessage]);

  function handleToggle(id: number) {
    toggleMutation.mutate(id);
  }

  function handleDelete(id: number) {
    deleteMutation.mutate(id);
  }

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    createMutation.mutate({
      name: newName.trim(),
      description: newDescription.trim(),
      content: newInstructions.trim() || undefined,
    });
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
        specialized actions during chat. Configure skill directories in General
        settings, then scan to discover skills.
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAddForm((v) => !v)}
        >
          <Plus className="mr-1 size-4" />
          Add Skill
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
        >
          {syncMutation.isPending ? (
            <Loader2 className="mr-1 size-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-1 size-4" />
          )}
          Scan Directories
        </Button>
        {syncMessage && (
          <span className="text-muted-foreground text-xs">{syncMessage}</span>
        )}
      </div>

      <Dialog open={showAddForm} onOpenChange={setShowAddForm}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Write skill instructions</DialogTitle>
          </DialogHeader>
          <form
            onSubmit={(e) => void handleCreate(e)}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="skill-name">Skill name</Label>
              <Input
                id="skill-name"
                placeholder="weekly-status-report"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="skill-desc">Description</Label>
              <Textarea
                id="skill-desc"
                rows={3}
                placeholder="Generate weekly status reports from recent work. Use when asked for updates or progress summaries."
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="skill-instructions">Instructions</Label>
              <Textarea
                id="skill-instructions"
                rows={8}
                placeholder="Summarize my recent work in three sections: wins, blockers, and next steps. Keep the tone professional but not stiff..."
                value={newInstructions}
                onChange={(e) => setNewInstructions(e.target.value)}
              />
            </div>
            {createMutation.isError && (
              <p className="text-destructive text-sm">
                {createMutation.error.message}
              </p>
            )}
            <DialogFooter>
              <DialogClose
                render={<Button variant="outline" type="button" />}
              >
                Cancel
              </DialogClose>
              <Button
                type="submit"
                disabled={!newName.trim() || createMutation.isPending}
              >
                {createMutation.isPending && (
                  <Loader2 className="mr-1 size-4 animate-spin" />
                )}
                Create
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {skills && skills.length > 0 ? (
        <div className="space-y-3">
          {skills.map((skill) => (
            <SkillRow
              key={skill.id}
              skill={skill}
              onToggle={handleToggle}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <div className="text-muted-foreground rounded-md border border-dashed p-8 text-center text-sm">
          No skills available. Add one manually or scan directories to discover
          skills.
        </div>
      )}
    </div>
  );
}
