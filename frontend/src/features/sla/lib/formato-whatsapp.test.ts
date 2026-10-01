import { describe, expect, it } from "vitest";
import type { IncidenteDerivado } from "../types/derivados";
import type { IncidenteMesaAyuda } from "../types/mesa-ayuda";
import type { IncidenteSinCerrar } from "../types/pendientes";
import type { IncidenteVencido } from "../types/sla";
import {
  formatearDerivadosWhatsapp,
  formatearMesaAyudaWhatsapp,
  formatearPendientesACerrarWhatsapp,
  formatearTablaWhatsapp,
} from "./formato-whatsapp";

// Mediodía en Argentina: el día calendario no depende del huso.
const FECHA = "2026-09-15T15:00:00Z";

function vencido(id: number, agente: string, horas: number, extra: Partial<IncidenteVencido> = {}): IncidenteVencido {
  return {
    id_incidente: id,
    tecnico: "Juan Pérez",
    id_tecnico: 1,
    region: "LOCAL",
    cliente: "Banco X",
    sucursal: "Centro",
    modelo: "HP M404",
    nro_serie: "SN1",
    fecha_ingreso: FECHA,
    fecha_operativo: FECHA,
    tiempo: "",
    rango: "",
    sla_horas: 48,
    horas_vencido: horas,
    agente,
    ...extra,
  };
}

describe("mensaje de WhatsApp de vencidos SLA", () => {
  it("encabeza con el período y el total de incidentes", () => {
    const lineas = formatearTablaWhatsapp([vencido(1, "Local", 5)], "septiembre").split("\n");
    expect(lineas.slice(0, 3)).toEqual(["📋 *Tablero SLA — vencidos septiembre*", "1 incidentes", ""]);
  });

  it("cada incidente lleva semáforo, ID, cliente, equipo, técnico, fecha y horas vencidas", () => {
    const texto = formatearTablaWhatsapp([vencido(12345, "Local", 30)], "hoy");
    expect(texto).toContain(
      "🟠 *#12345* — Banco X, Centro\n🖨️ HP M404 — Juan Pérez\n📅 15/9 · vencido *30h* (SLA 48h)",
    );
  });

  it("semáforo: amarillo hasta 24 h, naranja hasta 100 h y rojo por encima", () => {
    const marca = (horas: number) => formatearTablaWhatsapp([vencido(1, "Local", horas)], "x").split("\n")[5];
    expect(marca(24)).toMatch(/^🟡/);
    expect(marca(25)).toMatch(/^🟠/);
    expect(marca(100)).toMatch(/^🟠/);
    expect(marca(101)).toMatch(/^🔴/);
  });

  it("sin fecha operativa muestra un guion", () => {
    expect(formatearTablaWhatsapp([vencido(1, "Local", 5, { fecha_operativo: null })], "x")).toContain(
      "📅 — · vencido",
    );
  });

  it("agrupa por agente con subtotal, el que tiene más vencidos primero", () => {
    const texto = formatearTablaWhatsapp(
      [vencido(1, "Local", 5), vencido(2, "Ana", 5), vencido(3, "Ana", 5)],
      "x",
    );
    expect(texto.indexOf("👤 *Ana* (2)")).toBeGreaterThan(-1);
    expect(texto.indexOf("👤 *Ana* (2)")).toBeLessThan(texto.indexOf("👤 *Local* (1)"));
    // Línea en blanco entre incidentes y dos entre grupos.
    expect(texto).toContain("(SLA 48h)\n\n🟡 *#3*");
    expect(texto).toContain("(SLA 48h)\n\n\n👤 *Local* (1)");
  });
});

describe("mensaje de WhatsApp de incidentes sin consultar", () => {
  const derivado = (id: number, tecnico: string, demorado: boolean): IncidenteDerivado => ({
    id_incidente: id,
    fecha_ingreso: FECHA,
    tipo: "",
    estado: "",
    cliente: "Banco X",
    sucursal: "Centro",
    nro_serie: "SN1",
    modelo: "HP M404",
    tecnico,
    id_tecnico: 1,
    operador: null,
    dias_desde_ingreso: 4,
    demorado,
    mda_id_incidente: null,
    casos_mda_en_sucursal: 0,
  });

  it("agrupa por técnico y marca en rojo los demorados", () => {
    const texto = formatearDerivadosWhatsapp(
      [derivado(1, "Ana", true), derivado(2, "Beto", false), derivado(3, "Beto", false)],
      "semana",
    );
    expect(texto.startsWith("📋 *Incidentes sin consultar — semana*\n3 incidentes\n\n👤 *Beto* (2)")).toBe(true);
    expect(texto).toContain("🔴 *#1* — Banco X, Centro");
    expect(texto).toContain("🟡 *#2* — Banco X, Centro");
    expect(texto).toContain("📅 Ingreso 15/9 · sin consultar hace *4 día(s)*");
  });
});

describe("mensaje de WhatsApp de pendientes a cerrar", () => {
  const pendiente = (id: number, dias: number): IncidenteSinCerrar => ({
    id_incidente: id,
    tecnico: "Ana",
    id_tecnico: 1,
    cliente: "Banco X",
    sucursal: "Centro",
    modelo: "HP M404",
    nro_serie: "SN1",
    fecha_ingreso: FECHA,
    fecha_finalizacion: null,
    dias_en_estado: dias,
  });

  it("marca en rojo desde 30 días sin cerrar y muestra ingreso → finalizado", () => {
    const texto = formatearPendientesACerrarWhatsapp([pendiente(1, 29), pendiente(2, 30)]);
    expect(texto.startsWith("📋 *Pendientes a Cerrar*\n2 incidentes\n\n👤 *Ana* (2)")).toBe(true);
    expect(texto).toContain("🟡 *#1*");
    expect(texto).toContain("🔴 *#2*");
    expect(texto).toContain("📅 Ingreso 15/9 → Finalizado — · *30 día(s)* sin cerrar");
  });
});

describe("mensaje de WhatsApp de Mesa de Ayuda", () => {
  const caso = (id: number, operador: string, demorado: boolean): IncidenteMesaAyuda => ({
    id_incidente: id,
    fecha_ingreso: FECHA,
    tipo: "",
    estado: "",
    cliente: "Banco X",
    sucursal: "Centro",
    nro_serie: "SN1",
    modelo: "HP M404",
    operador_login: "op",
    operador,
    dias_transcurridos: 2,
    demorado,
    visita_id_incidente: null,
    visita_tecnico: null,
    visita_estado: null,
    visitas_en_sucursal: 0,
  });

  it("agrupa por operador y no muestra técnico en la línea del equipo", () => {
    const texto = formatearMesaAyudaWhatsapp([caso(1, "Carla", true)]);
    expect(texto).toBe(
      "📋 *Incidentes Mesa de Ayuda*\n1 incidentes\n\n👤 *Carla* (1)\n\n" +
        "🔴 *#1* — Banco X, Centro\n🖨️ HP M404\n📅 Ingreso 15/9 · *2 día(s)* transcurridos",
    );
  });
});
