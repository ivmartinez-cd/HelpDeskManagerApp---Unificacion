"use client";

import { useState, type FormEvent } from "react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";

interface CreateUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (email: string, fullName: string) => Promise<boolean>;
}

export function CreateUserModal({ isOpen, onClose, onCreate }: CreateUserModalProps) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleClose(): void {
    setEmail("");
    setFullName("");
    onClose();
  }

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    const ok = await onCreate(email, fullName);
    setSubmitting(false);
    if (ok) handleClose();
  }

  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title="Nuevo usuario">
      <p className="mb-5 font-body text-xs text-[#9a9a9a]">
        Se envía un link de activación por email.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <BrandInput
          id="new-user-email"
          label="Email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="nombre.apellido@empresa.com"
          autoComplete="off"
          required
        />
        <BrandInput
          id="new-user-full-name"
          label="Nombre completo"
          type="text"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          placeholder="Nombre Apellido"
          autoComplete="off"
          required
        />
        <div className="flex justify-end gap-3 pt-2">
          <BrandButton type="button" variant="outline" onClick={handleClose}>
            Cancelar
          </BrandButton>
          <BrandButton type="submit" loading={submitting}>
            Crear usuario
          </BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
