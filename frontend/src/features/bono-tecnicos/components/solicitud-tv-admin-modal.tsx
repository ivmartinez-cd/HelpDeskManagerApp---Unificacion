"use client";

import { useState, type FormEvent } from "react";
import type { CrearSolicitudTvAdminBody } from "../types/bono-tecnicos";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

interface SolicitudTvAdminModalProps {
  tecnico: string;
  onClose: () => void;
  onSubmit: (body: CrearSolicitudTvAdminBody) => Promise<unknown>;
}

/** Carga de TV a nombre de un técnico desde el panel de supervisor — mismo
 * formulario que `MisSolicitudesTv`, pero la solicitud nace ya APROBADA
 * (no pasa por la cola de pendientes de `SolicitudesTvPendientes`). El
 * `id_tecnico` no viaja como prop porque el padre ya lo cierra en
 * `onSubmit` (misma fila que abrió el modal). */
export function SolicitudTvAdminModal({ tecnico, onClose, onSubmit }: SolicitudTvAdminModalProps) {
  const [fecha, setFecha] = useState(todayIso());
  const [razonSocial, setRazonSocial] = useState("");
  const [sucursal, setSucursal] = useState("");
  const [tareaRealizada, setTareaRealizada] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    onSubmit({
      tecnico,
      fecha,
      razon_social: razonSocial,
      sucursal,
      tarea_realizada: tareaRealizada,
    })
      .then(() => onClose())
      .catch(() => setError("No se pudo cargar la TV."))
      .finally(() => setSubmitting(false));
  };

  return (
    <BrandModal isOpen title={`Cargar TV — ${tecnico}`} onClose={onClose} widthPx={480} error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <p className="font-body text-xs text-muted-foreground">
          Se registra ya aprobada e impacta el Puntaje del período.
        </p>
        <BrandInput
          label="Fecha"
          type="date"
          value={fecha}
          max={todayIso()}
          required
          onChange={(e) => setFecha(e.target.value)}
        />
        <BrandInput
          label="Razón Social"
          placeholder="Ej. Exolgan"
          value={razonSocial}
          required
          maxLength={200}
          onChange={(e) => setRazonSocial(e.target.value)}
        />
        <BrandInput
          label="Sucursal"
          placeholder="Ej. Dock Sur"
          value={sucursal}
          required
          maxLength={200}
          onChange={(e) => setSucursal(e.target.value)}
        />
        <div className="flex flex-col gap-1.5">
          <label className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            Tarea Realizada
          </label>
          <textarea
            value={tareaRealizada}
            required
            maxLength={2000}
            rows={3}
            placeholder="Describí la tarea realizada"
            onChange={(e) => setTareaRealizada(e.target.value)}
            className="rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
          />
        </div>
        <div>
          <BrandButton type="submit" loading={submitting}>
            Cargar TV
          </BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
