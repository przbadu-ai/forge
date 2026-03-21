"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";

export default function HomePage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">Forge</h1>
      {user && (
        <p className="text-muted-foreground text-sm">
          Signed in as {user.username}
        </p>
      )}
      <div className="flex gap-2">
        <Button
          variant="outline"
          render={<Link href="/settings" />}
        >
          <Settings data-icon="inline-start" />
          Settings
        </Button>
        <Button variant="outline" onClick={handleLogout}>
          Sign out
        </Button>
      </div>
    </main>
  );
}
