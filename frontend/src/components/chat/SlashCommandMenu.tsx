"use client";

import { useEffect, useRef } from "react";
import { Zap } from "lucide-react";
import type { SkillRead } from "@/lib/skills-api";

interface SlashCommandMenuProps {
  skills: SkillRead[];
  filter: string;
  selectedIndex: number;
  onSelect: (skill: SkillRead) => void;
  position: { bottom: number; left: number };
}

export function SlashCommandMenu({
  skills,
  filter,
  selectedIndex,
  onSelect,
  position,
}: SlashCommandMenuProps) {
  const listRef = useRef<HTMLDivElement>(null);

  const filtered = skills.filter(
    (s) => s.is_enabled && s.name.toLowerCase().includes(filter.toLowerCase())
  );

  // Scroll selected item into view
  useEffect(() => {
    const el = listRef.current?.children[selectedIndex] as
      | HTMLElement
      | undefined;
    el?.scrollIntoView({ block: "nearest" });
  }, [selectedIndex]);

  if (filtered.length === 0) return null;

  return (
    <div
      ref={listRef}
      className="bg-popover absolute z-50 max-h-60 w-72 overflow-y-auto rounded-lg border p-1 shadow-lg"
      style={{ bottom: position.bottom, left: position.left }}
    >
      <div className="text-muted-foreground px-2 py-1.5 text-xs font-medium">
        Skills
      </div>
      {filtered.map((skill, i) => (
        <button
          key={skill.id}
          type="button"
          className={`flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
            i === selectedIndex
              ? "bg-accent text-accent-foreground"
              : "hover:bg-accent/50"
          }`}
          onMouseDown={(e) => {
            e.preventDefault(); // prevent textarea blur
            onSelect(skill);
          }}
        >
          <Zap className="text-muted-foreground mt-0.5 size-3.5 shrink-0" />
          <div className="min-w-0">
            <div className="font-medium">/{skill.name}</div>
            {skill.description && (
              <div className="text-muted-foreground truncate text-xs">
                {skill.description}
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}

export function getFilteredSkills(
  skills: SkillRead[],
  filter: string
): SkillRead[] {
  return skills.filter(
    (s) => s.is_enabled && s.name.toLowerCase().includes(filter.toLowerCase())
  );
}
