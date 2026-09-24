"use client";

import { useCallback } from "react";
import Link from "next/link";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import { useSession } from "@/services/session-provider";
import { useRecesosProyeccion } from "../hooks/use-recesos-proyeccion";
import type { AnexoOption, GrupoEconomicoOption, Receso } from "../types/proyeccion";
import { diasEntre, fechaLarga } from "./proyeccion-formato";

/** Calendario de recesos — `Recesos.razor` del Estimador v1.7. */

type Estado = ReturnType<typeof useRecesosProyeccion>;

// Sin permiso de gestión solo queda el grupo (para ver su lista).
function Formulario({ r, puedeGestionar }: { r: Estado; puedeGestionar: boolean }) {
  const { form, setForm } = r;
  return (
    <div className="flex flex-col gap-3 self-start rounded-[12px] border border-border bg-card p-5">
      {puedeGestionar && (
        <h2 className="font-heading text-sm font-bold">{r.editId === null ? "Nuevo receso" : `Editar receso #${r.editId}`}</h2>
      )}
      <SearchableSelect
        label="Grupo económico"
        placeholder="— Elegí un grupo —"
        options={r.grupos.map((g) => ({ id: String(g.id), label: g.descripcion }))}
        value={form.idGrupo}
        onChange={(id) => setForm((f) => ({ ...f, idGrupo: id, idAnexo: null }))}
      />
      {puedeGestionar && <CamposReceso r={r} />}
    </div>
  );
}

function CamposReceso({ r }: { r: Estado }) {
  const { form, setForm } = r;
  return (
    <>
      <SearchableSelect
        label="Anexo"
        placeholder="Todos los anexos del grupo"
        disabled={!form.idGrupo}
        options={r.anexos.map((a) => ({ id: String(a.id_anexo), label: a.nombre_anexo }))}
        value={form.idAnexo}
        onChange={(id) => setForm((f) => ({ ...f, idAnexo: id }))}
      />
      <div className="grid grid-cols-2 gap-3">
        <BrandInput label="Desde" type="date" value={form.desde} onChange={(e) => setForm((f) => ({ ...f, desde: e.target.value }))} />
        <BrandInput label="Hasta" type="date" value={form.hasta} onChange={(e) => setForm((f) => ({ ...f, hasta: e.target.value }))} />
      </div>
      <BrandInput
        label="Descripción"
        placeholder="Ej. Receso invierno 2026"
        value={form.descripcion}
        onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))}
      />
      <div className="flex gap-2">
        <BrandButton onClick={r.guardar}>{r.editId === null ? "Agregar" : "Guardar"}</BrandButton>
        {r.editId !== null && (
          <button onClick={r.cancelar} className="text-xs font-bold text-muted-foreground hover:underline">
            Cancelar
          </button>
        )}
      </div>
    </>
  );
}

interface ListaProps {
  lista: Receso[];
  grupos: GrupoEconomicoOption[];
  anexos: AnexoOption[];
  puedeGestionar: boolean;
  onEditar: (r: Receso) => void;
  onEliminar: (id: number) => void;
}

function nombreAnexo(r: Receso, anexos: AnexoOption[]): string {
  if (r.id_anexo === null) return "Todos";
  return anexos.find((a) => a.id_anexo === r.id_anexo)?.nombre_anexo ?? String(r.id_anexo);
}

type SortKey = "grupo" | "anexo" | "desde" | "hasta" | "dias" | "descripcion";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "grupo", label: "Grupo" },
  { key: "anexo", label: "Anexo" },
  { key: "desde", label: "Desde" },
  { key: "hasta", label: "Hasta" },
  { key: "dias", label: "Días", className: "text-right" },
  { key: "descripcion", label: "Descripción" },
];

const DESC_PRIMERO: readonly SortKey[] = ["dias"];

function nombreGrupo(r: Receso, grupos: GrupoEconomicoOption[]): string {
  return grupos.find((g) => g.id === r.id_grupo_economico)?.descripcion ?? String(r.id_grupo_economico);
}

