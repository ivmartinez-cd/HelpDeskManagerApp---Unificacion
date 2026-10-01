import { describe, expect, it } from "vitest";
import type { DetalleContadorRow } from "../types/detalle-contador-proceso";
import { formatearTablaWhatsapp } from "./formato-whatsapp";

const fila = (over: Partial<DetalleContadorRow>): DetalleContadorRow =>
  ({
    sucursal: "Centro", modelo: "M404", serie: "S1", sector: null, fecha_toma_anterior: "2026-08-01",
    contador_anterior: 12000, fecha_toma_actual: "2026-09-01", contador_actual: 15500,
    impresiones_reales: 3500, tipo: "Real", estado_maquina: "Activa", falta_contador: false, ...over,
  }) as DetalleContadorRow;

describe("detalle de contadores para WhatsApp", () => {
  it("encabeza con cliente, alcance y cantidad de equipos", () => {
    const lineas = formatearTablaWhatsapp([fila({}), fila({ serie: "S2" })], "Acme SA", "Proceso 123").split("\n");
    expect(lineas[0]).toBe("📋 *Detalle de contadores — Acme SA*");
    expect(lineas[1]).toBe("Proceso 123 · 2 equipos");
    const uno = formatearTablaWhatsapp([fila({})], "Acme SA", "Proceso 123").split("\n");
    expect(uno[1]).toBe("Proceso 123 · 1 equipo");
  });

  it("agrupa por sucursal en orden alfabético con la cantidad de cada una", () => {
    const texto = formatearTablaWhatsapp(
      [fila({ sucursal: "Zárate" }), fila({ sucursal: "Ávila" }), fila({ sucursal: "Zárate", serie: "S2" })],
      "X", "Y",
    );
    const anclas = texto.split("\n").filter((l) => l.startsWith("📍"));
    expect(anclas).toEqual(["📍 *Ávila* (1)", "📍 *Zárate* (2)"]);
  });

  it("describe cada equipo con sus tomas en fecha dd/mm/aaaa y números con punto de miles", () => {
    const texto = formatearTablaWhatsapp([fila({ sector: "Recepción" })], "X", "Y");
    expect(texto).toContain("🟢 *M404* — Serie S1 · Recepción\n");
    expect(texto).toContain("📅 Ant. 01/08/2026 (12.000) → Act. 01/09/2026 (15.500)\n");
    expect(texto).toContain("🖨️ Impr: 3.500 · Real · Activa");
  });

  it("marca en rojo el equipo al que le falta contador y usa '—' para lo que no vino", () => {
    const texto = formatearTablaWhatsapp(
      [fila({ falta_contador: true, fecha_toma_actual: null, tipo: null, estado_maquina: null })], "X", "Y",
    );
    expect(texto).toContain("🔴 *M404* — Serie S1\n");
    expect(texto).toContain("Act. — (15.500)");
    expect(texto).toContain("🖨️ Impr: 3.500 · — · —");
  });
});
