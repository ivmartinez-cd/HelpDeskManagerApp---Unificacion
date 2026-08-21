"use client";

import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import type { TablaKm } from "../types/liquidaciones";

export type KmSortKey = "empresa" | "sucursal" | "kmsRec" | "kmsFact";
export const KM_SORT_KEYS: readonly KmSortKey[] = ["empresa", "sucursal", "kmsRec", "kmsFact"];

export function kmSortValue(t: TablaKm, key: KmSortKey) {
  switch (key) {
    case "empresa": return t.empresaNombre;
    case "sucursal": return t.sucursalNombre;
    case "kmsRec": return t.kmsRecorrido;
    case "kmsFact": return t.kmsAFacturar;
  }
}

const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-2 px-4 font-body text-sm text-foreground";

/** Tabla de entradas de Tabla KM (con agrupación visual por empresa cuando el
 * sort es por empresa), extraída de `tabla-km-config.tsx` porque ese archivo
 * ya superaba el tamaño máximo de archivo (§4). */
export function TablaKmTable({
  filtered,
  sort,
  toggleSort,
  puedeEditar,
  onEdit,
  onDelete,
}: {
  filtered: TablaKm[];
  sort: SortState<KmSortKey>;
  toggleSort: (key: KmSortKey) => void;
  puedeEditar: boolean;
  onEdit: (t: TablaKm) => void;
  onDelete: (id: string) => void;
}) {
  // Para agrupar visualmente por empresa cuando el sort es por empresa
  const groupByEmpresa = sort.key === "empresa";
  function isFirstOfGroup(idx: number) {
    if (!groupByEmpresa) return true;
    return idx === 0 || filtered[idx - 1].empresaNombre !== filtered[idx].empresaNombre;
  }

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full table-fixed">
          <colgroup>
            <col className="w-[22%]" />
            <col className="w-[38%]" />
            <col className="w-[10%]" />
            <col className="w-[10%]" />
            <col className="w-[8%]" />
            <col className="w-[12%]" />
          </colgroup>
          <thead>
            <tr className="bg-muted/40">
              <SortableHeader column={{ key: "empresa", label: "Empresa" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "sucursal", label: "Sucursal" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "kmsRec", label: "KMs rec." }} sort={sort} onToggleSort={toggleSort} thClassName={`${thCls} text-right`} />
              <SortableHeader column={{ key: "kmsFact", label: "KMs fact." }} sort={sort} onToggleSort={toggleSort} thClassName={`${thCls} text-right`} />
              <th className={`${thCls} text-center`}>Viático</th>
              <th className={`${thCls} text-right`}></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t, i) => {
              const firstOfGroup = isFirstOfGroup(i);
              const lastOfGroup = !groupByEmpresa || i === filtered.length - 1 || filtered[i + 1].empresaNombre !== t.empresaNombre;
              return (
                <tr
                  key={t.id}
                  className={`transition-colors hover:bg-muted/30 ${firstOfGroup ? "border-t border-border" : "border-t border-transparent"}`}
                >
                  <td className={`${tdCls} ${!firstOfGroup ? "text-transparent select-none" : ""}`}>
                    <span className={`block truncate ${firstOfGroup && lastOfGroup === false ? "font-semibold" : ""}`} title={t.empresaNombre}>
                      {firstOfGroup ? t.empresaNombre : "·"}
                    </span>
                  </td>
                  <td className={tdCls}>
                    <div className="flex items-center gap-2">
                      <span className="truncate" title={t.sucursalNombre}>{t.sucursalNombre}</span>
                      {t.urlMaps && (
                        <a href={t.urlMaps} target="_blank" rel="noopener noreferrer" className="shrink-0 text-muted-foreground hover:text-brand-orange" title="Ver en Maps">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                        </a>
                      )}
                    </div>
                  </td>
                  <td className={`${tdCls} text-right tabular-nums text-muted-foreground`}>
                    {t.kmsRecorrido > 0 ? Math.round(t.kmsRecorrido) : "—"}
                  </td>
                  <td className={`${tdCls} text-right tabular-nums`}>
                    {t.kmsAFacturar > 0 ? Math.ceil(t.kmsAFacturar) : "—"}
                  </td>
                  <td className={`${tdCls} text-center`}>
                    {t.aplicaViatico
                      ? <span className="inline-block rounded-full bg-success/10 px-2 py-0.5 font-body text-[10px] font-bold uppercase tracking-wide text-success">Sí</span>
                      : <span className="inline-block rounded-full bg-muted px-2 py-0.5 font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">No</span>}
                  </td>
                  <td className={`${tdCls} text-right`}>
                    {puedeEditar && (
                      <>
                        <button onClick={() => onEdit(t)} className="mr-3 font-body text-sm text-brand-orange hover:underline">Editar</button>
                        <button onClick={() => onDelete(t.id)} className="font-body text-sm text-destructive hover:underline">Eliminar</button>
                      </>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
