"use client";

import { useState, type FormEvent } from "react";
import { prestadoresApi } from "../api/prestadores-api";
import type { Contacto } from "../types/prestadores";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";

interface ContactoFormModalProps {
  prestadorId: string;
  contacto: Contacto | null;
  onClose: () => void;
  onSaved: () => void;
}

/** Alta/edición de un contacto de PST — un PST real puede tener varios (ej.
 * San Juan tiene 3 en la planilla de origen), por eso vive separado del
 * formulario del PST en sí. */
export function ContactoFormModal({
  prestadorId,
  contacto,
  onClose,
  onSaved,
}: ContactoFormModalProps) {
  const [nombre, setNombre] = useState(contacto?.nombre ?? "");
  const [telefono, setTelefono] = useState(contacto?.telefono ?? "");
  const [email, setEmail] = useState(contacto?.email ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const payload = {
      nombre,
      telefono: telefono || null,
      email: email || null,
      isPrincipal: contacto?.isPrincipal ?? false,
      sortOrder: contacto?.sortOrder ?? 0,
    };
    const request = contacto
      ? prestadoresApi.updateContacto(prestadorId, contacto.id, payload)
      : prestadoresApi.createContacto(prestadorId, payload);
    request
      .then(onSaved)
      .catch((err: unknown) => {
        console.error("Error al guardar el contacto:", err);
        setError(err instanceof Error ? err.message : "No se pudo guardar el contacto.");
      })
      .finally(() => setSaving(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={contacto ? "Editar contacto" : "Nuevo contacto"}
      widthPx={420}
      error={error}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <BrandInput
          label="Nombre"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
        />
        <BrandInput
          label="Teléfono"
          value={telefono}
          onChange={(e) => setTelefono(e.target.value)}
        />
        <BrandInput
          label="Correo electrónico"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
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
