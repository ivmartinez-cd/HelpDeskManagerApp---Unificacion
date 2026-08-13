"use client";

import { useState, type FormEvent } from "react";
import { prestadoresApi } from "../api/prestadores-api";
import type { OperadorOption, Prestador } from "../types/prestadores";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";

const SIN_ASIGNAR = "__sin_asignar__";

interface PrestadorFormModalProps {
  prestador: Prestador | null;
  operadores: OperadorOption[];
  onClose: () => void;
  onSaved: () => void;
}

/** Alta de un PST nuevo (con `siges_empresa_id` real, verificado a mano contra
 * Siges) o edición de sus datos propios. La asignación de operador en el alta
 * es un atajo (crea el primer tramo de historial); reasignar después usa
 * `AssignOperadorModal`. */
export function PrestadorFormModal({
  prestador,
  operadores,
  onClose,
  onSaved,
}: PrestadorFormModalProps) {
  const isEdit = prestador !== null;
  const [sigesEmpresaId, setSigesEmpresaId] = useState(
    prestador ? String(prestador.sigesEmpresaId) : "",
  );
  const [denComercial, setDenComercial] = useState(prestador?.denComercial ?? "");
  const [razonSocial, setRazonSocial] = useState(prestador?.razonSocial ?? "");
  const [cuit, setCuit] = useState(prestador?.cuit ?? "");
  const [equipos, setEquipos] = useState(
    prestador?.equipos != null ? String(prestador.equipos) : "",
  );
  const [operadorId, setOperadorId] = useState(prestador?.operadorId ?? SIN_ASIGNAR);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const request = isEdit
      ? prestadoresApi.updatePrestador(prestador.id, {
          denComercial,
          razonSocial: razonSocial || null,
          cuit: cuit || null,
          equipos: equipos === "" ? null : Number(equipos),
        })
      : prestadoresApi.createPrestador({
          sigesEmpresaId: Number(sigesEmpresaId),
          denComercial,
          razonSocial: razonSocial || null,
          cuit: cuit || null,
          equipos: equipos === "" ? null : Number(equipos),
          operadorId: operadorId === SIN_ASIGNAR ? null : operadorId,
        });
    request
      .then(onSaved)
      .catch((err: unknown) => {
        console.error("Error al guardar el PST:", err);
        setError(err instanceof Error ? err.message : "No se pudo guardar el PST.");
      })
      .finally(() => setSaving(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={isEdit ? "Editar PST" : "Nuevo PST"}
      widthPx={460}
      error={error}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <BrandInput
          label="ID de Siges (ID_Empresa)"
          type="number"
          value={sigesEmpresaId}
          onChange={(e) => setSigesEmpresaId(e.target.value)}
          disabled={isEdit}
          hint={
            isEdit
              ? "No se puede cambiar una vez creado."
              : "Verificar contra Siges antes de cargar — es la clave que vincula este PST con SLA."
          }
          required
        />
        <BrandInput
          label="Denominación comercial"
          value={denComercial}
          onChange={(e) => setDenComercial(e.target.value)}
          required
        />
        <BrandInput
          label="Razón social"
          value={razonSocial}
          onChange={(e) => setRazonSocial(e.target.value)}
        />
        <BrandInput label="CUIT" value={cuit} onChange={(e) => setCuit(e.target.value)} />
        <BrandInput
          label="Parque de impresoras"
          type="number"
          value={equipos}
          onChange={(e) => setEquipos(e.target.value)}
          hint="Cantidad de equipos del parque asignado a este PST."
        />
        {!isEdit && (
          <BrandSelect
            label="Operador"
            value={operadorId}
            onChange={(e) => setOperadorId(e.target.value)}
          >
            <option value={SIN_ASIGNAR}>Sin asignar</option>
            {operadores.map((op) => (
              <option key={op.id} value={op.id}>
                {op.fullName}
              </option>
            ))}
          </BrandSelect>
        )}
        <div className="mt-2 flex justify-end gap-2">
          <BrandButton type="button" variant="outline" onClick={onClose}>
            Cancelar
          </BrandButton>
          <BrandButton type="submit" loading={saving}>
            Guardar
          </BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
