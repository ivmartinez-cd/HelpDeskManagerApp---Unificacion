"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
import type { EmpleadoListItem } from "@/features/vacaciones/types/vacaciones";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import { nombrePersona, personasApi, type Persona } from "../api/personas-api";

export type PersonaSortKey =
  | "nombre" | "sector" | "cargo" | "ingreso" | "disponibles" | "acceso" | "estado";
const SORT_KEYS: readonly PersonaSortKey[] = [
  "nombre", "sector", "cargo", "ingreso", "disponibles", "acceso", "estado",
];

/** Persona + sus datos laborales (ingreso, saldo), que salen de Gestión de
 * Personal y solo llegan a quien tiene permiso de ver vacaciones. */
export interface FilaPersona extends Persona {
  laboral: EmpleadoListItem | null;
}

export interface FiltrosPersonas {
  busqueda: string;
  sectorId: string;
  acceso: "" | "si" | "no";
  estado: "" | "activa" | "inactiva";
}

function valorOrden(f: FilaPersona, key: PersonaSortKey) {
  switch (key) {
    case "nombre": return nombrePersona(f).toLowerCase();
    case "sector": return f.sectorNombre.toLowerCase();
    case "cargo": return f.cargoNombre.toLowerCase();
    case "ingreso": return f.laboral?.hireDate;
    case "disponibles": return f.laboral?.saldo.available;
    // Ascendente = "Sí" / "Activa" primero, como se lee la columna.
    case "acceso": return f.entraALaApp ? 0 : 1;
    case "estado": return f.activa ? 0 : 1;
  }
}

function pasaFiltros(f: FilaPersona, filtros: FiltrosPersonas): boolean {
  if (filtros.sectorId && f.sectorId !== filtros.sectorId) return false;
  if (filtros.acceso && f.entraALaApp !== (filtros.acceso === "si")) return false;
  if (filtros.estado && f.activa !== (filtros.estado === "activa")) return false;
  const q = filtros.busqueda.trim().toLowerCase();
  if (!q) return true;
  return [nombrePersona(f), f.email, f.cargoNombre].some((v) => v.toLowerCase().includes(q));
}

async function cargarFilas(conLaboral: boolean): Promise<{ filas: FilaPersona[]; total: number }> {
  const [pagina, empleados] = await Promise.all([
    personasApi.listTodas(),
    conLaboral ? gestionApi.listEmpleados() : Promise.resolve([] as EmpleadoListItem[]),
  ]);
  const porId = new Map(empleados.map((e) => [e.id, e]));
  const filas = pagina.items.map((p) => ({ ...p, laboral: porId.get(p.id) ?? null }));
  return { filas, total: pagina.total };
}

export function usePersonas() {
  const { can } = useSession();
  const conLaboral = can("vacaciones", "view");
  const [filas, setFilas] = useState<FilaPersona[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [filtros, setFiltros] = useState<FiltrosPersonas>({
    busqueda: "", sectorId: "", acceso: "", estado: "",
  });
  const { sort, toggleSort } = useTableSort<PersonaSortKey>({
    initial: { key: "nombre", direction: "asc" },
    keys: SORT_KEYS,
    descFirstKeys: ["ingreso", "disponibles"],
  });

  const recargar = useCallback(() => {
    cargarFilas(conLaboral)
      .then((r) => {
        setFilas(r.filas);
        setTotal(r.total);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudieron cargar las personas.");
      });
  }, [conLaboral]);

  useEffect(() => {
    recargar();
  }, [recargar]);

  const visibles = useMemo(() => {
    const base = (filas ?? []).filter((f) => pasaFiltros(f, filtros));
    return base.sort((a, b) =>
      compareSortValues(valorOrden(a, sort.key), valorOrden(b, sort.key), sort.direction),
    );
  }, [filas, filtros, sort]);

  const sectores = useMemo(() => {
    const unicos = new Map((filas ?? []).map((f) => [f.sectorId, f.sectorNombre]));
    return [...unicos].sort((a, b) => a[1].localeCompare(b[1], "es"));
  }, [filas]);

  return {
    filas: visibles,
    cargando: filas === null && !error,
    incompleta: filas !== null && filas.length < total,
    error,
    recargar,
    filtros,
    setFiltros,
    sectores,
    conLaboral,
    sort,
    toggleSort,
  };
}
