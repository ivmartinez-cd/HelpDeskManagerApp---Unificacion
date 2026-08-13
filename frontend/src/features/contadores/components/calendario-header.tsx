"use client";

import {
  ChevronLeft,
  ChevronRight,
  Download,
  Filter,
  RefreshCw,
  Search,
} from "lucide-react";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import type { CalendarioVerPor, Operador } from "../types/calendario";

interface Props {
  currentMonthTitle: string;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  onToday: () => void;
  searchQuery: string;
  setSearchQuery: (value: string) => void;
  showFilterPanel: boolean;
  onToggleFilterPanel: () => void;
  onExportCsv: () => void;
  exportDisabled: boolean;
  startDate: string;
  setStartDate: (value: string) => void;
  endDate: string;
  setEndDate: (value: string) => void;
  showOperadorFilter: boolean;
  operadorId: string | null;
  setOperadorId: (value: string | null) => void;
  operadores: Operador[];
  onApplyFilters: () => void;
  loading: boolean;
  syncing: boolean;
  onSync: () => void;
  lastSyncedAt: string | null;
  verPor: CalendarioVerPor;
  setVerPor: (value: CalendarioVerPor) => void;
}

function formatLastSynced(iso: string | null): string {
  if (!iso) return "Nunca sincronizado";
  const date = new Date(iso);
  return `Última sincronización: ${date.toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

export function CalendarioHeader({
  currentMonthTitle,
  onPrevMonth,
  onNextMonth,
  onToday,
  searchQuery,
  setSearchQuery,
  showFilterPanel,
  onToggleFilterPanel,
  onExportCsv,
  exportDisabled,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  showOperadorFilter,
  operadorId,
  setOperadorId,
  operadores,
  onApplyFilters,
  loading,
  syncing,
  onSync,
  lastSyncedAt,
  verPor,
  setVerPor,
}: Props) {
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-4 py-2">
        <div className="flex items-center gap-3">
          <h2 className="font-heading text-2xl font-extrabold tracking-tight text-foreground">
            {currentMonthTitle}
          </h2>

          {/* Navigation Controls: < > Oval Pill + Hoy Button */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-0.5 rounded-full border border-border bg-card px-1.5 py-0.5 shadow-2xs">
              <button
                onClick={onPrevMonth}
                className="rounded-full p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                title="Mes Anterior"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={onNextMonth}
                className="rounded-full p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                title="Mes Siguiente"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>

            <button
              onClick={onToday}
              className="rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground shadow-2xs hover:bg-muted transition-colors"
            >
              Hoy
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Switch efectivo/real: solo cambia el render de los eventos
              cubiertos, nunca el set de eventos (ver CoberturaEvento). */}
          <div className="flex items-center gap-1.5">
            <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Ver por
            </span>
            <SegmentedControl
              size="sm"
              label="Ver por"
              options={[
                { value: "efectivo", label: "Operador efectivo" },
                { value: "real", label: "Operador real" },
              ]}
              value={verPor}
              onChange={(value) => setVerPor(value as CalendarioVerPor)}
            />
          </div>

          {/* Search box */}
          <div className="relative w-48 sm:w-64">
            <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Buscar cliente..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-border bg-card pl-8 pr-3 py-1 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <button
            onClick={onToggleFilterPanel}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted transition-colors"
          >
            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
            Filtros
          </button>

          {/* Sync button */}
          <button
            onClick={onSync}
            disabled={syncing}
            title={formatLastSynced(lastSyncedAt)}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3.5 py-1.5 text-xs font-semibold text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 text-muted-foreground ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "Sincronizando..." : "Sincronizar"}
          </button>

          {/* Export button */}
          <button
            onClick={onExportCsv}
            disabled={exportDisabled}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3.5 py-1.5 text-xs font-semibold text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5 text-muted-foreground" />
            Exportar
          </button>
        </div>
      </div>

      <p className="-mt-2 text-right text-[11px] text-muted-foreground">
        {formatLastSynced(lastSyncedAt)}
      </p>

      {/* Expandable Filter Panel */}
      {showFilterPanel && (
        <div className="flex flex-wrap items-center gap-4 rounded-xl border border-border bg-card p-4 text-xs">
          <BrandInput
            id="start-date"
            label="Desde"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-36 text-xs"
          />
          <BrandInput
            id="end-date"
            label="Hasta"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-36 text-xs"
          />
          {showOperadorFilter && (
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="operador-filter"
                className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground"
              >
                Operador de facturación
              </label>
              <select
                id="operador-filter"
                value={operadorId ?? ""}
                onChange={(e) => setOperadorId(e.target.value || null)}
                className="w-48 rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
              >
                <option value="">Todos los operadores</option>
                {operadores.map((op) => (
                  <option key={op.id} value={op.id}>
                    {op.nombre}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="pt-5 ml-auto flex items-center gap-2">
            <BrandButton variant="outline" size="sm" onClick={onApplyFilters} disabled={loading}>
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Aplicar Filtros
            </BrandButton>
          </div>
        </div>
      )}
    </>
  );
}
