import { describe, it, expect } from "vitest";
import manifest from "../app/manifest";

describe("PWA manifest", () => {
  const m = manifest();

  it("has required PWA fields", () => {
    expect(m.name).toBe("Forge");
    expect(m.short_name).toBe("Forge");
    expect(m.start_url).toBe("/");
    expect(m.display).toBe("standalone");
  });

  it("has theme and background colors", () => {
    expect(m.theme_color).toBeDefined();
    expect(m.background_color).toBeDefined();
  });

  it("has 3 icons with correct sizes", () => {
    expect(m.icons).toHaveLength(3);
    const sizes = m.icons!.map((i) => i.sizes);
    expect(sizes).toContain("192x192");
    expect(sizes).toContain("512x512");
    expect(sizes).toContain("180x180");
  });

  it("icons are PNG type", () => {
    for (const icon of m.icons!) {
      expect(icon.type).toBe("image/png");
    }
  });
});
