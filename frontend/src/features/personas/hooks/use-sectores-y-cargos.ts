"use client";

import { useEffect, useState } from "react";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
import type { Cargo, Sector } from "@/features/vacaciones/types/vacaciones";

interface Opciones {
  /** Después de cargar (p. ej. para precargar el formulario con el primero). */
  alCargar?: (sectores: Sector[], cargos: Cargo[]) => void;
  /** Cada pantalla avisa el error a su manera (toast o error del modal). */
  alFallar: () => void;
}

/** Catálogos de sectores y cargos de Gestión de Personal, una vez al montar. */
export function useSectoresYCargos({ alCargar, alFallar }: Opciones) {
  const [sectores, setSectores] = useState<Sector[]>([]);
  const [cargos, setCargos] = useState<Cargo[]>([]);

  useEffect(() => {
    Promise.all([gestionApi.listSectores(), gestionApi.listCargos()])
      .then(([secs, cars]) => {
        setSectores(secs);
        setCargos(cars);
        alCargar?.(secs, cars);
      })
      .catch(alFallar);
    // Solo al montar: los callbacks son inline en el caller y no deben re-disparar la carga.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { sectores, cargos };
}
