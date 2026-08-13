"use client";

import { useState } from "react";
import { Building2 } from "lucide-react";
import { ApiError } from "@/services/http-client";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSelect,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { gestionApi } from "../api/gestion-api";
import { COLORES_IDENTIDAD } from "../lib/fechas";
import type { Sector, SectorPayload, UsuarioOption } from "../types/vacaciones";

interface Props {
  sectores: Sector[];
  usuarios: UsuarioOption[];
  puedeGestionar: boolean;
  abrirAlta: boolean;
  onCerrarAlta: () => void;
  onChanged: () => void;
}

export function SectoresTab({
  sectores,
  usuarios,
  puedeGestionar,
  abrirAlta,
  onCerrarAlta,
  onChanged,
}: Props) {
  const [editando, setEditando] = useState<Sector | null>(null);

  return (
    <div className="flex flex-col gap-4">
      {sectores.length === 0 ? (
        <BrandEmptyState
          icon={Building2}
          title="No hay sectores"
          description="Creá el primer sector para poder dar de alta empleados."
        />
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {sectores.map((s) => (
            <div
              key={s.id}
              className="flex items-start justify-between gap-3 rounded-[12px] border border-border bg-card p-5"
            >
              <div className="flex items-start gap-3">
                <span
                  className="mt-0.5 h-9 w-9 shrink-0 rounded-[10px]"
                  style={{ backgroundColor: s.color }}
                />
                <div>
                  <p className="font-heading text-sm font-bold text-foreground">{s.name}</p>
                  <p className="font-body text-xs text-muted-foreground">
                    {s.empleadosCount}{" "}
                    {s.empleadosCount === 1 ? "empleado activo" : "empleados activos"}
                  </p>
                  <p className="mt-1 font-body text-xs text-muted-foreground">
                    {s.jefes.length > 0
                      ? `Jefe: ${s.jefes.map((j) => j.fullName).join(", ")}`
                      : "Sin jefe asignado"}
                  </p>
                </div>
              </div>
              {puedeGestionar && (
                <button
                  type="button"
                  onClick={() => setEditando(s)}
                  className="rounded-[8px] border border-border px-3 py-1.5 font-body text-xs font-semibold text-foreground hover:bg-muted"
                >
                  Editar
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {(abrirAlta || editando) && (
        <SectorModal
          sector={editando}
          usuarios={usuarios}
          onClose={() => {
            onCerrarAlta();
            setEditando(null);
          }}
          onSaved={() => {
            onCerrarAlta();
            setEditando(null);
            onChanged();
          }}
        />
      )}
    </div>
  );
}

function SectorModal({
  sector,
  usuarios,
  onClose,
  onSaved,
}: {
  sector: Sector | null;
  usuarios: UsuarioOption[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<SectorPayload>({
    name: sector?.name ?? "",
    color: sector?.color ?? COLORES_IDENTIDAD[0],
    jefeUserId: sector?.jefes[0]?.id ?? null,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const guardar = () => {
    setBusy(true);
    setError(null);
    const req = sector
      ? gestionApi.updateSector(sector.id, form)
      : gestionApi.createSector(form);
    req
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo guardar el sector.");
      })
      .finally(() => setBusy(false));
  };

  const eliminar = () => {
    if (!sector) return;
    setBusy(true);
    gestionApi
      .deleteSector(sector.id)
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo eliminar el sector.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={sector ? "Editar sector" : "Nuevo sector"}
      widthPx={460}
      error={error}
    >
      <div className="flex flex-col gap-4">
        <BrandInput
          label="Nombre del sector"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
        <BrandSelect
          label="Jefe de sector"
          hint="Aprueba las solicitudes del sector (permiso approve + este vínculo)"
          value={form.jefeUserId ?? ""}
          onChange={(e) =>
            setForm((f) => ({ ...f, jefeUserId: e.target.value || null }))
          }
        >
          <option value="">Sin jefe asignado</option>
          {usuarios.map((u) => (
            <option key={u.id} value={u.id}>
              {u.fullName} · {u.email}
            </option>
          ))}
        </BrandSelect>
        <div>
          <span className="mb-1.5 block font-body text-[13px] font-semibold text-foreground">
            Color del sector
          </span>
          <div className="flex gap-2">
            {COLORES_IDENTIDAD.map((c) => (
              <button
                key={c}
                type="button"
                aria-label={`Color ${c}`}
                onClick={() => setForm((f) => ({ ...f, color: c }))}
                className={
                  form.color === c
                    ? "h-7 w-7 rounded-[8px] ring-2 ring-brand-orange ring-offset-2 ring-offset-background"
                    : "h-7 w-7 rounded-[8px] opacity-70 hover:opacity-100"
                }
                style={{ backgroundColor: c }}
              />
            ))}
          </div>
        </div>
        <div className="mt-1 flex items-center justify-between gap-2">
          {sector ? (
            <BrandButton
              variant="outline"
              onClick={eliminar}
              disabled={busy}
              className="border-destructive/40 text-destructive hover:bg-destructive/10"
            >
              Eliminar
            </BrandButton>
          ) : (
            <span />
          )}
          <div className="flex gap-2">
            <BrandButton variant="outline" onClick={onClose} disabled={busy}>
              Cancelar
            </BrandButton>
            <BrandButton onClick={guardar} loading={busy}>
              {sector ? "Guardar cambios" : "Crear sector"}
            </BrandButton>
          </div>
        </div>
      </div>
    </BrandModal>
  );
}
