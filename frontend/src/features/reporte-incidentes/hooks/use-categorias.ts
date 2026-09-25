"use client";

import { useCallback, useEffect, useState } from "react";
import { reporteIncidentesApi } from "../api/reporte-incidentes-api";
import type { CategoriaDetalle } from "../types/reporte";

export const COLOR_INICIAL = "#0275d8";
export const COLOR_HEX = /^#[0-9a-fA-F]{6}$/;

export const CATEGORIA_VACIA: CategoriaDetalle = {
  nombre: "",
  color: COLOR_INICIAL,
  descripcion: "",
  subcategorias: [],
};

/** Qué se está editando: `null` = nada; `nombreAnterior: ""` = alta nueva.
 * `serie` cambia con cada apertura del formulario (sirve de `key`). */
export interface Edicion {
  nombreAnterior: string;
  datos: CategoriaDetalle;
  serie: number;
}

function mensajeDe(err: unknown, porDefecto: string): string {
  return err instanceof Error && err.message ? err.message : porDefecto;
}

/** Valida el formulario antes de mandarlo; `null` = válido. */
export function validarCategoria(datos: CategoriaDetalle): string | null {
  if (!datos.nombre.trim()) return "El nombre de la categoría es obligatorio.";
  if (!COLOR_HEX.test(datos.color)) return "El color tiene que tener el formato #rrggbb.";
  if (!datos.descripcion.trim()) return "La pauta para la IA es obligatoria.";
  return null;
}

/** Estado del modal de categorías (port de `ConfigModal`, sin la bandeja de
 * sugerencias). `onCambio` corre tras cada alta, edición o baja exitosa. */
export function useCategorias(onCambio: () => void) {
  const [categorias, setCategorias] = useState<CategoriaDetalle[]>([]);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(null);
  const [edicion, setEdicion] = useState<Edicion | null>(null);
  const [aEliminar, setAEliminar] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    try {
      const page = await reporteIncidentesApi.listCategorias();
      setCategorias(page.items);
    } catch (err: unknown) {
      console.error("Error al cargar las categorías:", err);
      setError(mensajeDe(err, "No se pudieron cargar las categorías."));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    queueMicrotask(() => void cargar());
  }, [cargar]);

  const limpiarAvisos = () => {
    setError(null);
    setExito(null);
  };

  const editar = (datos: CategoriaDetalle, nombreAnterior: string) => {
    limpiarAvisos();
    setAEliminar(null);
    setEdicion((prev) => ({
      nombreAnterior,
      datos: { ...datos, subcategorias: [...datos.subcategorias] },
      serie: (prev?.serie ?? 0) + 1,
    }));
  };

  const guardar = async (datos: CategoriaDetalle) => {
    limpiarAvisos();
    const invalido = validarCategoria(datos);
    if (invalido) return setError(invalido);
    const limpio = { ...datos, nombre: datos.nombre.trim(), descripcion: datos.descripcion.trim() };
    setGuardando(true);
    try {
      if (edicion?.nombreAnterior) await reporteIncidentesApi.editarCategoria(edicion.nombreAnterior, limpio);
      else await reporteIncidentesApi.crearCategoria(limpio);
      setEdicion((prev) => ({ nombreAnterior: limpio.nombre, datos: limpio, serie: prev?.serie ?? 0 }));
      setExito("Categoría guardada. La IA usa la taxonomía nueva desde la próxima tipificación.");
      await cargar();
      onCambio();
    } catch (err: unknown) {
      setError(mensajeDe(err, "No se pudo guardar la categoría."));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async () => {
    if (!aEliminar) return;
    limpiarAvisos();
    setGuardando(true);
    try {
      await reporteIncidentesApi.eliminarCategoria(aEliminar);
      if (edicion?.nombreAnterior.toLowerCase() === aEliminar.toLowerCase()) setEdicion(null);
      setExito(`Categoría "${aEliminar}" eliminada.`);
      setAEliminar(null);
      await cargar();
      onCambio();
    } catch (err: unknown) {
      setError(mensajeDe(err, "No se pudo eliminar la categoría."));
    } finally {
      setGuardando(false);
    }
  };

  return {
    categorias,
    cargando,
    guardando,
    error,
    exito,
    edicion,
    aEliminar,
    nueva: () => editar(CATEGORIA_VACIA, ""),
    editar: (c: CategoriaDetalle) => editar(c, c.nombre),
    cancelar: () => {
      limpiarAvisos();
      setEdicion(null);
      setAEliminar(null);
    },
    guardar,
    pedirEliminar: (nombre: string) => {
      limpiarAvisos();
      setAEliminar(nombre);
    },
    cancelarEliminar: () => setAEliminar(null),
    eliminar,
  };
}

export type EstadoCategorias = ReturnType<typeof useCategorias>;
