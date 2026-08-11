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
  operadorId: string;
  setOperadorId: (value: string) => void;
  soloFacturacion: boolean;
  setSoloFacturacion: (value: boolean) => void;
  onApplyFilters: () => void;
  loading: boolean;
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
  operadorId,
  setOperadorId,
  soloFacturacion,
  setSoloFacturacion,
  onApplyFilters,
  loading,
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
          <div className="w-32">
            <BrandInput
              id="operador-id"
              label="Operador ID"
              placeholder="Ej: 318"
              value={operadorId}
              onChange={(e) => setOperadorId(e.target.value)}
              className="text-xs"
            />
          </div>
          <div className="flex items-center gap-2 pt-5">
            <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-foreground">
              <input
                type="checkbox"
                checked={soloFacturacion}
                onChange={(e) => setSoloFacturacion(e.target.checked)}
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
              />
              Solo Facturación
            </label>
          </div>
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
