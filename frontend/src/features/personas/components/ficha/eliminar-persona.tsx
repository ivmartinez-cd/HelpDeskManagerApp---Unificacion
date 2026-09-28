"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
import { ApiError } from "@/services/http-client";
import { BrandButton } from "@/shared/components/ui/brand-form";

interface Props {
  personaId: string;
  nombre: string;
  entraALaApp: boolean;
}

/** Borrado de la ficha (vacaciones.manage). Borra en cascada su historial de
 * vacaciones y ausencias, así que lo normal es pasarla a inactiva; y no se
 * permite con acceso activo para no dejar una cuenta que entra sin ficha. */
export function EliminarPersona({ personaId, nombre, entraALaApp }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  const eliminar = () => {
    const ok = window.confirm(
      `¿Eliminar a ${nombre}? Se borran también todas sus vacaciones, ausencias y ciclos, y no se puede deshacer. ` +
        "Si solo dejó de trabajar, pasala a inactiva.",
    );
    if (!ok) return;
    setBusy(true);
    gestionApi
      .deleteEmpleado(personaId)
      .then(() => {
        toast.success(`${nombre} fue eliminada`);
        router.push("/personas");
      })
      .catch((err: unknown) => {
        toast.error(err instanceof ApiError ? err.message : "No se pudo eliminar la persona.");
        setBusy(false);
      });
  };

  return (
    <div className="flex flex-col gap-2 border-t border-border pt-5">
      <div>
        <BrandButton
          variant="outline"
          onClick={eliminar}
          loading={busy}
          disabled={entraALaApp}
          className="border-destructive/40 text-destructive hover:bg-destructive/10"
        >
          Eliminar persona
        </BrandButton>
      </div>
      <p className="font-body text-xs text-muted-foreground">
        {entraALaApp
          ? "Entra a la app: para eliminarla, primero quitale el acceso."
          : "Borra la ficha y todo su historial de vacaciones y ausencias."}
      </p>
    </div>
  );
}
