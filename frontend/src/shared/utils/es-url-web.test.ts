import { describe, expect, it } from "vitest";
import { esUrlWeb } from "./es-url-web";

describe("esUrlWeb", () => {
  it("solo acepta http y https", () => {
    expect(esUrlWeb("https://maps.google.com/x")).toBe(true);
    expect(esUrlWeb(" HTTP://ejemplo.com")).toBe(true);
    expect(esUrlWeb("javascript:alert(1)")).toBe(false);
    expect(esUrlWeb("maps")).toBe(false);
    expect(esUrlWeb("google.com/maps")).toBe(false);
    expect(esUrlWeb(null)).toBe(false);
  });
});
