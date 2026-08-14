"use client";

import { useState } from "react";
import { toast } from "sonner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Liquidacion } from "../types/liquidaciones";
import { formatARS } from "../lib/format";

const inputCls =
  "rounded-[8px] border border-border bg-background px-3 py-1.5 font-body text-sm text-foreground outline-none focus:border-brand-orange/50";

export function ExtraItemSeccion({
  liquidacion,
  onUpdated,
}: {
  liquidacion: Liquidacion;
  onUpdated: (updated: Liquidacion) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [concepto, setConcepto] = useState(liquidacion.conceptoExtra ?? "");
  const [monto, setMonto] = useState(liquidacion.montoExtra?.toString() ?? "");
  const [saving, setSaving] = useState(false);

  const totalAjustado = liquidacion.totalImporte + (liquidacion.montoExtra ?? 0);

  const handleSave = async () => {
    setSaving(true);
    try {
      const montoNum = monto.trim() !== "" ? parseFloat(monto) : null;
      const updated = await liquidacionesApi.updateExtra(liquidacion.id, {
        conceptoExtra: concepto.trim() || null,
        montoExtra: montoNum,
      });
      onUpdated(updated);
      setEditing(false);
    } catch {
      toast.error("Error al guardar el ítem extra");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setConcepto(liquidacion.conceptoExtra ?? "");
    setMonto(liquidacion.montoExtra?.toString() ?? "");
    setEditing(false);
  };

  return (
    <div className="rounded-[12px] border border-border bg-card p-5">
      <div className="flex items-center justify-between gap-4">
        <span className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
          Ítem extra
        </span>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="flex items-center gap-1.5 rounded-[8px] border border-brand-orange/40 px-3 py-1.5 font-body text-xs font-semibold text-brand-orange transition-colors hover:bg-brand-orange/10"
          >
            + {liquidacion.montoExtra != null ? "Editar ítem" : "Agregar ítem"}
          </button>
        )}
      </div>

      {editing ? (
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="font-body text-xs text-muted-foreground">Concepto</label>
            <input
              value={concepto}
              onChange={(e) => setConcepto(e.target.value)}
              placeholder="Ej. Seguro de viaje"
              className={`${inputCls} w-56`}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="font-body text-xs text-muted-foreground">Monto ($)</label>
            <input
              type="number"
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              placeholder="0.00"
              className={`${inputCls} w-32`}
            />
          </div>
          <button
            onClick={() => void handleSave()}
            disabled={saving}
            className="rounded-[8px] bg-brand-orange px-4 py-1.5 font-body text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "Guardando..." : "Guardar"}
          </button>
          <button
            onClick={handleCancel}
            disabled={saving}
            className="font-body text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
          >
            Cancelar
          </button>
        </div>
      ) : liquidacion.montoExtra != null ? (
        <div className="mt-2 flex flex-wrap items-baseline gap-6">
          <div className="flex flex-col">
            <span className="font-body text-sm text-foreground">
              {liquidacion.conceptoExtra ?? "—"}
            </span>
            <span className="font-heading text-xl font-extrabold text-foreground">
              {formatARS(liquidacion.montoExtra)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
              Total ajustado
            </span>
            <span className="font-heading text-xl font-extrabold text-foreground">
              {formatARS(totalAjustado)}
            </span>
          </div>
        </div>
      ) : (
        <p className="mt-2 font-body text-sm text-muted-foreground">
          No hay ítems extra cargados en esta liquidación.
        </p>
      )}
    </div>
  );
}
