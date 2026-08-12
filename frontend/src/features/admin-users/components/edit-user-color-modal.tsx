"use client";

import { useState, type FormEvent } from "react";
import type { AdminUser } from "../api/admin-users-api";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton } from "@/shared/components/ui/brand-form";

interface EditUserColorModalProps {
  user: AdminUser | null;
  onClose: () => void;
  onSave: (user: AdminUser, color: string) => Promise<boolean>;
}

const DEFAULT_COLOR = "#F7941D";

export function EditUserColorModal({ user, onClose, onSave }: EditUserColorModalProps) {
  const [color, setColor] = useState(user?.color ?? DEFAULT_COLOR);
  const [submitting, setSubmitting] = useState(false);

  // El color inicial depende de `user`, que llega recién al abrir el modal
  // (mismo patrón de "ajustar estado durante el render" que sla-detail.tsx).
  const [prevUserId, setPrevUserId] = useState(user?.id);
  if (user && user.id !== prevUserId) {
    setPrevUserId(user.id);
    setColor(user.color ?? DEFAULT_COLOR);
  }

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!user) return;
    setSubmitting(true);
    const ok = await onSave(user, color);
    setSubmitting(false);
    if (ok) onClose();
  }

  return (
    <BrandModal isOpen={user !== null} onClose={onClose} title="Color de identidad">
      {user && (
        <>
          <p className="mb-5 font-body text-xs text-muted-foreground">
            Color de {user.fullName} en las tarjetas de Turnos y el avatar — por default es el
            que ya tiene asignado en Gestión, pero se puede corregir a mano acá.
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={color}
                onChange={(event) => setColor(event.target.value)}
                className="h-11 w-14 cursor-pointer rounded-[8px] border border-border bg-card p-1"
                aria-label="Color"
              />
              <input
                type="text"
                value={color}
                onChange={(event) => setColor(event.target.value)}
                pattern="^#[0-9A-Fa-f]{6}$"
                placeholder="#F7941D"
                className="flex-1 rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <BrandButton type="button" variant="outline" onClick={onClose}>
                Cancelar
              </BrandButton>
              <BrandButton type="submit" loading={submitting}>
                Guardar
              </BrandButton>
            </div>
          </form>
        </>
      )}
    </BrandModal>
  );
}
