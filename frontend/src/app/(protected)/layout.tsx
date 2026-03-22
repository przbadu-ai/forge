"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { AppHeader } from "@/components/layout/app-header";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace("/login");
    }
  }, [token, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="text-muted-foreground text-sm">Loading...</span>
      </div>
    );
  }

  if (!token) return null; // redirect in progress

  return (
    <div className="flex h-screen flex-col">
      <AppHeader />
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
