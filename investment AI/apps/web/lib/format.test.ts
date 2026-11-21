import { describe, expect, it } from "vitest";
import { pct } from "./format";

describe("pct", () => {
  it("formats one decimal", () => {
    expect(pct(12)).toBe("12.0%");
  });
});
