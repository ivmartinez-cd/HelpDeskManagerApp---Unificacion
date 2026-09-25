"use client";

import { useEffect, useState } from "react";
import { solicitudesApi } from "../api/solicitudes-api";
import { finInclusivo, rangoSemanaProxima } from "../lib/calendario";
import { formatRango, iniciales } from "../lib/fechas";
import type { EventoCalendario } from "../types/vacaciones";

/** Vacaciones (aprobadas y pendientes) que tocan la semana siguiente, con su
 * propia consulta para no depender del mes que muestre la grilla. */
export function VacacionesSemanaProxima({ hoy }: { hoy: string }) {
  const [eventos, setEventos] = useState<EventoCalendario[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const { desde, hasta } = rangoSemanaProxima(hoy);
    solicitudesApi
      .calendario(desde, hasta)
      .then((evs) =>
        setEventos(
          evs
            .filter((e) => e.tipo === "vacation" && e.status !== "REJECTED")
            .sort((a, b) => a.start.localeCompare(b.start)),
        ),
      )
      .catch((err: unknown) => {
        console.error("Error al cargar vacaciones de la semana próxima:", err);
        setError(true);
      });
  }, [hoy]);

  return (
    <div className="flex flex-col gap-3 border-t border-border pt-4">
      <h2 className="font-heading text-sm font-bold text-foreground">
        Vacaciones la semana que viene
      </h2>
      {error ? (
        <p className="font-body text-sm text-muted-foreground">No se pudo cargar.</p>
      ) : eventos === null ? null : eventos.length === 0 ? (
        <p className="font-body text-sm text-muted-foreground">
          Nadie tiene vacaciones la semana que viene
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {eventos.map((e) => (
            <FilaEvento key={e.id} evento={e} />
          ))}
        </div>
      )}
    </div>
  );
}

function FilaEvento({ evento: e }: { evento: EventoCalendario }) {
  const nombre = e.empleado ?? e.title;
  const pendiente = e.status === "PENDING";
  return (
    <div className="flex items-center gap-3 rounded-[10px] bg-muted/30 px-3.5 py-3">
      <span
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] font-heading text-xs font-bold text-white"
        style={{ backgroundColor: e.color, opacity: pendiente ? 0.55 : 1 }}
      >
        {iniciales(nombre)}
      </span>
      <div className="min-w-0">
        <p className="truncate font-body text-sm font-semibold text-foreground">{nombre}</p>
        <p className="font-body text-xs text-muted-foreground">
          {formatRango(e.start, finInclusivo(e))}
          {e.sector && ` · ${e.sector}`}
          {pendiente && " · Pendiente"}
        </p>
      </div>
    </div>
  );
}
