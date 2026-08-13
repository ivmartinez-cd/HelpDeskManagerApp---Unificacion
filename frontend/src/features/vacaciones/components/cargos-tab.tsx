"use client";

import { useState } from "react";
import { Briefcase } from "lucide-react";
import { ApiError } from "@/services/http-client";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { gestionApi } from "../api/gestion-api";
import type { Cargo, CargoPayload } from "../types/vacaciones";

interface Props {
  cargos: Cargo[];
  puedeGestionar: boolean;
  abrirAlta: boolean;
  onCerrarAlta: () => void;
  onChanged: () => void;
}

export function CargosTab({
  cargos,
  puedeGestionar,
  abrirAlta,
  onCerrarAlta,
  onChanged,
}: Props) {
  const [editando, setEditando] = useState<Cargo | null>(null);

  return (
    <div className="flex flex-col gap-4">
      {cargos.length === 0 ? (
        <BrandEmptyState
          icon={Briefcase}
          title="No hay cargos"
          description="Creá el primer cargo para poder dar de alta empleados."
        />
      ) : (
        <div className="overflow-x-auto rounded-[12px] border border-border">
          <table className="w-full min-w-[560px] font-body text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                <th className="px-4 py-3">Cargo</th>
                <th className="px-4 py-3 text-right">Empleados</th>
                <th className="px-4 py-3 text-right">Límite simultáneo</th>
                {puedeGestionar && <th className="px-4 py-3" />}
              </tr>
            </thead>
            <tbody>
              {cargos.map((c) => (
                <tr key={c.id} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-3 font-semibold text-foreground">{c.name}</td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {c.empleadosCount}
                  </td>
                  <td className="px-4 py-3 text-right text-foreground">
                    {c.maxSimultaneos ?? "Sin límite"}
                  </td>
                  {puedeGestionar && (
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setEditando(c)}
                        className="rounded-[8px] border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted"
                      >
                        Editar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(abrirAlta || editando) && (
        <CargoModal
          cargo={editando}
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

function CargoModal({
  cargo,
  onClose,
  onSaved,
}: {
  cargo: Cargo | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<CargoPayload>({
    name: cargo?.name ?? "",
    maxSimultaneos: cargo?.maxSimultaneos ?? null,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const guardar = () => {
    setBusy(true);
    setError(null);
    const req = cargo ? gestionApi.updateCargo(cargo.id, form) : gestionApi.createCargo(form);
    req
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo guardar el cargo.");
      })
      .finally(() => setBusy(false));
  };

  const eliminar = () => {
    if (!cargo) return;
    setBusy(true);
    gestionApi
      .deleteCargo(cargo.id)
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo eliminar el cargo.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={cargo ? "Editar cargo" : "Nuevo cargo"}
      widthPx={440}
      error={error}
    >
      <div className="flex flex-col gap-4">
        <BrandInput
          label="Nombre del cargo"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
        <BrandInput
          label="Límite de vacaciones simultáneas"
          hint="Máximo de empleados del cargo de vacaciones el mismo día. Vacío = sin límite."
          type="number"
          min={1}
          value={form.maxSimultaneos ?? ""}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              maxSimultaneos: e.target.value === "" ? null : Number(e.target.value),
            }))
          }
        />
        <div className="mt-1 flex items-center justify-between gap-2">
          {cargo ? (
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
              {cargo ? "Guardar cambios" : "Crear cargo"}
            </BrandButton>
          </div>
        </div>
      </div>
    </BrandModal>
  );
}
