"use client";

import { ArrowLeft, Download, FileText, Loader2, RefreshCw, Save } from "lucide-react";
import type { DateFilter } from "../utils/date-filter";
import { DateRangePicker } from "./date-range-picker";

interface Props {
  deviceId: string;
  dateFilter: DateFilter;
  onDateFilterChange: (f: DateFilter) => void;
  onBack: () => void;
  onEws: () => void;
  onRefresh: () => void;
  refreshing: boolean;
  onCpmd: () => void;
  onExportPdf: () => void;
  exportingPdf: boolean;
  onSave: () => void;
  saving: boolean;
  canSave: boolean;
}

const BTN =
  "flex items-center gap-1.5 rounded-[8px] border border-border bg-card px-3 py-2 font-body text-[12px] text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50";

export function PanelToolbar({
  deviceId, dateFilter, onDateFilterChange, onBack,
  onEws, onRefresh, refreshing, onCpmd, onExportPdf, exportingPdf, onSave, saving, canSave,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={onBack}
        title="Volver"
        className="flex h-9 w-9 items-center justify-center rounded-[8px] border border-border bg-card text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
      </button>
      <DateRangePicker value={dateFilter} onChange={onDateFilterChange} />
      {deviceId !== "manual" && (
        <>
          <button type="button" onClick={onEws} className={BTN}>
            EWS Remoto
          </button>
          <button type="button" onClick={onRefresh} disabled={refreshing} className={BTN}>
            {refreshing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            Actualizar caché HP
          </button>
        </>
      )}
      <button type="button" onClick={onCpmd} className={BTN}>
        <FileText className="h-3.5 w-3.5" />
        Manual CPMD
      </button>
      <button type="button" onClick={onExportPdf} disabled={exportingPdf} className={BTN}>
        {exportingPdf ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
        Exportar PDF
      </button>
      {canSave && (
        <button type="button" onClick={onSave} disabled={saving} className={BTN}>
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          Guardar
        </button>
      )}
    </div>
  );
}
