import { describe, expect, it } from "vitest";
import { incidentUrl } from "./incident-link";

const BASE = "https://webagentes.canaldirecto.com.ar/incidents/view";

describe("link a Web Agentes con dígito verificador", () => {
  it("agrega el dígito con pesos 3-1-3-1 de izquierda a derecha", () => {
    // 1·3 + 2 + 3·3 + 4 + 5·3 + 6 = 39 → 10 - 9 = 1
    expect(incidentUrl(123456)).toBe(`${BASE}/123456-1`);
    expect(incidentUrl("1000")).toBe(`${BASE}/1000-7`);
  });

  it("si la suma es múltiplo de 10 el dígito es 0, no 10", () => {
    // 5·3 + 5 = 20
    expect(incidentUrl(55)).toBe(`${BASE}/55-0`);
  });

  it("descarta un dígito verificador previo y lo recalcula", () => {
    expect(incidentUrl("123456-9")).toBe(`${BASE}/123456-1`);
  });
});
