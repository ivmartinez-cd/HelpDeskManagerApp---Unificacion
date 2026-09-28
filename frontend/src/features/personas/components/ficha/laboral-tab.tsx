"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
import { formatAntiguedad } from "@/features/vacaciones/lib/fechas";
import type {
  Cargo,
  EmpleadoListItem,
  EstadoEmpleado,
  Sector,
} from "@/features/vacaciones/types/vacaciones";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandInput, BrandSelect, BrandStatTile } from "@/shared/components/ui/brand-form";

interface Props {
  laboral: EmpleadoListItem;
  onGuardada: () => void;
}

interface FormLaboral {
  hireDate: string;
  status: EstadoEmpleado;
  departmentId: string;
  cargoId: string;
}

/** Datos laborales: se siguen editando por el ABM de empleados de Gestión de
 * Personal (vacaciones.manage), que recalcula días y audita el cambio. */
export function LaboralTab({ laboral, onGuardada }: Props) {
  const { can } = useSession();
  const puedeEditar = can("vacaciones", "manage");
  const [sectores, setSectores] = useState<Sector[]>([]);
  const [cargos, setCargos] = useState<Cargo[]>([]);
  const [form, setForm] = useState<FormLaboral>({
    hireDate: laboral.hireDate,
    status: laboral.status,
    departmentId: laboral.departmentId,
    cargoId: laboral.cargoId,
  });
  const [busy, setBusy] = useState(false);
  const cambios = (Object.keys(form) as (keyof FormLaboral)[]).some((k) => form[k] !== laboral[k]);

  useEffect(() => {
    Promise.all([gestionApi.listSectores(), gestionApi.listCargos()])
      .then(([secs, cars]) => {
        setSectores(secs);
        setCargos(cars);
      })
      .catch(() => toast.error("No se pudieron cargar sectores y cargos."));
  }, []);

  const set = <K extends keyof FormLaboral>(key: K, value: FormLaboral[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const guardar = () => {
    setBusy(true);
    const { firstName, lastName, email, color, userId } = laboral;
    gestionApi
      .updateEmpleado(laboral.id, { firstName, lastName, email, color, userId, ...form })
      .then(() => {
        toast.success("Datos laborales guardados");
        onGuardada();
      })
      .catch((err: unknown) => {
        toast.error(err instanceof ApiError ? err.message : "No se pudieron guardar los datos laborales.");
      })
      .finally(() => setBusy(false));
  };

  const s = laboral.saldo;
  return (
    <div className="flex max-w-[560px] flex-col gap-5">
      <div className="grid grid-cols-3 gap-3">
        <BrandStatTile label="Disponibles" value={s.available} tone="highlight" hint={`de ${s.annual + s.carryOver} este año`} />
        <BrandStatTile label="Días anuales" value={laboral.diasAnuales} hint={formatAntiguedad(laboral.antiguedadAnios)} />
        <BrandStatTile label="Legajo Siges" value={laboral.sigesEmpresaId ?? "—"} hint={laboral.sigesEmpresaId ? "Vinculado" : "Sin vincular"} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <BrandInput
          label="Fecha de ingreso"
          type="date"
          value={form.hireDate}
          disabled={!puedeEditar}
          onChange={(e) => set("hireDate", e.target.value)}
          hint="Define los días anuales por antigüedad"
        />
        <BrandSelect label="Estado" value={form.status} disabled={!puedeEditar} onChange={(e) => set("status", e.target.value as EstadoEmpleado)}>
          <option value="ACTIVE">Activa</option>
          <option value="INACTIVE">Inactiva</option>
        </BrandSelect>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <BrandSelect label="Sector" value={form.departmentId} disabled={!puedeEditar} onChange={(e) => set("departmentId", e.target.value)}>
          {sectores.length === 0 && <option value={laboral.departmentId}>{laboral.sectorNombre}</option>}
          {sectores.map((sec) => (
            <option key={sec.id} value={sec.id}>{sec.name}</option>
          ))}
        </BrandSelect>
        <BrandSelect label="Cargo" value={form.cargoId} disabled={!puedeEditar} onChange={(e) => set("cargoId", e.target.value)}>
          {cargos.length === 0 && <option value={laboral.cargoId}>{laboral.cargoNombre}</option>}
          {cargos.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </BrandSelect>
      </div>
      {puedeEditar && (
        <div>
          <BrandButton onClick={guardar} loading={busy} disabled={!cambios}>
            Guardar cambios
          </BrandButton>
        </div>
      )}
    </div>
  );
}
