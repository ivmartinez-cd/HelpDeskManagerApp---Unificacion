"use client";

import { useState, type FormEvent } from "react";
import { prestadoresApi } from "../api/prestadores-api";
import type { OperadorOption, Prestador } from "../types/prestadores";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { useModalSubmit } from "@/shared/hooks/use-modal-submit";

const SIN_ASIGNAR = "__sin_asignar__";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

interface AssignOperadorModalProps {
  prestador: Prestador;
  operadores: OperadorOption[];
  onClose: () => void;
  onAssigned: () => void;
}

/** Reasignación de operador de un PST — cada reasignación abre un tramo
 * nuevo en el historial y cierra el anterior (ver assign_operador.py). */
export function AssignOperadorModal({
  prestador,
  operadores,
  onClose,
  onAssigned,
}: AssignOperadorModalProps) {
  const [operadorId, setOperadorId] = useState(prestador.operadorId ?? SIN_ASIGNAR);
  const [desde, setDesde] = useState(today());
  const { saving, error, submit } = useModalSubmit();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submit(async () => {
      try {
        await prestadoresApi.assignOperador(
          prestador.id,
          operadorId === SIN_ASIGNAR ? null : operadorId,
          desde,
        );
      } catch (err: unknown) {
        console.error("Error al reasignar el PST:", err);
        throw err;
      }
      onAssigned();
    }, "No se pudo reasignar el PST.");
  };

  return (
    <BrandModal isOpen onClose={onClose} title="Reasignar operador" widthPx={420} error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">{prestador.denComercial}</p>
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
        <BrandInput
          label="Desde"
          type="date"
          value={desde}
          onChange={(e) => setDesde(e.target.value)}
          required
        />
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
