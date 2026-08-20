"use client";

import { useId, useState } from "react";
import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import { cn } from "@/shared/utils/cn";
import { enlaceMaps } from "../lib/asistente-km-textos";

/** Piezas compartidas del Asistente de KM. Todo sobre el design system y el
 * patrón de fila que el wizard ya usaba; sin componentes visuales nuevos. */

/** Disclosure "ver detalle ▾": mismo patrón de link subrayado que el toggle de
 * ex-clientes del wizard anterior (decisión 0.4.i), accesible (aria-expanded). */
export function VerDetalle({ etiqueta = "ver detalle", children, className }: {
  etiqueta?: string; children: React.ReactNode; className?: string;
}) {
  const [abierto, setAbierto] = useState(false);
  const id = useId();
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <button
        type="button"
        aria-expanded={abierto}
        aria-controls={id}
        onClick={() => setAbierto((v) => !v)}
        className="self-start font-body text-xs text-muted-foreground underline-offset-2 hover:underline"
      >
        {etiqueta} {abierto ? "▴" : "▾"}
      </button>
      {abierto && (
        <div id={id} className="rounded-[6px] bg-muted/30 px-3 py-2 font-body text-xs text-muted-foreground">
          {children}
        </div>
      )}
    </div>
  );
}

export function EnlaceMaps({ latitud, longitud, children }: {
  latitud: number | null; longitud: number | null; children: React.ReactNode;
}) {
  if (latitud === null || longitud === null) return null;
  return (
    <a
      href={enlaceMaps(latitud, longitud)}
      target="_blank"
      rel="noopener noreferrer"
      className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline"
    >
      {children}
    </a>
  );
}

/** Fila de la bandeja: título + etiqueta + cuerpo + acciones. `destacada` = lo
 * que ya se sabe roto con certeza. */
export function FilaBandeja({ titulo, etiqueta, etiquetaVariant = "neutral", destacada = false, children, acciones, detalle }: {
  titulo: React.ReactNode;
  etiqueta?: string;
  etiquetaVariant?: BadgeVariant;
  destacada?: boolean;
  children: React.ReactNode;
  acciones?: React.ReactNode;
  detalle?: React.ReactNode;
}) {
  return (
    <li className={cn(
      "list-none rounded-[8px] border px-4 py-3 flex flex-col gap-2",
      destacada ? "border-destructive/40 bg-destructive/5" : "border-border",
    )}>
      <div className="flex items-start justify-between gap-3">
        <p className="font-body text-sm font-semibold text-foreground">{titulo}</p>
        {etiqueta && <Badge variant={etiquetaVariant} className="flex-shrink-0">{etiqueta}</Badge>}
      </div>
      <div className="font-body text-sm text-muted-foreground">{children}</div>
      {(acciones || detalle) && (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">{acciones}</div>
          {detalle && <VerDetalle etiqueta="ver detalle técnico">{detalle}</VerDetalle>}
        </div>
      )}
    </li>
  );
}

export function Aviso({ tono = "info", children }: { tono?: "info" | "alerta" | "bloqueo"; children: React.ReactNode }) {
  return (
    <div
      role={tono === "bloqueo" ? "alert" : "status"}
      className={cn(
        "rounded-[8px] border p-3 font-body text-sm text-foreground",
        tono === "info" && "border-border bg-muted/30",
        tono === "alerta" && "border-warning/40 bg-warning/5",
        tono === "bloqueo" && "border-destructive/40 bg-destructive/5",
      )}
    >
      {children}
    </div>
  );
}

export function Resultado({ children }: { children: React.ReactNode }) {
  return <p className="font-body text-sm font-semibold text-brand-orange">✓ {children}</p>;
}