function useRecesosOrdenados({ lista, grupos, anexos }: Pick<ListaProps, "lista" | "grupos" | "anexos">) {
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const valorOrden = useCallback(
    (r: Receso, key: SortKey) => {
      if (key === "grupo") return nombreGrupo(r, grupos);
      if (key === "anexo") return nombreAnexo(r, anexos);
      if (key === "dias") return diasEntre(r.fecha_desde, r.fecha_hasta);
      return key === "desde" ? r.fecha_desde : key === "hasta" ? r.fecha_hasta : r.descripcion;
    },
    [grupos, anexos],
  );
  return { sort, toggleSort, filas: useSortedRows(lista, sort, valorOrden) };
}

function ListaRecesos({ lista, grupos, anexos, puedeGestionar, onEditar, onEliminar }: ListaProps) {
  const { sort, toggleSort, filas } = useRecesosOrdenados({ lista, grupos, anexos });
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border text-[11px] font-bold uppercase text-muted-foreground">
            {COLUMNAS.map((c) => (
              <SortableHeader key={c.key} column={c} sort={sort} onToggleSort={toggleSort} thClassName="px-4 py-2.5" />
            ))}
            <th className="px-4 py-2.5 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {filas.map((r) => (
            <tr key={r.id}>
              <td className="px-4 py-3">{nombreGrupo(r, grupos)}</td>
              <td className="px-4 py-3">{nombreAnexo(r, anexos)}</td>
              <td className="px-4 py-3">{fechaLarga(r.fecha_desde)}</td>
              <td className="px-4 py-3">{fechaLarga(r.fecha_hasta)}</td>
              <td className="px-4 py-3 text-right tabular-nums">{diasEntre(r.fecha_desde, r.fecha_hasta) + 1}</td>
              <td className="px-4 py-3">{r.descripcion}</td>
              <td className="px-4 py-3 text-right">
                {puedeGestionar && (
                  <div className="flex justify-end gap-3">
                    <button onClick={() => onEditar(r)} className="text-xs font-bold text-foreground hover:underline">
                      Editar
                    </button>
                    <button onClick={() => onEliminar(r.id)} className="text-xs font-bold text-destructive hover:underline">
                      Eliminar
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Lista({ r, puedeGestionar }: { r: Estado; puedeGestionar: boolean }) {
  if (!r.form.idGrupo) return <p className="text-sm text-muted-foreground">Elegí un grupo económico para ver sus recesos.</p>;
  if (!r.lista) return <p className="text-sm text-muted-foreground">Cargando…</p>;
  if (r.lista.length === 0) return <p className="text-sm text-muted-foreground">No hay recesos cargados todavía.</p>;
  return (
    <ListaRecesos
      lista={r.lista}
      grupos={r.grupos}
      anexos={r.anexos}
      puedeGestionar={puedeGestionar}
      onEditar={r.editar}
      onEliminar={r.eliminar}
    />
  );
}

export function ProyeccionRecesosView() {
  const { can } = useSession();
  const puedeGestionar = can("contadores", "manage");
  const r = useRecesosProyeccion();

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contadores" className="hover:text-foreground">Centro de Contadores</Link>
        <span>›</span>
        <Link href="/contadores/proyeccion" className="hover:text-foreground">Estimador de contadores</Link>
        <span>›</span>
        <span className="font-semibold text-foreground">Recesos</span>
      </div>

      <div>
        <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
          Calendario de recesos
        </h1>
        <p className="mt-1 max-w-3xl font-body text-sm text-muted-foreground">
          Períodos sin uso del cliente (recesos escolares de invierno/verano, etc.). Se descuentan de la
          estimación: no diluyen la tasa diaria ni se facturan como impresiones. Elegí el <strong>grupo
          económico</strong> y, opcionalmente, un <strong>anexo</strong> puntual (vacío = todos los anexos del grupo).
        </p>
      </div>

      {r.error && <div className="rounded-[8px] bg-destructive/10 px-4 py-3 text-sm text-destructive">{r.error}</div>}

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <Formulario r={r} puedeGestionar={puedeGestionar} />
        <Lista r={r} puedeGestionar={puedeGestionar} />
      </div>
    </div>
  );
}
