"use client";

import { useCallback, useRef, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { SendHorizontal, Square } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { listSkills } from "@/lib/skills-api";
import type { SkillRead } from "@/lib/skills-api";
import { SlashCommandMenu, getFilteredSkills } from "./SlashCommandMenu";

interface ChatInputProps {
  onSend: (content: string) => void;
  onStop?: () => void;
  isStreaming?: boolean;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onStop,
  isStreaming,
  disabled,
}: ChatInputProps) {
  const { token } = useAuth();
  const [value, setValue] = useState("");
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashFilter, setSlashFilter] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data: skills = [] } = useQuery({
    queryKey: ["skills"],
    queryFn: () => listSkills(token!),
    enabled: !!token,
    staleTime: 30_000,
  });

  const enabledSkills = skills.filter((s) => s.is_enabled);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled || isStreaming) return;

    // Check if the message starts with a slash command
    const slashMatch = trimmed.match(/^\/(\S+)\s*([\s\S]*)$/);
    if (slashMatch) {
      const skillName = slashMatch[1];
      const userMessage = slashMatch[2].trim();
      const skill = enabledSkills.find(
        (s) => s.name.toLowerCase() === skillName.toLowerCase()
      );

      if (skill?.content) {
        // Prepend skill instructions to the user's message
        const enriched = `[Skill: ${skill.name}]\n\n<skill_instructions>\n${skill.content}\n</skill_instructions>\n\n${userMessage || `Use the ${skill.name} skill.`}`;
        onSend(enriched);
      } else {
        // No content/instructions — send as-is
        onSend(trimmed);
      }
    } else {
      onSend(trimmed);
    }

    setValue("");
    setShowSlashMenu(false);
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    });
  }, [value, disabled, isStreaming, onSend, enabledSkills]);

  const insertSkillCommand = useCallback((skill: SkillRead) => {
    setValue(`/${skill.name} `);
    setShowSlashMenu(false);
    setSlashFilter("");
    setSelectedIndex(0);
    textareaRef.current?.focus();
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      setValue(newValue);
      adjustHeight();

      // Detect slash command input
      const match = newValue.match(/^\/(\S*)$/);
      if (match && enabledSkills.length > 0) {
        setSlashFilter(match[1]);
        setShowSlashMenu(true);
        setSelectedIndex(0);
      } else {
        setShowSlashMenu(false);
      }
    },
    [adjustHeight, enabledSkills.length]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showSlashMenu) {
      const filtered = getFilteredSkills(enabledSkills, slashFilter);

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filtered.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(
          (prev) => (prev - 1 + filtered.length) % filtered.length
        );
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          insertSkillCommand(filtered[selectedIndex]);
        }
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setShowSlashMenu(false);
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Close menu on outside click
  useEffect(() => {
    if (!showSlashMenu) return;
    const handleClick = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowSlashMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showSlashMenu]);

  return (
    <div
      ref={containerRef}
      className="relative flex items-end gap-2 border-t p-4"
    >
      {showSlashMenu && (
        <SlashCommandMenu
          skills={enabledSkills}
          filter={slashFilter}
          selectedIndex={selectedIndex}
          onSelect={insertSkillCommand}
          position={{ bottom: 72, left: 16 }}
        />
      )}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Type a message... (/ for skills)"
        disabled={disabled || isStreaming}
        rows={1}
        className="bg-background placeholder:text-muted-foreground focus:ring-ring flex-1 resize-none rounded-xl border px-4 py-3 text-sm outline-none focus:ring-2 disabled:opacity-50"
      />
      {isStreaming ? (
        <Button
          onClick={onStop}
          variant="destructive"
          size="icon"
          aria-label="Stop generation"
        >
          <Square className="h-4 w-4" />
        </Button>
      ) : (
        <Button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          size="icon"
          aria-label="Send message"
        >
          <SendHorizontal className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
