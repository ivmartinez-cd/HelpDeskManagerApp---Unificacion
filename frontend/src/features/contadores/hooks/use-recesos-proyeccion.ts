import { useCallback, useEffect, useState } from "react";
import { mensajeError, proyeccionApi } from "../api/proyeccion-api";
import type { AnexoOption, GrupoEconomicoOption, Receso } from "../types/proyeccion";

/** Estado de la pantalla de recesos — `Recesos.razor` del Estimador v1.7:
 * grupos económicos al entrar, anexos del grupo elegido, validación al
 * guardar ("Elegí un grupo económico." / "Hasta" no anterior a "Desde") y
 * todo error visible. Descripción opcional. "Editar" carga el receso en el
 * formulario ("Editar receso #N" / "Guardar" / "Cancelar").
 *
 * Diferencia con el legacy, por el contrato actual del backend: la lista
 * muestra los recesos del grupo elegido (no los de todos los grupos). */

export interface FormReceso {
  idGrupo: string | null;
  idAnexo: string | null;
  desde: string;
  hasta: string;
  descripcion: string;
}

function hoy(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export const formVacio = (): FormReceso => ({ idGrupo: null, idAnexo: null, desde: hoy(), hasta: hoy(), descripcion: "" });

export function validarReceso(f: FormReceso): string | null {
  if (!f.idGrupo) return "Elegí un grupo económico.";
  if (!f.desde || !f.hasta) return "Completá las fechas 'Desde' y 'Hasta'.";
  if (f.hasta < f.desde) return "La fecha 'Hasta' no puede ser anterior a 'Desde'.";
  return null;
}

function useCatalogos(idGrupo: string | null, setError: (e: string) => void) {
  const [grupos, setGrupos] = useState<GrupoEconomicoOption[]>([]);
  const [anexos, setAnexos] = useState<AnexoOption[]>([]);
  useEffect(() => {
    proyeccionApi
      .listGruposEconomicos()
      .then(setGrupos)
      .catch((err) => setError(`No se pudieron cargar los grupos económicos: ${mensajeError(err, "error de conexión")}`));
  }, [setError]);
  useEffect(() => {
    if (!idGrupo) return;
    proyeccionApi
      .listAnexos(Number(idGrupo))
      .then(setAnexos)
      .catch((err) => setError(`No se pudieron cargar los anexos: ${mensajeError(err, "error de conexión")}`));
  }, [idGrupo, setError]);
  return { grupos, anexos: idGrupo ? anexos : [] };
}

function useListaRecesos(idGrupo: string | null, setError: (e: string) => void) {
  const [lista, setLista] = useState<Receso[] | null>(null);
  const recargar = useCallback(() => {
    if (!idGrupo) return;
    proyeccionApi
      .listRecesos(Number(idGrupo))
      .then(setLista)
      .catch((err) => setError(mensajeError(err, "No se pudieron leer los recesos.")));
  }, [idGrupo, setError]);
  useEffect(recargar, [recargar]);
  return { lista: idGrupo ? lista : null, recargar };
}

function formDe(r: Receso): FormReceso {
  return {
    idGrupo: String(r.id_grupo_economico),
    idAnexo: r.id_anexo === null ? null : String(r.id_anexo),
    desde: r.fecha_desde,
    hasta: r.fecha_hasta,
    descripcion: r.descripcion,
  };
}

function useEdicion(setForm: (f: FormReceso | ((f: FormReceso) => FormReceso)) => void, setError: (e: string | null) => void) {
  const [editId, setEditId] = useState<number | null>(null);
  const editar = (r: Receso) => {
    setEditId(r.id);
    setForm(formDe(r));
    setError(null);
  };
  // Se conserva el grupo elegido: la lista es la de ese grupo.
  const cancelar = () => {
    setEditId(null);
    setForm((f) => ({ ...formVacio(), idGrupo: f.idGrupo }));
    setError(null);
  };
  return { editId, editar, cancelar };
}

export function useRecesosProyeccion() {
  const [form, setForm] = useState<FormReceso>(formVacio);
  const [error, setErrorRaw] = useState<string | null>(null);
  const setError = useCallback((e: string | null) => setErrorRaw(e), []);
  const catalogos = useCatalogos(form.idGrupo, setError);
  const { lista, recargar } = useListaRecesos(form.idGrupo, setError);
  const edicion = useEdicion(setForm, setError);
  const guardar = async () => {
    const invalido = validarReceso(form);
    setError(invalido);
    if (invalido) return;
    const body = cuerpoReceso(form);
    try {
      await (edicion.editId === null ? proyeccionApi.crearReceso(body) : proyeccionApi.actualizarReceso(edicion.editId, body));
      edicion.cancelar();
      recargar();
    } catch (err) {
      setError(mensajeError(err, "No se pudo guardar el receso."));
    }
  };
  const eliminar = (id: number) =>
    proyeccionApi
      .eliminarReceso(id, Number(form.idGrupo))
      .then(() => {
        if (edicion.editId === id) edicion.cancelar();
        recargar();
      })
      .catch((err) => setError(mensajeError(err, "No se pudo eliminar el receso.")));
  return { ...catalogos, ...edicion, form, setForm, error, lista, guardar, eliminar };
}

function cuerpoReceso(f: FormReceso) {
  return {
    id_grupo_economico: Number(f.idGrupo),
    id_anexo: f.idAnexo ? Number(f.idAnexo) : null,
    fecha_desde: f.desde,
    fecha_hasta: f.hasta,
    descripcion: f.descripcion.trim(),
  };
}
