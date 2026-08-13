"use client";

import { useState } from "react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { solicitudesApi } from "../api/solicitudes-api";
import { hoyIso } from "../lib/fechas";
import type { EmpleadoListItem, Solicitud } from "../types/vacaciones";

interface Props {
  solicitud: Solicitud | null;
  /** Solo con `manage`: elegir el empleado. Vacío = solicitud propia. */
  empleados: EmpleadoListItem[];
  onClose: () => void;
  onSaved: () => void;
}

export function SolicitudModal({ solicitud, empleados, onClose, onSaved }: Props) {
  const anioActual = new Date().getFullYear();
  const [empleadoId, setEmpleadoId] = useState(solicitud?.empleadoId ?? "");
  const [startDate, setStartDate] = useState(solicitud?.startDate ?? hoyIso());
  const [endDate, setEndDate] = useState(solicitud?.endDate ?? hoyIso());
  const [ciclo, setCiclo] = useState<string>(
    solicitud?.chargedToYear ? String(solicitud.chargedToYear) : "",
  );
  const [reason, setReason] = useState(solicitud?.reason ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const guardar = () => {
    setBusy(true);
    setError(null);
    const payload = {
      startDate,
      endDate,
      chargedToYear: ciclo ? Number(ciclo) : null,
      reason: reason || null,
    };
    const req = solicitud
      ? solicitudesApi.update(solicitud.id, payload)
      : solicitudesApi.create({
          ...payload,
          ...(empleadoId ? { empleadoId } : {}),
        });
    req
      .then(onSaved)
      .catch((err: unknown) => {
        // Los 400/409 del backend traen el mensaje de negocio exacto del
        // legacy (saldo insuficiente, solapamiento, exclusión, límite…).
        setError(
          err instanceof ApiError ? err.message : "No se pudo guardar la solicitud.",
        );
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={solicitud ? "Editar solicitud" : "Nueva solicitud de vacaciones"}
      widthPx={490}
      error={error}
    >
      <div className="flex flex-col gap-4">
        {empleados.length > 0 && !solicitud && (
          <BrandSelect
            label="Empleado"
            value={empleadoId}
            onChange={(e) => setEmpleadoId(e.target.value)}
          >
            <option value="">Seleccioná un empleado…</option>
            {empleados.map((e) => (
              <option key={e.id} value={e.id}>
                {e.firstName} {e.lastName} · {e.sectorNombre}
              </option>
            ))}
          </BrandSelect>
        )}
        <div className="grid grid-cols-2 gap-3">
          <BrandInput
            label="Fecha de inicio"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <BrandInput
            label="Fecha de fin"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <BrandSelect
          label="Ciclo de cargo"
          hint="A qué año se imputan los días"
          value={ciclo}
          onChange={(e) => setCiclo(e.target.value)}
        >
          <option value="">Automático (año de inicio)</option>
          <option value={String(anioActual)}>Ciclo {anioActual}</option>
          <option value={String(anioActual + 1)}>Ciclo {anioActual + 1} (adelantada)</option>
        </BrandSelect>
        <div>
          <label className="mb-1.5 block font-body text-[13px] font-semibold text-foreground">
            Motivo (opcional)
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Ej: Vacaciones de verano"
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
            {solicitud ? "Guardar cambios" : "Crear solicitud"}
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
