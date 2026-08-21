"use client";

import type { Dispatch, FormEvent, SetStateAction } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Modal } from "@/shared/components/ui/modal";

interface Props {
  isOpen: boolean;
  isEditing: boolean;
  nombre: string;
  setNombre: Dispatch<SetStateAction<string>>;
  onClose: () => void;
  onSubmit: (e: FormEvent) => void;
}

/** Modal de alta/edición de casilla, extraído de `casillas-manager.tsx` (§4). */
export function CasillaFormModal({ isOpen, isEditing, nombre, setNombre, onClose, onSubmit }: Props) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? "Editar Casilla" : "Nueva Casilla"}>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="font-body text-xs font-semibold text-foreground">
            Nombre de la Casilla (ej. INSUMOS, ST)
          </label>
          <Input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Nombre"
            required
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit">Guardar</Button>
        </div>
      </form>
    </Modal>
  );
}
