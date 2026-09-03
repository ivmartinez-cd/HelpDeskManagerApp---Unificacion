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
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import { gestionApi } from "../api/gestion-api";
import { solicitudesApi } from "../api/solicitudes-api";
import type { EmpleadoListItem, EstadoSolicitud, Solicitud } from "../types/vacaciones";
import { SolicitudEliminarModal } from "./solicitud-eliminar-modal";
import { SolicitudModal } from "./solicitud-modal";
import {
  SOLICITUD_SORT_KEYS,
  SolicitudesTabla,
  solicitudSortValue,
  type SolicitudSortKey,
} from "./solicitudes-tabla";

const PAGE_SIZE = 25;

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

  // Solo vacaciones: home office y cambios de horario viven en Asistencias
  // (pestaña "Home office y horario", `MisNovedades`) desde 2026-09-03.
  const [solicitudes, setSolicitudes] = useState<Solicitud[] | null>(null);
  const [empleados, setEmpleados] = useState<EmpleadoListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<"todas" | EstadoSolicitud>("todas");
  const [busqueda, setBusqueda] = useState("");
  const [page, setPage] = useState(1);

  const { sort, toggleSort } = useTableSort<SolicitudSortKey>({
    initial: { key: "inicio", direction: "desc" },
    keys: SOLICITUD_SORT_KEYS,
    descFirstKeys: ["inicio"],
  });
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
    const base = solicitudes.filter((s) => {
      if (filtro !== "todas" && s.status !== filtro) return false;
      if (!q) return true;
      return [s.empleadoNombre, s.reason ?? "", s.sectorNombre].some((v) =>
        v.toLowerCase().includes(q),
      );
    });
    return [...base].sort((a, b) =>
      compareSortValues(solicitudSortValue(a, sort.key), solicitudSortValue(b, sort.key), sort.direction),
    );
  }, [solicitudes, filtro, busqueda, sort]);

  useEffect(() => {
    setPage(1);
  }, [filtro, busqueda, sort]);

  const totalPaginas = Math.max(1, Math.ceil(visibles.length / PAGE_SIZE));
  const paginaActual = Math.min(page, totalPaginas);
  const visiblesPagina = visibles.slice((paginaActual - 1) * PAGE_SIZE, paginaActual * PAGE_SIZE);

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
            Creá y gestioná tus solicitudes de vacaciones
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
            <>
              <SolicitudesTabla
                visibles={visiblesPagina}
                sort={sort}
                onToggleSort={toggleSort}
                onEditar={setEditando}
                onEliminar={setEliminando}
              />
              <PaginationBar
                page={paginaActual}
                total={visibles.length}
                size={PAGE_SIZE}
                onPageChange={setPage}
                noun="solicitudes"
              />
            </>
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
        <SolicitudEliminarModal
          eliminando={eliminando}
          busy={eliminandoBusy}
          onClose={() => setEliminando(null)}
          onConfirm={handleEliminar}
        />
      )}
    </div>
  );
}
