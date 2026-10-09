import { describe, expect, it } from "vitest";
import { conAjusteInicial, diasDelCiclo, textoAjusteInicial } from "./saldo";

describe("saldo de vacaciones", () => {
  it("los días del ciclo son antigüedad más arrastre, sin el ajuste inicial", () => {
    expect(diasDelCiclo({ annual: 35, carryOver: 14 })).toBe(49);
  });

  it("describe el ajuste inicial con su signo", () => {
    expect(textoAjusteInicial({ ajusteInicial: -14 })).toBe("ajuste inicial −14");
    expect(textoAjusteInicial({ ajusteInicial: 7 })).toBe("ajuste inicial +7");
  });

  it("sin ajuste no muestra nada", () => {
    expect(textoAjusteInicial({ ajusteInicial: 0 })).toBeNull();
    expect(conAjusteInicial("de 35 este año", { ajusteInicial: 0 })).toBe("de 35 este año");
  });

  it("agrega el ajuste al final del texto", () => {
    expect(conAjusteInicial("de 35 este año", { ajusteInicial: -14 })).toBe(
      "de 35 este año · ajuste inicial −14",
    );
  });
});
