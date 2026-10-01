import { afterEach, describe, expect, it, vi } from "vitest";
import type { Tarifario } from "../types/liquidaciones";
import { agruparPorZona, labelTipo, tiposPresentes } from "./tarifarios-matriz";

const tarifa = (over: Partial<Tarifario>): Tarifario =>
  ({
    id: Math.random().toString(), tipoServicio: "correctivo", spstId: null, costoServicio: 100,
    costoKm: 10, vigenciaDesde: "2026-01-01", vigenciaHasta: null, ...over,
  }) as Tarifario;

afterEach(() => {
  vi.useRealTimers();
});

describe("columnas de la matriz de tarifarios", () => {
  it("ordena los tipos como Siges y deja los desconocidos al final, alfabéticos", () => {
    const tipos = tiposPresentes([
      tarifa({ tipoServicio: "zeta" }), tarifa({ tipoServicio: "guardia" }),
      tarifa({ tipoServicio: "correctivo" }), tarifa({ tipoServicio: "alfa" }),
      tarifa({ tipoServicio: "guardia" }),
    ]);
    expect(tipos).toEqual(["correctivo", "guardia", "alfa", "zeta"]);
  });

  it("rotula los tipos conocidos y humaniza los desconocidos", () => {
    expect(labelTipo("instalacion_desinstalacion")).toBe("Instalación");
    expect(labelTipo("tipo_nuevo_x")).toBe("tipo nuevo x");
  });
});

describe("agrupado de tarifas por zona y vigencia", () => {
  it("arma una vigencia por fecha de inicio, de la más nueva a la más vieja", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T15:00:00Z"));
    const [zona] = agruparPorZona([
      tarifa({ vigenciaDesde: "2026-01-01", vigenciaHasta: "2026-05-31" }),
      tarifa({ vigenciaDesde: "2026-06-01", tipoServicio: "correctivo" }),
      tarifa({ vigenciaDesde: "2026-06-01", tipoServicio: "preventivo" }),
    ]);
    expect(zona.spstId).toBeNull();
    expect(zona.vigencias.map((v) => v.desde)).toEqual(["2026-06-01", "2026-01-01"]);
    expect(Object.keys(zona.vigencias[0].porTipo).sort()).toEqual(["correctivo", "preventivo"]);
    expect(zona.vigente?.desde).toBe("2026-06-01");
  });

  it("separa las zonas SPST de la genérica", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T15:00:00Z"));
    const zonas = agruparPorZona([tarifa({ spstId: "SP1" }), tarifa({}), tarifa({ spstId: "SP1" })]);
    expect(zonas.map((z) => z.spstId).sort()).toEqual([null, "SP1"].sort());
  });

  it("la vigencia queda abierta si alguna tarifa no tiene hasta, y si no toma el hasta más tardío", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T15:00:00Z"));
    const [abierta] = agruparPorZona([
      tarifa({ vigenciaHasta: "2026-03-31" }), tarifa({ tipoServicio: "guardia", vigenciaHasta: null }),
    ]);
    expect(abierta.vigencias[0].hasta).toBeNull();
    const [cerrada] = agruparPorZona([
      tarifa({ vigenciaHasta: "2026-03-31" }), tarifa({ tipoServicio: "guardia", vigenciaHasta: "2026-04-30" }),
    ]);
    expect(cerrada.vigencias[0].hasta).toBe("2026-04-30");
  });

  it("usa el mayor costo por km cuando las tarifas de una vigencia difieren", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-15T15:00:00Z"));
    const [zona] = agruparPorZona([tarifa({ costoKm: 12 }), tarifa({ tipoServicio: "guardia", costoKm: 30 })]);
    expect(zona.vigencias[0].costoKm).toBe(30);
  });

  it("toma como vigente la que cubre hoy y, si ninguna, la más nueva", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-15T15:00:00Z"));
    const tarifas = [
      tarifa({ vigenciaDesde: "2026-01-01", vigenciaHasta: "2026-05-31" }),
      tarifa({ vigenciaDesde: "2026-06-01" }),
    ];
    expect(agruparPorZona(tarifas)[0].vigente?.desde).toBe("2026-01-01");
    vi.setSystemTime(new Date("2025-12-01T15:00:00Z"));
    expect(agruparPorZona(tarifas)[0].vigente?.desde).toBe("2026-06-01");
  });

  it("la vigente se decide con el día argentino, no el de UTC", () => {
    vi.useFakeTimers();
    // 31/05 a las 23:00 en Argentina = 01/06 02:00 UTC.
    vi.setSystemTime(new Date("2026-06-01T02:00:00Z"));
    const [zona] = agruparPorZona([
      tarifa({ vigenciaDesde: "2026-01-01", vigenciaHasta: "2026-05-31" }),
      tarifa({ vigenciaDesde: "2026-06-01" }),
    ]);
    expect(zona.vigente?.desde).toBe("2026-01-01");
  });
});
