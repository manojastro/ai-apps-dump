import { createContext, useContext, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type Role, type Session } from "./api";

interface AuthValue {
  session: Session | null;
  loading: boolean;
  has: (role: Role) => boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      try {
        return await api<Session>("/api/auth/session");
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null;
        throw e;
      }
    },
    staleTime: 60_000,
    retry: false,
  });
  const session = q.data ?? null;
  const value: AuthValue = {
    session,
    loading: q.isLoading,
    has: (role) => !!session && (session.roles.includes(role) || (role === "viewer" && session.roles.includes("admin"))),
    refresh: async () => { await qc.invalidateQueries({ queryKey: ["session"] }); },
    logout: async () => {
      await api("/api/auth/logout", { method: "POST" }).catch(() => undefined);
      qc.removeQueries();
      qc.setQueryData(["session"], null);
    },
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const v = useContext(AuthContext);
  if (!v) throw new Error("useAuth outside AuthProvider");
  return v;
}
