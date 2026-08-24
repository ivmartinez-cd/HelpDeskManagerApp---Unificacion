import { EditableNumberCell } from "./editable-number-cell";
import type { PuntajeTecnico } from "../types/bono-tecnicos";
import type { StatsColumn } from "@/shared/components/ui/stats-table";

interface BuildColumnsOptions {
  canUpdate: boolean;
  savingId: number | null;
  onGuardarDias: (row: PuntajeTecnico, dias: number) => void;
  onVerDetalle: (row: PuntajeTecnico) => void;
}

export function buildBonoTecnicosColumns({
  canUpdate,
  savingId,
  onGuardarDias,
  onVerDetalle,
}: BuildColumnsOptions): StatsColumn<PuntajeTecnico>[] {
  return [
    {
      key: "tecnico",
      label: "Técnico",
      render: (row) => (
        <button
          type="button"
          onClick={() => onVerDetalle(row)}
          className="font-semibold text-brand-orange hover:underline"
        >
          {row.tecnico}
        </button>
      ),
    },
    {
      key: "correctivo",
      label: "Correctivo",
      align: "right",
      render: (row) => row.correctivo,
    },
    {
      key: "preventivo",
      label: "Preventivo",
      align: "right",
      render: (row) => row.preventivo,
    },
    { key: "inst_des", label: "Inst-Des", align: "right", render: (row) => row.inst_des },
    {
      key: "pre_correctivo",
      label: "Pre-Correctivo",
      align: "right",
      render: (row) => row.pre_correctivo,
    },
    {
      key: "entrega_insumos",
      label: "Entrega Insumos",
      align: "right",
      render: (row) => row.entrega_insumos,
    },
    {
      key: "dias",
      label: "Días",
      align: "right",
      className: "w-36",
      render: (row) => (
        <div className="flex flex-col items-end gap-0.5">
          <EditableNumberCell
            value={row.dias}
            disabled={!canUpdate}
            saving={savingId === row.id_tecnico}
            onCommit={(v) => onGuardarDias(row, v)}
          />
          {row.dias_sugeridos !== null && row.dias_sugeridos !== row.dias && (
            <button
              type="button"
              disabled={!canUpdate}
              onClick={() => onGuardarDias(row, row.dias_sugeridos as number)}
              className="font-body text-[11px] text-muted-foreground hover:text-brand-orange disabled:cursor-not-allowed"
              title="Sugerido a partir de las asistencias en Gestión de Personal"
            >
              sugerido: {row.dias_sugeridos}
            </button>
          )}
        </div>
      ),
    },
    {
      key: "tareas_varias",
      label: "TV",
      align: "right",
      className: "w-28",
      // Ya no es carga manual: es la cuenta de solicitudes de TV aprobadas
      // del período (ver SolicitudTv) — solo lectura acá.
      render: (row) => row.tareas_varias,
    },
    {
      key: "puntaje",
      label: "Puntaje",
      align: "right",
      className: "w-24",
      render: (row) => (
        <span className="font-semibold tabular-nums text-brand-orange">
          {row.puntaje === null
            ? "—"
            : row.puntaje.toLocaleString("es-AR", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
        </span>
      ),
    },
  ];
}
