"use client";

import { useMemo, useState } from "react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { asistenciasApi } from "../api/asistencias-api";
import { hoyIso } from "../lib/fechas";
import { TIPO_AUSENCIA, TIPOS_SELECCIONABLES } from "../lib/tipos-ausencia";
import type { Ausencia, EmpleadoListItem, EstadoSolicitud, TipoAusencia } from "../types/vacaciones";

interface Props {
  ausencia: Ausencia | null;
  empleados: EmpleadoListItem[];
  esAdmin: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export function AusenciaModal({ ausencia, empleados, esAdmin, onClose, onSaved }: Props) {
  const [empleadoIds, setEmpleadoIds] = useState<string[]>(
    ausencia ? [ausencia.empleadoId] : [],
  );
  const [busqueda, setBusqueda] = useState("");
  const [startDate, setStartDate] = useState(ausencia?.startDate ?? hoyIso());
  const [endDate, setEndDate] = useState(ausencia?.endDate ?? hoyIso());
  const [tipo, setTipo] = useState<TipoAusencia>(ausencia?.tipo ?? "DESCUENTO_DIA");
  const [halfDay, setHalfDay] = useState(ausencia?.halfDay ?? false);
  const [reason, setReason] = useState(ausencia?.reason ?? "");
  const [status, setStatus] = useState<EstadoSolicitud>(ausencia?.status ?? "APPROVED");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!q) return empleados;
    return empleados.filter((e) =>
      `${e.firstName} ${e.lastName}`.toLowerCase().includes(q),
    );
  }, [empleados, busqueda]);

  const toggle = (id: string) => {
    setEmpleadoIds((ids) =>
      ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id],
    );
  };

  const guardar = () => {
    if (!ausencia && empleadoIds.length === 0) {
      setError("Seleccioná al menos un empleado.");
      return;
    }
    setBusy(true);
    setError(null);
    // Paridad legacy: el medio día solo aplica al tipo Descuento día.
    const base = {
      startDate,
      endDate,
      tipo,
      reason: reason || null,
      halfDay: tipo === "DESCUENTO_DIA" ? halfDay : false,
    };
    const req = ausencia
      ? asistenciasApi.update(ausencia.id, {
          ...base,
          ...(esAdmin ? { status } : {}),
        })
      : asistenciasApi.create({ ...base, empleadoIds });
    req
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo guardar la baja.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={ausencia ? "Editar baja" : "Registrar baja"}
      widthPx={480}
      error={error}
    >
      <div className="flex flex-col gap-4">
        {!ausencia && (
          <div>
            <p className="mb-1.5 font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Empleado/s
            </p>
            <input
              type="text"
              placeholder="Buscar empleado…"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="mb-1.5 w-full rounded-[8px] border border-border bg-card px-3.5 py-2 font-body text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-brand-orange/40"
            />
            <div className="flex max-h-40 flex-col gap-0.5 overflow-y-auto rounded-[8px] border border-border p-1.5">
              {filtrados.map((e) => (
                <label
                  key={e.id}
                  className="flex cursor-pointer items-center gap-2 rounded-[6px] px-2 py-1 font-body text-sm text-foreground hover:bg-muted"
                >
                  <input
                    type="checkbox"
                    checked={empleadoIds.includes(e.id)}
                    onChange={() => toggle(e.id)}
                    className="h-4 w-4 accent-brand-orange"
                  />
                  {e.firstName} {e.lastName}
                  <span className="text-xs text-muted-foreground">· {e.sectorNombre}</span>
                </label>
              ))}
              {filtrados.length === 0 && (
                <p className="px-2 py-1 font-body text-xs text-muted-foreground">
                  Sin resultados.
                </p>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <BrandInput
            label="Fecha inicio"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <BrandInput
            label="Fecha fin"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        <BrandSelect
          label="Tipo de baja"
          value={tipo}
          onChange={(e) => setTipo(e.target.value as TipoAusencia)}
        >
          {TIPOS_SELECCIONABLES.map((t) => (
            <option key={t} value={t}>
              {TIPO_AUSENCIA[t].label}
            </option>
          ))}
        </BrandSelect>

        <label
          className={`flex items-center gap-2.5 font-body text-sm ${
            tipo === "DESCUENTO_DIA" ? "text-foreground" : "text-muted-foreground"
          }`}
        >
          <input
            type="checkbox"
            checked={tipo === "DESCUENTO_DIA" && halfDay}
            disabled={tipo !== "DESCUENTO_DIA"}
            onChange={(e) => setHalfDay(e.target.checked)}
            className="h-4 w-4 accent-brand-orange"
          />
          Medio día
          <span className="text-xs text-muted-foreground">
            (solo para Descuento día — computa 0.5)
          </span>
        </label>

        {ausencia && esAdmin && (
          <BrandSelect
            label="Estado"
            value={status}
            onChange={(e) => setStatus(e.target.value as EstadoSolicitud)}
          >
            <option value="APPROVED">Aprobada</option>
            <option value="PENDING">Pendiente</option>
            <option value="REJECTED">Rechazada</option>
          </BrandSelect>
        )}

        <div>
          <label className="mb-1.5 block font-body text-[13px] font-semibold text-foreground">
            Observaciones <span className="font-normal text-muted-foreground">(opcional)</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Agregá observaciones sobre la baja…"
            rows={3}
            maxLength={500}
            className="w-full rounded-[10px] border border-border bg-background px-3.5 py-2.5 font-body text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-brand-orange"
          />
        </div>

        <div className="mt-1 flex justify-end gap-2">
          <BrandButton variant="outline" onClick={onClose} disabled={busy}>
            Cancelar
          </BrandButton>
          <BrandButton onClick={guardar} loading={busy}>
            {ausencia ? "Guardar cambios" : "Registrar"}
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
