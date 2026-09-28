"use client";

import { useEffect, useState } from "react";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
import { COLORES_IDENTIDAD, hoyIso } from "@/features/vacaciones/lib/fechas";
import type { Cargo, EmpleadoPayload, Sector } from "@/features/vacaciones/types/vacaciones";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SelectorColor } from "./selector-color";

interface Props {
  onClose: () => void;
  onCreada: (id: string) => void;
}

/** Alta de persona = alta de su ficha de empleado (toda persona tiene ficha,
 * ADR-040). El acceso a la app se da después, desde la ficha. */
export function NuevaPersonaModal({ onClose, onCreada }: Props) {
  const [sectores, setSectores] = useState<Sector[]>([]);
  const [cargos, setCargos] = useState<Cargo[]>([]);
  const [form, setForm] = useState<EmpleadoPayload>({
    firstName: "", lastName: "", email: "", hireDate: hoyIso(), departmentId: "", cargoId: "",
    color: COLORES_IDENTIDAD[0], status: "ACTIVE", userId: null,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([gestionApi.listSectores(), gestionApi.listCargos()])
      .then(([secs, cars]) => {
        setSectores(secs);
        setCargos(cars);
        setForm((f) => ({ ...f, departmentId: secs[0]?.id ?? "", cargoId: cars[0]?.id ?? "" }));
      })
      .catch(() => setError("No se pudieron cargar sectores y cargos."));
  }, []);

  const set = <K extends keyof EmpleadoPayload>(key: K, value: EmpleadoPayload[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const crear = () => {
    setBusy(true);
    setError(null);
    gestionApi
      .createEmpleado(form)
      .then((e) => onCreada(e.id))
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo crear la persona.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal isOpen onClose={onClose} title="Nueva persona" widthPx={520} error={error}>
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <BrandInput label="Nombre" value={form.firstName} onChange={(e) => set("firstName", e.target.value)} />
          <BrandInput label="Apellido" value={form.lastName} onChange={(e) => set("lastName", e.target.value)} />
        </div>
        <BrandInput label="Email" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
        <BrandInput
          label="Fecha de ingreso"
          type="date"
          value={form.hireDate}
          onChange={(e) => set("hireDate", e.target.value)}
          hint="Define los días anuales de vacaciones por antigüedad"
        />
        <div className="grid grid-cols-2 gap-3">
          <BrandSelect label="Sector" value={form.departmentId} onChange={(e) => set("departmentId", e.target.value)}>
            {sectores.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </BrandSelect>
          <BrandSelect label="Cargo" value={form.cargoId} onChange={(e) => set("cargoId", e.target.value)}>
            {cargos.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </BrandSelect>
        </div>
        <SelectorColor value={form.color} onChange={(c) => set("color", c)} />
        <p className="font-body text-xs text-muted-foreground">
          Para que entre a la app, después de crearla usá &quot;Dar acceso&quot; en su ficha.
        </p>
        <div className="mt-1 flex justify-end gap-2">
          <BrandButton variant="outline" onClick={onClose} disabled={busy}>Cancelar</BrandButton>
          <BrandButton onClick={crear} loading={busy} disabled={!form.departmentId || !form.cargoId}>
            Crear persona
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
