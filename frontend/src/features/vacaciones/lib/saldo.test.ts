import { describe, expect, it } from "vitest";
import { diasDelCiclo } from "./saldo";

describe("saldo de vacaciones", () => {
  it("los días del ciclo son antigüedad más arrastre, sin el ajuste inicial", () => {
    expect(diasDelCiclo({ annual: 35, carryOver: 14 })).toBe(49);
  });
});
