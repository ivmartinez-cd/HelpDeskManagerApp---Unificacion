import { describe, expect, it } from "vitest";
import { calcCheckDigit, formatIncidentNumber } from "./check-digit";

describe("dígito verificador de Canal Directo (3-1 mod 10)", () => {
  it("pondera 3 y 1 alternados desde la izquierda", () => {
    // 1*3 + 2*1 + 3*3 = 14 → (10 - 4) % 10 = 6
    expect(calcCheckDigit("123")).toBe("6");
    expect(calcCheckDigit("0")).toBe("0");
  });

  it("ignora lo que no es dígito y no inventa uno sin número", () => {
    expect(calcCheckDigit("1-2-3")).toBe("6");
    expect(calcCheckDigit("abc")).toBe("");
  });

  it("arma el número de incidente con su dígito", () => {
    expect(formatIncidentNumber("123")).toBe("123-6");
    expect(formatIncidentNumber("")).toBe("");
  });
});
