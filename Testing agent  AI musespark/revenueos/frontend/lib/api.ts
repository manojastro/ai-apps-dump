"use client";

import { useCallback, useEffect, useState } from "react";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (response.status === 401 && !path.startsWith("/auth/")) {
    window.location.href = "/login";
    throw new ApiError(401, "Session expired");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : response.statusText;
    throw new ApiError(response.status, detail || "Request failed");
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(path !== null);

  const load = useCallback(() => {
    if (path === null) return () => undefined;
    let current = true;
    setLoading(true);
    setError(null);
    api<T>(path)
      .then((result) => current && setData(result))
      .catch((failure: ApiError) => current && setError(failure))
      .finally(() => current && setLoading(false));
    return () => {
      current = false;
    };
  }, [path]);

  useEffect(() => load(), [load]);
  return { data, error, loading, reload: load };
}
