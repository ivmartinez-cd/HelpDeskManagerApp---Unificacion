"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { NombreCandidato, NombreSinCandidato } from "../lib/asistente-km-bandeja";
import type { CandidatoN2Match } from "../types/liquidaciones";
import { FilaBandeja, VerDetalle } from "./tabla-km-wizard-ui";

function Candidato({ tablaKmId, candidato, principal, onResuelto }: {
  tablaKmId: string; candidato: CandidatoN2Match; principal: boolean; onResuelto: () => Promise<void>;
}) {
  const [ejecutando, setEjecutando] = useState<"si" | "no" | null>(null);
  const responder = async (es: boolean) => {
    setEjecutando(es ? "si" : "no");
    try {
      if (es) {
        await liquidacionesApi.confirmarVinculo(tablaKmId, candidato.sigesSucursalId);
        toast.success(`${candidato.sucursalNombre}: vínculo confirmado`);
      } else {
        await liquidacionesApi.rechazarPropuesta(tablaKmId, candidato.sigesSucursalId);
      }
      await onResuelto();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "No se pudo guardar la respuesta");
    } finally { setEjecutando(null); }
  };
  return (
    <div className="flex items-center justify-between gap-3 rounded-[6px] border border-border/70 bg-muted/20 px-3 py-2">
      <div className="min-w-0">
        <p className="flex items-center gap-2 font-body text-sm font-semibold text-foreground">
          <span className="truncate">{candidato.sucursalNombre}</span>
          {candidato.mismaDireccion && <Badge variant="success">misma dirección</Badge>}
        </p>
        <p className="truncate font-body text-xs text-muted-foreground">{candidato.domicilio ?? "sin domicilio en Gestión"}</p>
      </div>
      <div className="flex flex-shrink-0 items-center gap-2">
        <BrandButton size="sm" variant="outline" loading={ejecutando === "no"} disabled={ejecutando !== null} onClick={() => responder(false)}>
          No es esta
        </BrandButton>
        <BrandButton size="sm" variant={principal ? "primary" : "outline"} loading={ejecutando === "si"} disabled={ejecutando !== null} onClick={() => responder(true)}>
          Sí, es esta
        </BrandButton>
      </div>
    </div>
  );
}

/** Una fila de la Tabla KM cuyo nombre no aparece igual en Gestión, con candidatos:
 * cada uno requiere tu confirmación (nunca se vincula solo). */
export function ItemNombreCandidato({ item, onCambio }: { item: NombreCandidato; onCambio: () => Promise<void> }) {
  const [verMas, setVerMas] = useState(false);
  const { propuesta } = item;
  const [primero, ...resto] = propuesta.candidatos;
  const visibles = verMas ? propuesta.candidatos : [primero];
  return (
    <FilaBandeja
      titulo={<>¿&quot;{propuesta.sucursalNombre}&quot; es esta sucursal de Gestión?</>}
      etiqueta="nombre"
      etiquetaVariant="info"
      acciones={resto.length > 0 && (
        <button
          type="button"
          aria-expanded={verMas}
          onClick={() => setVerMas((v) => !v)}
          className="font-body text-xs text-muted-foreground underline-offset-2 hover:underline"
        >
          {verMas ? "Ver menos candidatos ▴" : `Ver ${resto.length} candidato${resto.length !== 1 ? "s" : ""} más ▾`}
        </button>
      )}
      detalle={
        <ul className="flex flex-col gap-0.5">
          {propuesta.candidatos.map((c) => (
            <li key={c.sigesSucursalId}>{c.sucursalNombre}: {Math.round(c.score * 100)}% · {c.motivo}</li>
          ))}
        </ul>
      }
    >
      <p className="mb-2 text-xs">
        Empresa: {propuesta.empresaNombre}.
        {propuesta.candidatos.some((c) => c.mismaDireccion) && " Hay una sucursal de Gestión con la misma dirección: puede ser esta misma, renombrada."}
        {" "}Si no es ninguna, respondé &quot;No es esta&quot; y no se vuelve a proponer.
      </p>
      <div className="flex flex-col gap-1.5">
        {visibles.map((c, i) => (
          <Candidato key={c.sigesSucursalId} tablaKmId={propuesta.tablaKmId} candidato={c} principal={i === 0} onResuelto={onCambio} />
        ))}
      </div>
    </FilaBandeja>
  );
}

/** Fila sin ningún candidato en Gestión: se resuelve a mano. */
export function ItemNombreSinCandidato({ item }: { item: NombreSinCandidato }) {
  const { fila } = item;
  return (
    <FilaBandeja titulo={`No encontramos "${fila.sucursalNombre}" en Gestión`} etiqueta="a mano" etiquetaVariant="neutral">
      <p>Empresa: {fila.empresaNombre}. Su domicilio no se actualizó.</p>
      <p>Corregí el nombre de la fila en la Tabla KM (botón Editar) o dala de baja si ya no se atiende.</p>
      <VerDetalle className="mt-1">
        Puede que la sucursal haya cambiado de nombre en Gestión, o que ya no esté asignada a este prestador.
        El asistente solo propone candidatos cuando el nombre se parece lo suficiente.
      </VerDetalle>
    </FilaBandeja>
  );
}
