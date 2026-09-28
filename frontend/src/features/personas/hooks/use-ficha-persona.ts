"use client";

import { useCallback, useEffect, useState } from "react";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
import type { EmpleadoListItem } from "@/features/vacaciones/types/vacaciones";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import { personasApi, type Persona } from "../api/personas-api";

export type PestanaFicha = "datos" | "laboral" | "acceso";

/** Ficha de una persona: sus datos (Personas) y, para quien ve vacaciones, su
 * ficha laboral completa (no hay GET individual de empleado: la lista es chica). */
export function useFichaPersona(id: string) {
  const { can } = useSession();
  const conLaboral = can("vacaciones", "view");
  const [persona, setPersona] = useState<Persona | null>(null);
  const [laboral, setLaboral] = useState<EmpleadoListItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recargar = useCallback(() => {
    Promise.all([
      personasApi.get(id),
      conLaboral ? gestionApi.listEmpleados() : Promise.resolve([] as EmpleadoListItem[]),
    ])
      .then(([p, empleados]) => {
        setPersona(p);
        setLaboral(empleados.find((e) => e.id === id) ?? null);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo cargar la persona.");
      });
  }, [id, conLaboral]);

  useEffect(() => {
    recargar();
  }, [recargar]);

  const pestanas: { value: PestanaFicha; label: string }[] = [
    { value: "datos", label: "Datos" },
    ...(conLaboral ? [{ value: "laboral" as const, label: "Laboral" }] : []),
    // Recursos Humanos no ve la pestaña Acceso (plan de unificación).
    ...(can("personas", "manage") ? [{ value: "acceso" as const, label: "Acceso a la app" }] : []),
  ];

  return { persona, setPersona, laboral, error, recargar, pestanas };
}
