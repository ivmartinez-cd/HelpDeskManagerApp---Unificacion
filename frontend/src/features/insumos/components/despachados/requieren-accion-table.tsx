"use client";

import type { KeyboardEvent } from "react";
import { BrandButton, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { FilaDespacho } from "../../types/despachados";
import {
  ChipSemaforo,
  ConExtra,
  EstadoOcaCelda,
  TD,
  TH,
  UltimaAccionCelda,
  claseFila,
} from "./despacho-celdas";
import { TONO, textoLimite } from "./semaforo";

/** Activa una fila con Enter/Espacio (el click lo maneja `onClick`). */
export function alTeclearFila(e: KeyboardEvent<HTMLTableRowElement>, abrir: () => void) {
  if (e.target !== e.currentTarget) return;
  if (e.key !== "Enter" && e.key !== " ") return;
  e.preventDefault();
  abrir();
}

interface Props {
  filas: FilaDespacho[];
  loading: boolean;
  seleccionada: string | null;
  canUpdate: boolean;
  onAbrir: (guia: string) => void;
  onRegistrar: (fila: FilaDespacho) => void;
}

/** Bandeja "Requieren acción": rojos y naranjas con la alerta abierta, en el
 * orden en que los devuelve el backend (lo que vence antes, primero). */
export function RequierenAccionTable({
  filas,
  loading,
  seleccionada,
  canUpdate,
  onAbrir,
  onRegistrar,
}: Props) {
  return (
    <section aria-labelledby="despachados-bandeja" className="rounded-[12px] border border-border bg-card">
      <div className="border-b border-border px-5 py-4">
        <h2 id="despachados-bandeja" className="flex items-center gap-2 font-heading text-base font-bold leading-6 text-foreground">
          Requieren acción
          {!loading && (
            <span className="inline-flex h-[22px] min-w-[22px] items-center justify-center rounded-full bg-[#c2410c] px-1.5 font-body text-xs font-bold tabular-nums text-white">
              {filas.length}
            </span>
          )}
        </h2>
        <p className="mt-0.5 font-body text-[13px] text-muted-foreground">
          Visitas fallidas y envíos esperando en sucursal. Primero lo que vence antes.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              {["Color", "Guía", "Cliente", "Incidente", "Estado OCA", "Sucursal", "Límite", "Última acción"].map((h) => (
                <th key={h} scope="col" className={TH}>{h}</th>
              ))}
              <th scope="col" className={TH}><span className="sr-only">Acción</span></th>
            </tr>
          </thead>
          <tbody>
            {loading && filas.length === 0 ? (
              <tr>
                <td colSpan={9} className="p-5"><BrandSkeleton className="h-16 w-full" /></td>
              </tr>
            ) : filas.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-5 py-9 text-center font-body text-[13px] text-muted-foreground">
                  <b className="mb-0.5 block text-foreground">No hay envíos que requieran acción</b>
                  Las visitas fallidas y los envíos en sucursal aparecen acá apenas OCA los informa.
                </td>
              </tr>
            ) : (
              filas.map((f) => (
                <tr
                  key={f.guia}
                  tabIndex={0}
                  className={claseFila(seleccionada === f.guia)}
                  onClick={() => onAbrir(f.guia)}
                  onKeyDown={(e) => alTeclearFila(e, () => onAbrir(f.guia))}
                >
                  <td className={TD}><ChipSemaforo color={f.color} estado={f.estado} observacion={f.observacion} /></td>
                  <td className={cn(TD, "whitespace-nowrap font-semibold tabular-nums tracking-[.01em]")}>{f.guia}</td>
                  <td className={TD}>{f.cliente}</td>
                  <td className={cn(TD, "tabular-nums")}><ConExtra valor={f.incidente} cantidad={f.cantidadIncidentes} /></td>
                  <td className={TD}><EstadoOcaCelda fila={f} /></td>
                  <td className={TD}>{f.sucursalOca || "—"}</td>
                  <td className={TD}>
                    {f.color === "rojo" && f.fechaLimite ? (
                      <span className={cn("whitespace-nowrap font-bold", TONO.rojo.text)}>
                        {textoLimite(f.fechaLimite, f.diasHabilesParaLimite)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className={TD}><UltimaAccionCelda accion={f.ultimaAccion} /></td>
                  <td className={cn(TD, "whitespace-nowrap")}>
                    {canUpdate && (
                      <BrandButton
                        type="button"
                        variant="outline"
                        size="sm"
                        className="rounded-[8px]"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRegistrar(f);
                        }}
                        onKeyDown={(e) => e.stopPropagation()}
                      >
                        Registrar acción
                      </BrandButton>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
