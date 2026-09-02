"use client";

import { FileQuestion } from "lucide-react";
import {
  DERIVADOS_PAGE_SIZE,
  MIS_PST,
  TODOS,
  useIncidentesDerivados,
} from "../hooks/use-incidentes-derivados";
import { incidentesDerivadosColumns } from "./incidentes-derivados-columns";
import { BrandSelect } from "@/shared/components/ui/brand-form";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { StatsTable } from "@/shared/components/ui/stats-table";
import { Spinner } from "@/shared/components/ui/spinner";

export function IncidentesDerivadosDetail() {
  const {
    canVerOperadores,
    monthValue,
    setMonthValue,
    scope,
    setScope,
    operadores,
    incidentes,
    total,
    page,
    setPage,
    loading,
    error,
    isSuperadmin,
  } = useIncidentesDerivados();

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <FileQuestion className="h-6 w-6 shrink-0 text-brand-orange" aria-hidden="true" />
          <div className="flex flex-col gap-1">
            <h1 className="font-heading text-[25px] font-extrabold text-foreground">
              Incidentes sin consultar
            </h1>
            <p className="font-body text-sm text-muted-foreground">
              Incidentes Derivados (estado 200) que el operador todavía no consultó con el
              técnico.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1">
            <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
              Período
            </span>
            <input
              type="month"
              value={monthValue}
              onChange={(e) => setMonthValue(e.target.value)}
              className="rounded-[8px] border border-border bg-card px-3 py-1.5 font-body text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-orange/60"
            />
          </label>
          {canVerOperadores && (
            <BrandSelect
              label="Sin consultar de"
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="min-w-[180px]"
            >
              <option value={MIS_PST}>Mis PST</option>
              {isSuperadmin && <option value={TODOS}>Todos</option>}
              {operadores.map((op) => (
                <option key={op.id} value={op.id}>
                  {op.fullName}
                </option>
              ))}
            </BrandSelect>
          )}
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
            title="Incidentes sin consultar"
            subtitle={
              total > 0
                ? `${total} incidente${total !== 1 ? "s" : ""} — ordenados por días sin consultar (mayor primero)`
                : undefined
            }
            columns={incidentesDerivadosColumns}
            rows={incidentes}
            rowKey={(row) => String(row.id_incidente)}
            emptyLabel="Sin incidentes derivados sin consultar para el período y filtro seleccionados."
          />
          {total > 0 && (
            <PaginationBar
              page={page}
              total={total}
              size={DERIVADOS_PAGE_SIZE}
              onPageChange={setPage}
              noun="incidentes"
            />
          )}
        </>
      )}
    </div>
  );
}
