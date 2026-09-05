"use client";

import { Settings2 } from "lucide-react";
import type { Alerta, Incidente } from "../types/liquidaciones";

const PENDIENTES = new Set(["pendiente", "en_revision"]);

/** Diagnóstico de configuración derivado de las alertas pendientes: qué falta
 * en NUESTRA config (no en la factura del prestador) para que el motor pueda
 * ponerle precio a cada incidente. Es lo que nadie podía ver en el caso INFOMAC
 * 2026-09-04: 17 ALT008 que en realidad eran "sucursales sin zona". */
export function diagnosticoConfig(alertas: Alerta[], incidentes: Incidente[]) {
  const porId = Object.fromEntries(incidentes.map((i) => [i.id, i]));
  const sucursalesSinZona = new Set<string>();
  let incidentesSinZona = 0;
  let conZonaSinTarifa = 0;
  let paresFueraTablaKm = 0;
  for (const a of alertas) {
    if (!PENDIENTES.has(a.estado)) continue;
    if (a.tipoAlerta === "ALT009") {
      paresFueraTablaKm += 1;
    } else if (a.tipoAlerta === "ALT008") {
      const ctx = a.datosContexto as { spst_id?: string | null } | null;
      if (ctx?.spst_id) {
        conZonaSinTarifa += 1;
      } else {
        incidentesSinZona += 1;
        const inc = porId[a.incidenteId];
        if (inc) sucursalesSinZona.add(`${inc.empresaNombre ?? ""}|${inc.sucursalNombre ?? ""}`);
      }
    }
  }
  return {
    incidentesSinZona,
    sucursalesSinZona: sucursalesSinZona.size,
    conZonaSinTarifa,
    paresFueraTablaKm,
    total: incidentesSinZona + conZonaSinTarifa + paresFueraTablaKm,
  };
}

export function LiquidacionConfigBanner({
  alertas,
  incidentes,
}: {
  alertas: Alerta[];
  incidentes: Incidente[];
}) {
  const d = diagnosticoConfig(alertas, incidentes);
  if (d.total === 0) return null;
  const partes: string[] = [];
  if (d.incidentesSinZona > 0) {
    partes.push(
      `${d.sucursalesSinZona} sucursal(es) sin zona en Tabla KM (${d.incidentesSinZona} incidente(s)) — asignala desde "Gestionar" en la alerta ALT008`,
    );
  }
  if (d.conZonaSinTarifa > 0) {
    partes.push(`${d.conZonaSinTarifa} incidente(s) con zona pero sin tarifa cargada para su tipo y fecha`);
  }
  if (d.paresFueraTablaKm > 0) {
    partes.push(`${d.paresFueraTablaKm} incidente(s) cuya sucursal no está en Tabla KM (ALT009)`);
  }
  return (
    <div className="flex items-start gap-3 rounded-[12px] border border-border bg-muted/40 px-5 py-4">
      <Settings2 size={16} className="mt-0.5 flex-shrink-0 text-muted-foreground" />
      <div className="font-body text-sm text-foreground">
        <p className="font-semibold">
          {d.total} incidente(s) sin precio resoluble por configuración incompleta (no es un
          error del prestador).
        </p>
        <ul className="mt-1 list-disc pl-5 text-muted-foreground">
          {partes.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
