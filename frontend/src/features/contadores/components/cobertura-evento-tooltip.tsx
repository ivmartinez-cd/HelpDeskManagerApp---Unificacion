"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { CoberturaEvento } from "../types/calendario";
import { formatFechaCobertura } from "../utils/calendario-format";

/** Contenido del tooltip de un evento cubierto (§3.3.C del handoff de
 * reasignación temporal). El link "Ver detalle" lleva al ABM de coberturas
 * del módulo, donde vive la regla completa. */

function Fila({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2 font-body text-xs">
      <span className="w-24 flex-none text-muted-foreground">{label}</span>
      <span className="font-semibold text-foreground">{value}</span>
    </div>
  );
}

export function CoberturaEventoTooltip({ cobertura }: { cobertura: CoberturaEvento }) {
  const ausente = cobertura.operador_ausente_nombre ?? cobertura.operador_ausente_id;
  const reemplazante = cobertura.operador_reemplazante_nombre ?? cobertura.operador_reemplazante_id;
  return (
    <div className="flex flex-col gap-1.5">
      <p className="font-heading text-[11px] font-extrabold uppercase tracking-wide text-brand-orange">
        Cobertura activa
      </p>
      <Fila label="Ausente" value={`${ausente} (@${cobertura.operador_ausente_id})`} />
      <Fila
        label="Reemplazante"
        value={`${reemplazante} (@${cobertura.operador_reemplazante_id})`}
      />
      <Fila
        label="Vigencia"
        value={`${formatFechaCobertura(cobertura.vigente_desde)} → ${formatFechaCobertura(cobertura.vigente_hasta)}`}
      />
      <Fila label="Alcance" value={cobertura.alcance_total ? "Total" : "Clientes específicos"} />
      <Link
        href="/contadores/coberturas"
        className="mt-1 inline-flex items-center gap-1 font-body text-xs font-semibold text-brand-orange hover:underline"
      >
        Ver detalle
        <ArrowRight className="h-3 w-3" />
      </Link>
    </div>
  );
}
