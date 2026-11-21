"use client";

export const KEYS = {
  disclaimer: "aegis.disclaimer",
  household: "aegis.household_id",
  plan: "aegis.plan_id",
};

export function readKey(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

export function writeKey(key: string, value: string) {
  window.localStorage.setItem(key, value);
}
