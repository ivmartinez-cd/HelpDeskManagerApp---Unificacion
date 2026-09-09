"use client";

import { ESTADO_ALERTA_STYLES, ESTADO_ALERTA_TONO } from "../lib/alerta-estados";
import type { EstadoAlerta } from "../types/liquidaciones";

/** Insignia de estado de una alerta con ícono redundante al color y texto
 * más grande que el `Badge` genérico (10px) — pensada para no depender de
 * distinguir el matiz. Variante A del mockup acordado con Iván, 2026-09-08. */
export function AlertaEstadoBadge({ estado }: { estado: EstadoAlerta }) {
  const estilo = ESTADO_ALERTA_STYLES[estado] ?? ESTADO_ALERTA_STYLES.pendiente;
  const tono = ESTADO_ALERTA_TONO[estado] ?? ESTADO_ALERTA_TONO.pendiente;
  const Icon = tono.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 font-body text-xs font-bold uppercase tracking-wide ${tono.pillBg} ${tono.pillText}`}
    >
      <Icon size={14} strokeWidth={2.4} aria-hidden="true" />
      {estilo.label}
    </span>
  );
}
