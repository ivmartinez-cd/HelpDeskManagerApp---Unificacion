import { describe, expect, it } from "vitest";
import type { AnexoPendiente } from "../types/anexos-pendientes";
import { formatearAnexosPendientesWhatsapp } from "./formato-whatsapp-anexos";

const anexo = (over: Partial<AnexoPendiente>): AnexoPendiente =>
  ({
    grupo: "Grupo A", contrato: "CT-1", anexo: "AX-1", empresa_admin: "Acme SA", vendedor: "Laura",
    periodo: "202608", fecha_proceso: "2026-09-03", estado: "demorado", importe_usd: "1234.5", ...over,
  }) as AnexoPendiente;

describe("anexos sin facturar para WhatsApp", () => {
  it("encabeza con el período y la cantidad de anexos", () => {
    const lineas = formatearAnexosPendientesWhatsapp([anexo({}), anexo({ anexo: "AX-2" })], "Agosto 2026").split("\n");
    expect(lineas[0]).toBe("📋 *Anexos sin facturar — Agosto 2026*");
    expect(lineas[1]).toBe("2 anexos");
  });

  it("agrupa por grupo de cliente en orden alfabético, con 'Sin grupo' para los que no tienen", () => {
    const texto = formatearAnexosPendientesWhatsapp(
      [anexo({ grupo: "Zeta" }), anexo({ grupo: null }), anexo({ grupo: "Alfa" }), anexo({ grupo: "Zeta" })], "P",
    );
    expect(texto.split("\n").filter((l) => l.startsWith("📁"))).toEqual([
      "📁 *Alfa* (1)", "📁 *Sin grupo* (1)", "📁 *Zeta* (2)",
    ]);
  });

  it("describe cada anexo con estado, contrato, empresa, vendedor, período, fecha e importe", () => {
    const texto = formatearAnexosPendientesWhatsapp([anexo({})], "P");
    expect(texto).toContain("🔴 *AX-1* (CT-1)\n🏢 Acme SA · Vendedor: Laura\n📅 Período 08/2026 (03/09/2026) · USD 1.234,50");
  });

  it("marca el estado con su emoji y omite el contrato si coincide con el anexo", () => {
    const texto = formatearAnexosPendientesWhatsapp(
      [anexo({ estado: "en_proceso", contrato: "AX-1" }), anexo({ anexo: "AX-2", estado: "mes_en_curso", contrato: null })], "P",
    );
    expect(texto).toContain("🟡 *AX-1*\n");
    expect(texto).toContain("⚪ *AX-2*\n");
  });

  it("usa '—' sin empresa y omite el vendedor si no hay", () => {
    const texto = formatearAnexosPendientesWhatsapp([anexo({ empresa_admin: null, vendedor: null })], "P");
    expect(texto).toContain("\n🏢 —\n");
  });
});
