"use client";

import type { Dispatch, FormEvent, SetStateAction } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Modal } from "@/shared/components/ui/modal";
import type { UserOption } from "../../types/turnos";

interface Props {
  isOpen: boolean;
  isEditing: boolean;
  horaInicio: string;
  setHoraInicio: Dispatch<SetStateAction<string>>;
  horaFin: string;
  setHoraFin: Dispatch<SetStateAction<string>>;
  users: UserOption[];
  selectedUserIds: string[];
  setSelectedUserIds: Dispatch<SetStateAction<string[]>>;
  onClose: () => void;
  onSubmit: (e: FormEvent) => void;
}

/** Modal de alta/edición de franja horaria + asignación de operadores,
 * extraído de `casillas-manager.tsx` (§4). */
export function SlotFormModal({
  isOpen, isEditing, horaInicio, setHoraInicio, horaFin, setHoraFin,
  users, selectedUserIds, setSelectedUserIds, onClose, onSubmit,
}: Props) {
  function toggleUser(userId: string, checked: boolean) {
    setSelectedUserIds((prev) =>
      checked ? [...prev, userId] : prev.filter((id) => id !== userId)
    );
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? "Editar Franja Horaria" : "Nueva Franja Horaria"}
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="font-body text-xs font-semibold text-foreground">
              Hora Inicio (HH:MM)
            </label>
            <Input
              type="time"
              value={horaInicio}
              onChange={(e) => setHoraInicio(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="font-body text-xs font-semibold text-foreground">
              Hora Fin (HH:MM)
            </label>
            <Input
              type="time"
              value={horaFin}
              onChange={(e) => setHoraFin(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="font-body text-xs font-semibold text-foreground">
            Seleccionar Operadores para este horario
          </label>
          <div className="max-h-48 overflow-y-auto rounded-[8px] border border-border bg-muted/30 p-2.5 flex flex-col gap-1.5">
            {users.map((u) => {
              const checked = selectedUserIds.includes(u.id);
              return (
                <label
                  key={u.id}
                  className="flex items-center gap-2 cursor-pointer rounded-md p-1.5 hover:bg-muted"
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => toggleUser(u.id, e.target.checked)}
                    className="rounded border-border text-brand-orange focus:ring-brand-orange"
                  />
                  <span className="font-body text-xs text-foreground font-medium">
                    {u.fullName}
                  </span>
                </label>
              );
            })}
            {users.length === 0 && (
              <span className="font-body text-xs text-muted-foreground">
                No hay operadores disponibles.
              </span>
            )}
          </div>
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
