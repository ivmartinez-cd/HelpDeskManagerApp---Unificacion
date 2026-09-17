"use client";

import { useMemo, useState } from "react";
import type { GrillaVariante, VarianteSlot } from "../../types/grilla-variantes";
import {
  DIAS_SEMANA,
  diaInicialVigente,
  diaSemanaDeIso,
  diasActivosDeRango,
} from "../../lib/variante-validacion";
import { formatFecha, hhmm, hoyIso } from "../../lib/variante-estado";
import { TurnosTimeline, type TimelineShift } from "../turnos-timeline";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";

interface VariantePreviewModalProps {
  variante: GrillaVariante;
  /** Orden de casillas del admin (nombres), para que los tracks salgan como en Inicio. */
  ordenCasillas: string[];
  onClose: () => void;
}

/** Firma de un día para detectar días idénticos (el caso típico: L–V iguales). */
function firmaDia(slots: VarianteSlot[]): string {
  return slots
    .map((s) => `${s.casillaNombre}|${hhmm(s.horaInicio)}|${hhmm(s.horaFin)}|${s.operadores.map((o) => o.userId).join(",")}`)
    .sort()
    .join(";");
}

function aTimeline(slots: VarianteSlot[]): TimelineShift[] {
  return slots.map((s) => ({
    key: s.id,
    casillaNombre: s.casillaNombre,
    horaInicio: s.horaInicio,
    horaFin: s.horaFin,
    operadores: s.operadores,
  }));
}

/** Vista previa de una grilla de vacaciones con el mismo timeline de
 * "Turnos del día" (ADR-025): lo que ve la TL acá es exactamente lo que van
 * a ver los operadores en Inicio durante la vigencia. Si todos los días con
 * franjas son idénticos se muestra un solo timeline; si no, pestañas por día. */
export function VariantePreviewModal({ variante, ordenCasillas, onClose }: VariantePreviewModalProps) {
  // Sólo los días que la vigencia alcanza: mostrar un lunes en una grilla que
  // corre de martes a viernes hace creer que ese día se va a aplicar.
  const porDia = useMemo(() => {
    const delRango = diasActivosDeRango(variante.desde, variante.hasta);
    const mapa = new Map<number, VarianteSlot[]>();
    for (const s of variante.slots) {
      if (delRango && !delRango.has(s.diaSemana)) continue;
      mapa.set(s.diaSemana, [...(mapa.get(s.diaSemana) ?? []), s]);
    }
    return Array.from(mapa.entries()).sort(([a], [b]) => a - b);
  }, [variante.slots, variante.desde, variante.hasta]);

  const dias = porDia.map(([d]) => d);
  const todosIguales = porDia.length > 1 && new Set(porDia.map(([, s]) => firmaDia(s))).size === 1;
  // Arranca en el día de hoy cuando la grilla ya está vigente: es el que se
  // contrasta contra Turnos del día.
  const [diaActivo, setDiaActivo] = useState<number>(() =>
    diaInicialVigente(undefined, diaSemanaDeIso(hoyIso()), dias),
  );
  const slotsVisibles = todosIguales ? porDia[0][1] : (porDia.find(([d]) => d === diaActivo)?.[1] ?? []);

  const rotuloDias = todosIguales
    ? dias.length === 5 && dias[0] === 0 && dias[4] === 4
      ? "Lunes a viernes"
      : dias.map((d) => DIAS_SEMANA[d]).join(", ")
    : DIAS_SEMANA[diaActivo];

  const titulo = variante.motivo ?? "Grilla de vacaciones";
  const subtitulo = `${formatFecha(variante.desde)} → ${formatFecha(variante.hasta)}`;

  return (
    <BrandModal isOpen onClose={onClose} title={`Grilla de vacaciones · ${titulo}`} widthPx={900}>
      <div className="flex flex-col gap-4" data-testid="variante-preview">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="font-body text-sm text-muted-foreground">
            Vigencia {subtitulo} · {rotuloDias}
            {todosIguales && " (igual todos los días)"}
          </p>
          {!todosIguales && porDia.length > 1 && (
            <SegmentedControl
              label="Día"
              size="sm"
              options={dias.map((d) => ({ value: String(d), label: DIAS_SEMANA[d] }))}
              value={String(diaActivo)}
              onChange={(v) => setDiaActivo(Number(v))}
            />
          )}
        </div>
        <div className="rounded-[12px] border border-border bg-card px-4 pb-4 pt-1">
          <TurnosTimeline
            shifts={aTimeline(slotsVisibles)}
            ordenCasillas={ordenCasillas}
            emptyText="Sin franjas para este día."
          />
        </div>
        <p className="font-body text-xs text-muted-foreground">
          Así se va a ver “Turnos del día” en Inicio durante la vigencia. Al vencer, vuelve la grilla
          titular.
        </p>
      </div>
    </BrandModal>
  );
}
