"use client";

import { useState } from "react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { gestionApi } from "../api/gestion-api";
import { COLORES_IDENTIDAD, hoyIso } from "../lib/fechas";
import type {
  Cargo,
  EmpleadoListItem,
  EmpleadoPayload,
  Sector,
  UsuarioOption,
} from "../types/vacaciones";

interface Props {
  empleado: EmpleadoListItem | null;
  sectores: Sector[];
  cargos: Cargo[];
  usuarios: UsuarioOption[];
  onClose: () => void;
  onSaved: () => void;
  onDeleted: () => void;
  deleteFn?: () => Promise<void>;
}

export function EmpleadoModal({
  empleado,
  sectores,
  cargos,
  usuarios,
  onClose,
  onSaved,
  onDeleted,
  deleteFn,
}: Props) {
  const [form, setForm] = useState<EmpleadoPayload>({
    firstName: empleado?.firstName ?? "",
    lastName: empleado?.lastName ?? "",
    email: empleado?.email ?? "",
    hireDate: empleado?.hireDate ?? hoyIso(),
    departmentId: empleado?.departmentId ?? sectores[0]?.id ?? "",
    cargoId: empleado?.cargoId ?? cargos[0]?.id ?? "",
    color: empleado?.color ?? COLORES_IDENTIDAD[0],
    status: empleado?.status ?? "ACTIVE",
    userId: empleado?.userId ?? null,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof EmpleadoPayload>(key: K, value: EmpleadoPayload[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const guardar = () => {
    setBusy(true);
    setError(null);
    const req = empleado
      ? gestionApi.updateEmpleado(empleado.id, form)
      : gestionApi.createEmpleado(form);
    req
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo guardar el empleado.");
      })
      .finally(() => setBusy(false));
  };

  const eliminar = () => {
    if (!deleteFn) return;
    setBusy(true);
    deleteFn()
      .then(onDeleted)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo eliminar el empleado.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={empleado ? "Editar empleado" : "Nuevo empleado"}
      widthPx={520}
      error={error}
    >
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <BrandInput
            label="Nombre"
            value={form.firstName}
            onChange={(e) => set("firstName", e.target.value)}
          />
          <BrandInput
            label="Apellido"
            value={form.lastName}
            onChange={(e) => set("lastName", e.target.value)}
          />
        </div>
        <BrandInput
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => set("email", e.target.value)}
        />
        <div className="grid grid-cols-2 gap-3">
          <BrandInput
            label="Fecha de ingreso"
            type="date"
            value={form.hireDate}
            onChange={(e) => set("hireDate", e.target.value)}
            hint="Define los días anuales por antigüedad"
          />
          <BrandSelect
            label="Estado"
            value={form.status}
            onChange={(e) => set("status", e.target.value as "ACTIVE" | "INACTIVE")}
          >
            <option value="ACTIVE">Activo</option>
            <option value="INACTIVE">Inactivo</option>
          </BrandSelect>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <BrandSelect
            label="Sector"
            value={form.departmentId}
            onChange={(e) => set("departmentId", e.target.value)}
          >
            {sectores.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </BrandSelect>
          <BrandSelect
            label="Cargo"
            value={form.cargoId}
            onChange={(e) => set("cargoId", e.target.value)}
          >
            {cargos.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </BrandSelect>
        </div>
        <BrandSelect
          label="Cuenta vinculada"
          hint="Cuenta de la plataforma para que el empleado vea su saldo y pida vacaciones"
          value={form.userId ?? ""}
          onChange={(e) => set("userId", e.target.value || null)}
        >
          <option value="">Sin cuenta vinculada</option>
          {usuarios.map((u) => (
            <option key={u.id} value={u.id}>
              {u.fullName} · {u.email}
            </option>
          ))}
        </BrandSelect>
        <div>
          <span className="mb-1.5 block font-body text-[13px] font-semibold text-foreground">
            Color de identidad
          </span>
          <div className="flex gap-2">
            {COLORES_IDENTIDAD.map((c) => (
              <button
                key={c}
                type="button"
                aria-label={`Color ${c}`}
                onClick={() => set("color", c)}
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
          {empleado && deleteFn ? (
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
              {empleado ? "Guardar cambios" : "Crear empleado"}
            </BrandButton>
          </div>
        </div>
      </div>
    </BrandModal>
  );
}
