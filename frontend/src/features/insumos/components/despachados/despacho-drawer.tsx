"use client";

import { useState } from "react";
import { AlertTriangle, Copy, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { BrandDrawer } from "@/shared/components/ui/brand-drawer";
import { BrandButton, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { copiarTexto } from "@/shared/utils/clipboard";
import { cn } from "@/shared/utils/cn";
import { formatArgDate, formatArgTime } from "../../utils/format";
import type { DespachoDetalleState } from "../../hooks/use-despacho-detalle";
import type { DetalleDespacho } from "../../types/despachados";
import { ChipSemaforo } from "./despacho-celdas";
import { Acciones, Cambios, Cliente, EstadoActual, Remitos, Seccion } from "./despacho-detalle-secciones";
import { TONO } from "./semaforo";

/** Link genérico de OCA, igual que el mockup: OCA no publica una URL de
 * seguimiento por guía estable (anotado en el README del handoff). */
/** Seguimiento público de OCA para una guía. */
const urlSeguimientoOca = (guia: string) =>
  `https://oca.com.ar/Seguimiento/Paquetes/${encodeURIComponent(guia)}`;

interface Props {
  guia: string | null;
  estado: DespachoDetalleState;
  canUpdate: boolean;
  onClose: () => void;
  onRegistrar: (detalle: DetalleDespacho) => void;
  onReclamar: (guia: string) => void;
  onCerrarAlerta: (guia: string) => Promise<void>;
}

async function copiarGuia(guia: string) {
  try {
    await copiarTexto(guia);
    toast.success(`Guía ${guia} copiada`);
  } catch {
    toast.error("No se pudo copiar. Seleccioná la guía al pie del panel.");
  }
}

function RecuadroAlerta({ detalle, canUpdate, onCerrar }: {
  detalle: DetalleDespacho;
  canUpdate: boolean;
  onCerrar: () => Promise<void>;
}) {
  const [cerrando, setCerrando] = useState(false);
  const { envio } = detalle;
  if (!envio.alerta) return null;
  const clase = cn("mt-3.5 flex flex-col gap-2.5 rounded-[10px] border px-3.5 py-3 font-body text-[13px]", TONO[envio.color].alertBox);
  if (!envio.alertaAbierta) {
    const cierre = envio.cierreAlerta;
    return (
      <div className={clase}>
        <p>
          <b>Alerta cerrada</b>
          {cierre && ` por ${cierre.usuarioNombre} el ${formatArgDate(cierre.cerradaEn)} a las ${formatArgTime(cierre.cerradaEn)}`}.
        </p>
        <p className="text-xs text-muted-foreground">Si OCA informa un estado nuevo con problema, se abre otra alerta.</p>
      </div>
    );
  }
  const sinAcciones = detalle.acciones.length === 0;
  const porque = `why-${envio.guia}`;
  return (
    <div className={clase}>
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <p>
          <b>Alerta abierta</b> · {envio.color === "rojo" ? "retiro en sucursal pendiente" : "visita fallida"}
        </p>
        {canUpdate && (
          <BrandButton
            type="button"
            variant="outline"
            size="sm"
            className="rounded-[8px]"
            disabled={sinAcciones}
            loading={cerrando}
            aria-describedby={sinAcciones ? porque : undefined}
            onClick={async () => {
              setCerrando(true);
              try {
                await onCerrar();
              } finally {
                setCerrando(false);
              }
            }}
          >
            Cerrar alerta
          </BrandButton>
        )}
      </div>
      {sinAcciones && (
        <p id={porque} className="text-xs text-muted-foreground">
          Para cerrar la alerta registrá al menos una acción.
        </p>
      )}
    </div>
  );
}

function subtituloDe(detalle: DetalleDespacho): string {
  const incidente = detalle.remitos.flatMap((r) => r.incidentes)[0]?.numero;
  return incidente ? `${detalle.envio.cliente} · Incidente ${incidente}` : detalle.envio.cliente;
}

/** Panel lateral con el detalle de una guía (`GET /despachados/{guia}`). */
export function DespachoDrawer({ guia, estado, canUpdate, onClose, onRegistrar, onReclamar, onCerrarAlerta }: Props) {
  const { detalle, error } = estado;
  const envio = detalle?.envio;
  return (
    <BrandDrawer
      isOpen={guia !== null}
      onClose={onClose}
      eyebrow={envio && <ChipSemaforo color={envio.color} estado={envio.estadoOca?.estado ?? ""} observacion={envio.observacion} />}
      title={
        <>
          Guía {guia}
          {guia && (
            <button
              type="button"
              onClick={() => void copiarGuia(guia)}
              aria-label="Copiar número de guía"
              title="Copiar guía"
              className="inline-flex cursor-pointer rounded-[6px] p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <Copy className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          )}
        </>
      }
      subtitle={detalle ? subtituloDe(detalle) : undefined}
      footer={
        <>
          <a
            href={guia ? urlSeguimientoOca(guia) : undefined}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 font-body text-sm font-bold text-[#b45f06] no-underline hover:underline dark:text-brand-orange"
          >
            <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            Ver en OCA
          </a>
          <span className="font-body text-xs text-muted-foreground">
            Guía para el seguimiento: <span className="select-all tabular-nums">{guia}</span>
          </span>
        </>
      }
    >
      {error && !detalle && (
        <div role="alert" className="mt-4 flex items-start gap-2.5 rounded-[10px] border border-destructive/20 bg-destructive/10 p-3 font-body text-[13px] text-destructive">
          <AlertTriangle className="h-4 w-4 flex-none" aria-hidden="true" />
          {error}
        </div>
      )}
      {!detalle && !error && (
        <div className="flex flex-col gap-3 py-5">
          <BrandSkeleton className="h-6 w-2/3" />
          <BrandSkeleton className="h-24 w-full" />
          <BrandSkeleton className="h-24 w-full" />
        </div>
      )}
      {detalle && (
        <>
          <Seccion titulo="Estado OCA actual">
            <EstadoActual detalle={detalle} />
            <RecuadroAlerta
              detalle={detalle}
              canUpdate={canUpdate}
              onCerrar={() => onCerrarAlerta(detalle.envio.guia)}
            />
          </Seccion>
          <Remitos detalle={detalle} />
          <Cliente detalle={detalle} />
          <Cambios detalle={detalle} />
          <Acciones
            detalle={detalle}
            accion={
              canUpdate && (
                <div className="flex flex-wrap gap-2">
                  <BrandButton type="button" variant="outline" size="sm" className="rounded-[8px] normal-case tracking-normal" onClick={() => onReclamar(detalle.envio.guia)}>
                    Reclamar en OCA
                  </BrandButton>
                  <BrandButton type="button" size="sm" className="rounded-[8px] normal-case tracking-normal" onClick={() => onRegistrar(detalle)}>
                    Registrar acción
                  </BrandButton>
                </div>
              )
            }
          />
        </>
      )}
    </BrandDrawer>
  );
}
