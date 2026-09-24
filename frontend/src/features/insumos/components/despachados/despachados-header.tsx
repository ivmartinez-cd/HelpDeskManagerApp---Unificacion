"use client";

import { Clock, RefreshCw } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { formatArgTime } from "../../utils/format";
import type { EstadoActualizacionDespachos } from "../../types/despachados";

/** Cabecera: migas, título, "Última consulta a OCA" y "Actualizar ahora". La
 * hora sale de la última corrida terminada (`/despachados/actualizacion`): la
 * pantalla nunca espera a OCA, lee lo que el job ya guardó en HDM. */
interface Props {
  estado: EstadoActualizacionDespachos | null;
  enCurso: boolean;
  canUpdate: boolean;
  onActualizar: () => void;
}

export function DespachadosHeader({ estado, enCurso, canUpdate, onActualizar }: Props) {
  const ultima = estado?.ultimaTerminada;
  const hora = ultima ? formatArgTime(ultima.terminadaEn ?? ultima.iniciadaEn) : "—";
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="mb-1 font-body text-xs text-muted-foreground">Insumos / Despachados</p>
        <h1 className="font-heading text-[25px] font-extrabold leading-[1.2] tracking-[-.005em] text-foreground">
          Despachados
        </h1>
        <p className="mt-1 font-body text-sm text-muted-foreground">
          Estado en vivo de los envíos por OCA.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3.5">
        <span className="inline-flex items-center gap-1.5 font-body text-[13px] text-muted-foreground">
          <Clock className="h-3.5 w-3.5" aria-hidden="true" />
          Última consulta a OCA:{" "}
          <b className="font-bold tabular-nums text-foreground">{hora}</b>
        </span>
        {canUpdate && (
          <BrandButton type="button" onClick={onActualizar} disabled={enCurso} aria-busy={enCurso}>
            <RefreshCw className={cn("h-4 w-4", enCurso && "animate-spin")} aria-hidden="true" />
            {enCurso ? "Actualizando…" : "Actualizar ahora"}
          </BrandButton>
        )}
      </div>
      <p className="sr-only" aria-live="polite">
        {enCurso ? "Actualizando estados desde OCA" : ""}
      </p>
    </div>
  );
}
