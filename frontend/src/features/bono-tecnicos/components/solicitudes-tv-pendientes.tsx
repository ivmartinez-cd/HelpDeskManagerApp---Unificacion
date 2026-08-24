"use client";

import { useState } from "react";
import { useSolicitudesTvPendientes } from "../hooks/use-solicitudes-tv-pendientes";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";

interface Props {
  periodo: string;
  enabled: boolean;
}

export function SolicitudesTvPendientes({ periodo, enabled }: Props) {
  const { solicitudes, loading, decidingId, error, decidir } = useSolicitudesTvPendientes(
    periodo,
    enabled,
  );
  const [motivoPorId, setMotivoPorId] = useState<Record<string, string>>({});

  if (!enabled) return null;

  return (
    <div className="flex flex-col gap-3 rounded-[12px] border border-border bg-card p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-lg font-bold text-foreground">
          Solicitudes de TV pendientes
        </h2>
        {!loading && solicitudes.length > 0 && (
          <span className="font-body text-xs font-bold uppercase tracking-wide text-muted-foreground">
            {solicitudes.length} pendiente{solicitudes.length === 1 ? "" : "s"}
          </span>
        )}
      </div>

      {loading && (
        <div className="flex h-24 items-center justify-center">
          <Spinner />
        </div>
      )}
      {!loading && error && <p className="font-body text-sm text-destructive">{error}</p>}
      {!loading && !error && solicitudes.length === 0 && (
        <p className="font-body text-sm text-muted-foreground">
          Sin solicitudes pendientes en este período.
        </p>
      )}
      {!loading && !error && solicitudes.length > 0 && (
        <div className="flex flex-col gap-3">
          {solicitudes.map((s) => (
            <div
              key={s.id}
              className="flex flex-col gap-2 rounded-[8px] border border-border p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex flex-col gap-0.5">
                <p className="font-body text-sm font-bold text-foreground">
                  {s.tecnico} — {s.fecha}
                </p>
                <p className="font-body text-sm text-muted-foreground">
                  {s.razon_social} / {s.sucursal}
                </p>
                <p className="font-body text-sm text-foreground">{s.tarea_realizada}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type="text"
                  placeholder="Motivo si rechazás (opcional)"
                  value={motivoPorId[s.id] ?? ""}
                  onChange={(e) =>
                    setMotivoPorId((m) => ({ ...m, [s.id]: e.target.value }))
                  }
                  className="rounded-[8px] border border-border bg-background px-2 py-1 font-body text-xs text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
                />
                <BrandButton
                  type="button"
                  variant="outline"
                  size="sm"
                  loading={decidingId === s.id}
                  onClick={() => decidir(s.id, "RECHAZADA", motivoPorId[s.id] || undefined)}
                >
                  Rechazar
                </BrandButton>
                <BrandButton
                  type="button"
                  size="sm"
                  loading={decidingId === s.id}
                  onClick={() => decidir(s.id, "APROBADA")}
                >
                  Aprobar
                </BrandButton>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
