"use client";

import { ClipboardList, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { pendientesApi } from "../api/pendientes-api";
import type { IncidenteSinCerrar } from "../types/pendientes";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import type { OperadorOption } from "@/features/prestadores/types/prestadores";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandSelect } from "@/shared/components/ui/brand-form";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { StatsTable, type StatsColumn } from "@/shared/components/ui/stats-table";
import { Spinner } from "@/shared/components/ui/spinner";
import { incidentUrl } from "@/shared/utils/incident-link";

const MIS_PST = "__mis_pst__";
const TODOS = "__todos__";
const PAGE_SIZE = 100;

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function formatUpdatedAt(iso: string): string {
  const d = new Date(iso);
  return `${d.toLocaleDateString("es-AR")} ${d.toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

const columns: StatsColumn<IncidenteSinCerrar>[] = [
  {
    key: "id",
    label: "ID",
    className: "w-20",
    render: (row) => (
      <a
        href={incidentUrl(row.id_incidente)}
        target="_blank"
        rel="noopener noreferrer"
        className="font-semibold tabular-nums text-brand-orange hover:underline"
      >
        {row.id_incidente}
      </a>
    ),
  },
  { key: "tecnico", label: "Técnico (PST)", render: (row) => row.tecnico },
  { key: "cliente", label: "Cliente", render: (row) => row.cliente },
  { key: "sucursal", label: "Sucursal", render: (row) => row.sucursal },
  { key: "modelo", label: "Modelo", render: (row) => row.modelo },
  { key: "nro_serie", label: "N° Serie", render: (row) => row.nro_serie },
  {
    key: "fecha_ingreso",
    label: "Ingreso",
    render: (row) => <span className="tabular-nums">{formatFecha(row.fecha_ingreso)}</span>,
  },
  {
    key: "fecha_finalizacion",
    label: "Finalizado",
    render: (row) => <span className="tabular-nums">{formatFecha(row.fecha_finalizacion)}</span>,
  },
  {
    key: "dias",
    label: "Días",
    align: "right",
    className: "w-20",
    render: (row) => (
      <span
        className={
          row.dias_en_estado >= 30
            ? "font-semibold text-[#dc2626] dark:text-[#f87171]"
            : "tabular-nums"
        }
      >
        {row.dias_en_estado}
      </span>
    ),
  },
];

export function PendientesACerrarDetail() {
  const { user, can } = useSession();
  const canUpdate = user.isSuperadmin || can("sla", "update");
  const canVerOperadores = user.isSuperadmin || can("prestadores", "view");

  const [scope, setScope] = useState<string>(MIS_PST);
  const [operadores, setOperadores] = useState<OperadorOption[]>([]);
  const [incidentes, setIncidentes] = useState<IncidenteSinCerrar[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [prevScope, setPrevScope] = useState(scope);
  if (scope !== prevScope) {
    setPrevScope(scope);
    setLoading(true);
    setError(null);
    setIncidentes([]);
    setPage(1);
  }

  useEffect(() => {
    if (!canVerOperadores) return;
    prestadoresApi.listOperadores().then(setOperadores).catch(() => setOperadores([]));
  }, [canVerOperadores]);

  useEffect(() => {
    let active = true;
    const operadorId = scope === TODOS ? undefined : scope === MIS_PST ? undefined : scope;
    pendientesApi
      .listPendientes({ operadorId, page, size: PAGE_SIZE })
      .then((res) => {
        if (!active) return;
        setIncidentes(res.items);
        setTotal(res.total);
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar pendientes a cerrar:", err);
        setError(
          err instanceof Error ? err.message : "No se pudieron cargar los pendientes a cerrar.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [scope, page]);

  const handleRefresh = () => {
    setRefreshing(true);
    setError(null);
    const operadorId = scope === TODOS ? undefined : scope === MIS_PST ? undefined : scope;
    pendientesApi
      .refresh()
      .then(() => pendientesApi.listPendientes({ operadorId, page, size: PAGE_SIZE }))
      .then((res) => {
        setIncidentes(res.items);
        setTotal(res.total);
        setUpdatedAt(new Date().toISOString());
      })
      .catch((err: unknown) => {
        console.error("Error al actualizar pendientes:", err);
        setError(err instanceof Error ? err.message : "No se pudo actualizar.");
      })
      .finally(() => setRefreshing(false));
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <ClipboardList className="h-6 w-6 shrink-0 text-brand-orange" aria-hidden="true" />
          <div className="flex flex-col gap-1">
            <h1 className="font-heading text-[25px] font-extrabold text-foreground">
              Pendientes a Cerrar
            </h1>
            <p className="font-body text-sm text-muted-foreground">
              Incidentes Finalizados (estado 500) que aún no fueron cerrados.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          {canVerOperadores && (
            <BrandSelect
              label="Pendientes de"
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="min-w-[180px]"
            >
              <option value={MIS_PST}>Mis PST</option>
              {user.isSuperadmin && <option value={TODOS}>Todos</option>}
              {operadores.map((op) => (
                <option key={op.id} value={op.id}>
                  {op.fullName}
                </option>
              ))}
            </BrandSelect>
          )}
          <div className="flex flex-col items-end gap-1">
            <BrandButton
              onClick={handleRefresh}
              loading={refreshing}
              disabled={!canUpdate || loading}
              title={canUpdate ? undefined : "Sin permiso para actualizar"}
            >
              {!refreshing && <RefreshCw className="h-4 w-4" />}
              Actualizar
            </BrandButton>
            {updatedAt && (
              <span className="font-body text-[11px] text-muted-foreground">
                Actualizado {formatUpdatedAt(updatedAt)}
              </span>
            )}
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {!loading && !error && (
        <>
          <StatsTable
            title="Incidentes pendientes a cerrar"
            subtitle={
              total > 0
                ? `${total} incidente${total !== 1 ? "s" : ""} — ordenados por días sin cerrar (mayor primero)`
                : undefined
            }
            columns={columns}
            rows={incidentes}
            rowKey={(row) => String(row.id_incidente)}
            emptyLabel="Sin incidentes pendientes a cerrar para el filtro seleccionado."
          />
          {total > 0 && (
            <PaginationBar
              page={page}
              total={total}
              size={PAGE_SIZE}
              onPageChange={setPage}
              noun="incidentes"
            />
          )}
        </>
      )}
    </div>
  );
}
