"use client";

import { useState } from "react";
import { toast } from "sonner";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { personasApi, type DatosPersona, type Persona } from "../../api/personas-api";
import { SelectorColor } from "../selector-color";

interface Props {
  persona: Persona;
  onGuardada: (persona: Persona) => void;
}

/** Nombre, mail y color: una sola edición que se escribe en la ficha y en la
 * cuenta (ADR-040). */
export function DatosTab({ persona, onGuardada }: Props) {
  const { can } = useSession();
  const puedeEditar = can("personas", "update");
  // Cambiar el mail de quien entra a la app cambia su login: exige gestionar accesos.
  const mailBloqueado = persona.entraALaApp && !can("personas", "manage");
  const [form, setForm] = useState<DatosPersona>({
    firstName: persona.firstName,
    lastName: persona.lastName,
    email: persona.email,
    color: persona.color,
  });
  const [busy, setBusy] = useState(false);
  const cambios = (Object.keys(form) as (keyof DatosPersona)[]).some((k) => form[k] !== persona[k]);

  const set = <K extends keyof DatosPersona>(key: K, value: DatosPersona[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const guardar = () => {
    setBusy(true);
    personasApi
      .updateDatos(persona.id, form)
      .then((p) => {
        toast.success("Datos guardados");
        onGuardada(p);
      })
      .catch((err: unknown) => {
        toast.error(err instanceof ApiError ? err.message : "No se pudieron guardar los datos.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <div className="flex max-w-[560px] flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        <BrandInput label="Nombre" value={form.firstName} disabled={!puedeEditar} onChange={(e) => set("firstName", e.target.value)} />
        <BrandInput label="Apellido" value={form.lastName} disabled={!puedeEditar} onChange={(e) => set("lastName", e.target.value)} />
      </div>
      <BrandInput
        label="Email"
        type="email"
        value={form.email}
        disabled={!puedeEditar || mailBloqueado}
        onChange={(e) => set("email", e.target.value)}
        hint={
          mailBloqueado
            ? "Entra a la app con este mail: solo quien gestiona accesos puede cambiarlo."
            : persona.entraALaApp
              ? "Es también el mail con el que inicia sesión."
              : undefined
        }
      />
      <SelectorColor value={form.color} onChange={(c) => set("color", c)} disabled={!puedeEditar} />
      <p className="font-body text-xs text-muted-foreground">
        El color se usa en toda la app: turnos, calendario de vacaciones y avatar.
      </p>
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
