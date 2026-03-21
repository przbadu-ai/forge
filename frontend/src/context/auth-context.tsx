"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { loginApi, logoutApi, meApi, refreshApi } from "@/lib/auth";
import type { UserResponse } from "@/lib/auth";

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    user: null,
    isLoading: true,
  });
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Schedule next refresh 1 minute before expiry (14 min for 15 min tokens)
  const scheduleRefresh = useCallback((delayMs: number = 14 * 60 * 1000) => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    refreshTimerRef.current = setTimeout(async () => {
      try {
        const data = await refreshApi();
        setState((prev) => ({ ...prev, token: data.access_token }));
        scheduleRefresh();
      } catch {
        setState({ token: null, user: null, isLoading: false });
      }
    }, delayMs);
  }, []);

  // On mount: attempt refresh to restore session
  useEffect(() => {
    refreshApi()
      .then(async (data) => {
        const user = await meApi(data.access_token);
        setState({ token: data.access_token, user, isLoading: false });
        scheduleRefresh();
      })
      .catch(() => {
        setState({ token: null, user: null, isLoading: false });
      });
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [scheduleRefresh]);

  const login = useCallback(
    async (username: string, password: string) => {
      const data = await loginApi(username, password);
      const user = await meApi(data.access_token);
      setState({ token: data.access_token, user, isLoading: false });
      scheduleRefresh();
    },
    [scheduleRefresh],
  );

  const logout = useCallback(async () => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    await logoutApi();
    setState({ token: null, user: null, isLoading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
