"use client";

import { useState, type FormEvent } from "react";
import type { CrearSolicitudTvAdminBody } from "../types/tareas-varias";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { useModalSubmit } from "@/shared/hooks/use-modal-submit";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

interface SolicitudTvAdminModalProps {
  onClose: () => void;
  onSubmit: (idTecnico: number, body: CrearSolicitudTvAdminBody) => Promise<unknown>;
}

/** Carga de TV a nombre de un técnico desde el panel de supervisor — mismo
 * formulario que `MisTareasVarias`, pero la solicitud nace ya APROBADA (no
 * pasa por la cola de pendientes). Sin catálogo propio de técnicos en este
 * módulo (ver Bono Técnicos para el ID), el ID y el nombre se escriben a
 * mano — mismo criterio que "Cargar Días" ahí. */
export function SolicitudTvAdminModal({ onClose, onSubmit }: SolicitudTvAdminModalProps) {
  const [idTecnico, setIdTecnico] = useState("");
  const [tecnico, setTecnico] = useState("");
  const [fecha, setFecha] = useState(todayIso());
  const [razonSocial, setRazonSocial] = useState("");
  const [sucursal, setSucursal] = useState("");
  const [tareaRealizada, setTareaRealizada] = useState("");
  const { saving: submitting, error, submit } = useModalSubmit();

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    void submit(async () => {
      await onSubmit(Number(idTecnico), {
        tecnico,
        fecha,
        razon_social: razonSocial,
        sucursal,
        tarea_realizada: tareaRealizada,
      });
      onClose();
    }, "No se pudo cargar la TV.");
  };

  return (
    <BrandModal isOpen title="Cargar TV a nombre de un técnico" onClose={onClose} widthPx={480} error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <p className="font-body text-xs text-muted-foreground">
          Se registra ya aprobada e impacta el Puntaje del bono del período. El ID de técnico es
          el mismo que se ve en Bono Técnicos.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <BrandInput
            label="ID Técnico"
            type="number"
            value={idTecnico}
            required
            min={1}
            onChange={(e) => setIdTecnico(e.target.value)}
          />
          <BrandInput
            label="Técnico"
            placeholder="Ej. CD - Agustin HACZEK"
            value={tecnico}
            required
            maxLength={200}
            onChange={(e) => setTecnico(e.target.value)}
          />
        </div>
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
