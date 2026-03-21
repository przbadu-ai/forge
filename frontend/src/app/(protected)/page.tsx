"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";

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
      <Button variant="outline" onClick={handleLogout}>
        Sign out
      </Button>
    </main>
  );
}
