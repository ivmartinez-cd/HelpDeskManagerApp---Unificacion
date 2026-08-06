"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/shared/components/ui/modal";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";

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
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Nuevo usuario"
      subtitle="Se envía un link de activación por email"
      maxWidth="max-w-md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="new-user-email"
          label="Email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="nombre.apellido@empresa.com"
          autoComplete="off"
          required
        />
        <Input
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
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancelar
          </Button>
          <Button type="submit" loading={submitting}>
            Crear usuario
          </Button>
        </div>
      </form>
    </Modal>
  );
}
