"use client";

import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const themes = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
] as const;

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  // Avoid hydration mismatch — next-themes resolves theme on client only
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Theme</CardTitle>
        <CardDescription>
          Choose how the application looks. Your preference is saved
          automatically.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          {themes.map(({ value, label, icon: Icon }) => (
            <Button
              key={value}
              variant={mounted && theme === value ? "default" : "outline"}
              size="sm"
              onClick={() => setTheme(value)}
              aria-pressed={mounted && theme === value}
            >
              <Icon data-icon="inline-start" />
              {label}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
