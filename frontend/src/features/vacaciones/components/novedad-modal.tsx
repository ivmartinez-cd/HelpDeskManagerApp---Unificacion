"use client";

import { useState } from "react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { asistenciasApi } from "../api/asistencias-api";
import { hoyIso } from "../lib/fechas";
import { TIPO_AUSENCIA } from "../lib/tipos-ausencia";
import { TIPOS_SOLICITABLES, type TipoAusencia } from "../types/vacaciones";

/** Alta de una "novedad" propia (home office o cambio de horario): se crea
 * como ausencia PENDING a nombre del empleado vinculado al usuario y la
 * decide la TL desde Aprobaciones (2026-08-21). Para cambio de horario el
 * rango horario es obligatorio (ej. 08:00–17:00 en vez del habitual). */
export function NovedadModal({
  tipoInicial = "HOME_OFFICE",
  onClose,
  onSaved,
}: {
  tipoInicial?: TipoAusencia;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [tipo, setTipo] = useState<TipoAusencia>(tipoInicial);
  const [startDate, setStartDate] = useState(hoyIso());
  const [endDate, setEndDate] = useState(hoyIso());
  const [horaDesde, setHoraDesde] = useState("08:00");
  const [horaHasta, setHoraHasta] = useState("17:00");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esCambioHorario = tipo === "CAMBIO_HORARIO";

  const guardar = () => {
    if (endDate < startDate) {
      setError("La fecha de fin debe ser posterior o igual a la de inicio.");
      return;
    }
    if (esCambioHorario && horaHasta <= horaDesde) {
      setError("La hora hasta debe ser posterior a la hora desde.");
      return;
    }
    setBusy(true);
    setError(null);
    asistenciasApi
      .create({
        startDate,
        endDate,
        tipo,
        reason: reason || null,
        halfDay: false,
        horaDesde: esCambioHorario ? horaDesde : null,
        horaHasta: esCambioHorario ? horaHasta : null,
      })
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo enviar la solicitud.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal isOpen onClose={onClose} title="Nueva solicitud" widthPx={480} error={error}>
      <div className="flex flex-col gap-4">
        <BrandSelect
          label="Tipo"
          value={tipo}
          onChange={(e) => setTipo(e.target.value as TipoAusencia)}
        >
          {TIPOS_SOLICITABLES.map((t) => (
            <option key={t} value={t}>
              {TIPO_AUSENCIA[t].label}
            </option>
          ))}
        </BrandSelect>

        <div className="grid grid-cols-2 gap-3">
          <BrandInput
            label="Desde"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <BrandInput
            label="Hasta"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        {esCambioHorario && (
          <div className="grid grid-cols-2 gap-3">
            <BrandInput
              label="Horario desde"
              type="time"
              value={horaDesde}
              onChange={(e) => setHoraDesde(e.target.value)}
            />
            <BrandInput
              label="Horario hasta"
              type="time"
              value={horaHasta}
              onChange={(e) => setHoraHasta(e.target.value)}
            />
          </div>
        )}

        <BrandInput
          label="Motivo (opcional)"
          value={reason}
          maxLength={500}
          placeholder={esCambioHorario ? "Ej.: turno médico a la tarde" : "Ej.: trabajo remoto"}
          onChange={(e) => setReason(e.target.value)}
        />

        <p className="rounded-[8px] bg-muted/30 px-3.5 py-2.5 font-body text-xs text-muted-foreground">
          La solicitud queda pendiente hasta que la apruebe tu TL. Al aprobarse aparece en el
          Registro de asistencias y, si tenés franjas de turno en esas fechas, Turnos lo refleja.
        </p>

        <div className="flex justify-end gap-2 pt-1">
          <BrandButton variant="outline" onClick={onClose} disabled={busy}>
            Cancelar
          </BrandButton>
          <BrandButton onClick={guardar} loading={busy}>
            Enviar solicitud
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
