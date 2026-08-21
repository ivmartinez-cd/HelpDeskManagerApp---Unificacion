"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardCheck } from "lucide-react";
import {
  BrandButton,
  BrandEmptyState,
  BrandSelect,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { solicitudesApi } from "../api/solicitudes-api";
import { formatRango } from "../lib/fechas";
import type { Solicitud } from "../types/vacaciones";
import { AprobacionCard } from "./aprobacion-card";
import { avisoDeVacaciones, AvisoAfectaTurnos } from "./aviso-afecta-turnos";
import { NovedadesPendientes, type AvisoTurnos } from "./novedades-aprobacion";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";

export function AprobacionesView() {
  const [solicitudes, setSolicitudes] = useState<Solicitud[] | null>(null);
  const [soloPendientes, setSoloPendientes] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [avisoTurnos, setAvisoTurnos] = useState<AvisoTurnos | null>(null);

  const load = useCallback(
    () =>
      solicitudesApi
        .list()
        .then((items) => {
          setSolicitudes(items);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar aprobaciones:", err);
          setError("No se pudieron cargar las solicitudes. Intentá de nuevo.");
        }),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const pendientes = useMemo(
    () => (solicitudes ?? []).filter((s) => s.status === "PENDING"),
    [solicitudes],
  );
  const listadas = soloPendientes ? pendientes : (solicitudes ?? []);
  const historial = useMemo(
    () => (solicitudes ?? []).filter((s) => s.aprobaciones.length > 0),
    [solicitudes],
  );

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Aprobaciones
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Revisá, aprobá o rechazá las solicitudes de vacaciones, home office y cambios de
            horario
          </p>
        </div>
        <div className="min-w-[180px]">
          <BrandSelect
            label="Mostrar"
            value={soloPendientes ? "pendientes" : "todas"}
            onChange={(e) => setSoloPendientes(e.target.value === "pendientes")}
          >
            <option value="pendientes">Sólo pendientes</option>
            <option value="todas">Todas</option>
          </BrandSelect>
        </div>
      </div>

      {solicitudes === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }, (_, i) => (
            <BrandSkeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {avisoTurnos && (
        <AvisoAfectaTurnos decision={avisoTurnos} onClose={() => setAvisoTurnos(null)} />
      )}

      <NovedadesPendientes onDecided={setAvisoTurnos} />

      {solicitudes !== null && !error && (
        <>
          <section className="flex flex-col gap-3">
            <h2 className="font-heading text-sm font-bold uppercase tracking-[.05em] text-foreground">
              Vacaciones pendientes de aprobación{" "}
              <span className="ml-1 rounded-[20px] bg-amber-500/15 px-2 py-0.5 font-body text-xs text-amber-600 dark:text-amber-400">
                {pendientes.length}
              </span>
            </h2>
            {listadas.length === 0 ? (
              <BrandEmptyState
                icon={ClipboardCheck}
                title="No hay solicitudes para mostrar"
                description="Cuando alguien pida vacaciones vas a verlas acá."
              />
            ) : (
              listadas.map((s) => (
                <AprobacionCard
                  key={s.id}
                  solicitud={s}
                  onDecided={(res) => {
                    setAvisoTurnos(avisoDeVacaciones(res));
                    void load();
                  }}
                />
              ))
            )}
          </section>

          {historial.length > 0 && (
            <section className="flex flex-col gap-3">
              <h2 className="font-heading text-sm font-bold uppercase tracking-[.05em] text-foreground">
                Historial de decisiones
              </h2>
              <div className="overflow-x-auto rounded-[12px] border border-border">
                <table className="w-full min-w-[720px] font-body text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                      <th className="px-4 py-3">Empleado</th>
                      <th className="px-4 py-3">Rango</th>
                      <th className="px-4 py-3 text-right">Días</th>
                      <th className="px-4 py-3">Decisión</th>
                      <th className="px-4 py-3">Decisor</th>
                      <th className="px-4 py-3">Comentario</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historial.map((s) => {
                      const ultima = s.aprobaciones[0];
                      return (
                        <tr key={s.id} className="border-b border-border/60 last:border-0">
                          <td className="px-4 py-3 font-semibold text-foreground">
                            {s.empleadoNombre}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {formatRango(s.startDate, s.endDate)}
                          </td>
                          <td className="px-4 py-3 text-right text-foreground">
                            {s.daysRequested}
                          </td>
                          <td className="px-4 py-3">
                            <SolicitudEstadoBadge
                              estado={ultima.decision === "APPROVED" ? "APPROVED" : "REJECTED"}
                            />
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {ultima.approverEmail ?? "—"}
                          </td>
                          <td className="max-w-[220px] truncate px-4 py-3 text-muted-foreground">
                            {ultima.comment ?? "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
