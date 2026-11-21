"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { User } from "@/lib/types";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<{ user: User }>("/auth/me").then((r) => r.user),
    staleTime: 60_000,
  });
}

export function useCan(permission: string): boolean {
  const { data } = useMe();
  return Boolean(data?.permissions.includes(permission));
}
