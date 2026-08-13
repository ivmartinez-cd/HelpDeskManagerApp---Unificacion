"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarX2, Plus } from "lucide-react";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { gestionApi } from "../api/gestion-api";
import { solicitudesApi } from "../api/solicitudes-api";
import { formatFecha, iniciales } from "../lib/fechas";
import type { EmpleadoListItem, EstadoSolicitud, Solicitud } from "../types/vacaciones";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";
import { SolicitudModal } from "./solicitud-modal";

const FILTROS: { value: "todas" | EstadoSolicitud; label: string }[] = [
  { value: "todas", label: "Todas" },
  { value: "PENDING", label: "Pendiente" },
  { value: "APPROVED", label: "Aprobada" },
  { value: "REJECTED", label: "Rechazada" },
];

export function SolicitudesView() {
  const { user, can } = useSession();
  const esAdmin = user.isSuperadmin || can("vacaciones", "manage");
  const puedeCrear = esAdmin || can("vacaciones", "create");

  const [solicitudes, setSolicitudes] = useState<Solicitud[] | null>(null);
  const [empleados, setEmpleados] = useState<EmpleadoListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<"todas" | EstadoSolicitud>("todas");
  const [busqueda, setBusqueda] = useState("");
  const [creando, setCreando] = useState(false);
  const [editando, setEditando] = useState<Solicitud | null>(null);
  const [eliminando, setEliminando] = useState<Solicitud | null>(null);
  const [eliminandoBusy, setEliminandoBusy] = useState(false);

  const load = useCallback(() => {
    const conEmpleados = esAdmin
      ? gestionApi.listEmpleados()
      : Promise.resolve([] as EmpleadoListItem[]);
    return Promise.all([solicitudesApi.list(), conEmpleados])
      .then(([items, emps]) => {
        setSolicitudes(items);
        setEmpleados(emps);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar solicitudes:", err);
        setError("No se pudieron cargar las solicitudes. Intentá de nuevo.");
      });
  }, [esAdmin]);

  useEffect(() => {
    void load();
  }, [load]);

  const visibles = useMemo(() => {
    if (!solicitudes) return [];
    const q = busqueda.trim().toLowerCase();
    return solicitudes.filter((s) => {
      if (filtro !== "todas" && s.status !== filtro) return false;
      if (!q) return true;
      return [s.empleadoNombre, s.reason ?? "", s.sectorNombre].some((v) =>
        v.toLowerCase().includes(q),
      );
    });
  }, [solicitudes, filtro, busqueda]);

  const handleEliminar = () => {
    if (!eliminando) return;
    setEliminandoBusy(true);
    solicitudesApi
      .remove(eliminando.id)
      .then(() => {
        setEliminando(null);
        return load();
      })
      .catch((err: unknown) => {
        setError(
          err instanceof ApiError ? err.message : "No se pudo eliminar la solicitud.",
        );
        setEliminando(null);
      })
      .finally(() => setEliminandoBusy(false));
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Mis Solicitudes
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Creá y gestioná las solicitudes de vacaciones
          </p>
        </div>
        {puedeCrear && (
          <BrandButton onClick={() => setCreando(true)}>
            <Plus className="h-4 w-4" />
            Nueva solicitud
          </BrandButton>
        )}
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[240px]">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Por empleado, motivo o sector…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
        <SegmentedControl
          label="Estado"
          size="sm"
          options={FILTROS}
          value={filtro}
          onChange={(v) => setFiltro(v as typeof filtro)}
        />
      </div>

      {solicitudes === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }, (_, i) => (
            <BrandSkeleton key={i} className="h-14 w-full" />
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

      {solicitudes !== null && !error && (
        <>
          {visibles.length === 0 ? (
            <BrandEmptyState
              icon={CalendarX2}
              title="No hay solicitudes todavía"
              description="Creá una solicitud para pedir tus vacaciones."
            />
          ) : (
            <div className="overflow-x-auto rounded-[12px] border border-border">
              <table className="w-full min-w-[860px] font-body text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                    <th className="px-4 py-3">Empleado</th>
                    <th className="px-4 py-3">Rango</th>
                    <th className="px-4 py-3 text-right">Días</th>
                    <th className="px-4 py-3 text-right">Año cargo</th>
                    <th className="px-4 py-3">Estado</th>
                    <th className="px-4 py-3">Motivo</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {visibles.map((s) => (
                    <tr key={s.id} className="border-b border-border/60 last:border-0">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <span
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] font-heading text-[11px] font-bold text-white"
                            style={{ backgroundColor: s.empleadoColor }}
                          >
                            {iniciales(s.empleadoNombre)}
                          </span>
                          <div>
                            <div className="font-semibold text-foreground">
                              {s.empleadoNombre}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {s.sectorNombre}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-foreground">{formatFecha(s.startDate)}</div>
                        <div className="text-xs text-muted-foreground">
                          → {formatFecha(s.endDate)}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="font-semibold text-foreground">
                          {s.daysRequested}
                        </span>{" "}
                        <span className="text-xs text-muted-foreground">hábiles</span>
                      </td>
                      <td className="px-4 py-3 text-right text-muted-foreground">
                        {s.chargedToYear ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        <SolicitudEstadoBadge estado={s.status} />
                      </td>
                      <td className="max-w-[180px] truncate px-4 py-3 text-muted-foreground">
                        {s.reason ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => setEditando(s)}
                            className="rounded-[8px] border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => setEliminando(s)}
                            className="rounded-[8px] border border-destructive/40 px-3 py-1.5 text-xs font-semibold text-destructive hover:bg-destructive/10"
                          >
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {(creando || editando) && (
        <SolicitudModal
          solicitud={editando}
          empleados={empleados}
          onClose={() => {
            setCreando(false);
            setEditando(null);
          }}
          onSaved={() => {
            setCreando(false);
            setEditando(null);
            void load();
          }}
        />
      )}

      {eliminando && (
        <BrandModal
          isOpen
          onClose={() => setEliminando(null)}
          title="Eliminar solicitud"
          widthPx={440}
        >
          <p className="font-body text-sm text-foreground">
            ¿Eliminar la solicitud de{" "}
            <span className="font-semibold">{eliminando.empleadoNombre}</span> del{" "}
            {formatFecha(eliminando.startDate)} al {formatFecha(eliminando.endDate)}? Esta
            acción no se puede deshacer.
          </p>
          <div className="mt-5 flex justify-end gap-2">
            <BrandButton variant="outline" onClick={() => setEliminando(null)}>
              Volver
            </BrandButton>
            <BrandButton
              onClick={handleEliminar}
              loading={eliminandoBusy}
              className="bg-destructive hover:bg-destructive/90"
            >
              Eliminar
            </BrandButton>
          </div>
        </BrandModal>
      )}
    </div>
  );
}
