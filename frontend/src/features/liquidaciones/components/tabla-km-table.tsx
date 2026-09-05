"use client";

import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import type { Spst, TablaKm } from "../types/liquidaciones";

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
const warnBadgeCls = "inline-flex items-center rounded-full bg-warning/10 px-2 py-0.5 font-body text-[10px] font-bold uppercase tracking-wide text-warning hover:bg-warning/20";

/** Hace visible en un solo lugar la cadena que hoy está repartida en 2
 * pantallas (Tabla KM → SPST → Tarifario): sin esto, saber por qué un
 * incidente no tiene precio obliga a saltar entre pantallas adivinando. */
function CeldaSpst({
  fila,
  spstsPorId,
  spstsConTarifa,
  onEdit,
}: {
  fila: TablaKm;
  spstsPorId: Map<string, Spst>;
  spstsConTarifa: Set<string | null>;
  onEdit: (t: TablaKm) => void;
}) {
  if (!fila.spstId) {
    return (
      <button type="button" onClick={() => onEdit(fila)} className={warnBadgeCls} title="Sin esto no se puede resolver ninguna tarifa — clic para vincular">
        Sin SPST
      </button>
    );
  }
  const spst = spstsPorId.get(fila.spstId);
  if (!spst) {
    return <span className="font-body text-xs text-muted-foreground">SPST no encontrado</span>;
  }
  const sinTarifa = !spstsConTarifa.has(fila.spstId);
  return (
    <div className="flex flex-col gap-0.5">
      <span className="truncate font-body text-sm text-foreground" title={spst.nombre}>{spst.nombre}</span>
      <span className="flex items-center gap-1.5">
        {spst.zonaCobertura && (
          <span className="truncate font-body text-xs text-muted-foreground" title={spst.zonaCobertura}>
            {spst.zonaCobertura}
          </span>
        )}
        {sinTarifa && (
          <button type="button" onClick={() => onEdit(fila)} className={warnBadgeCls} title="Este SPST no tiene ninguna tarifa cargada — el incidente va a quedar sin precio">
            Sin tarifario
          </button>
        )}
      </span>
    </div>
  );
}

/** Tabla de entradas de Tabla KM (con agrupación visual por empresa cuando el
 * sort es por empresa), extraída de `tabla-km-config.tsx` porque ese archivo
 * ya superaba el tamaño máximo de archivo (§4). */
export function TablaKmTable({
  filtered,
  sort,
  toggleSort,
  puedeEditar,
  spstsPorId,
  spstsConTarifa,
  onEdit,
  onDelete,
  onArchivar,
}: {
  filtered: TablaKm[];
  sort: SortState<KmSortKey>;
  toggleSort: (key: KmSortKey) => void;
  puedeEditar: boolean;
  /** SPST del prestador seleccionado, por id — para mostrar el SPST resuelto
   * de cada fila sin obligar a saltar a la pantalla de SPSTs. */
  spstsPorId: Map<string, Spst>;
  /** Ids de SPST (o `null` = genérica) con al menos un tarifario cargado para
   * este prestador — permite avisar "sin tarifario" en el momento, no semanas
   * después cuando aparece como alerta en una liquidación. */
  spstsConTarifa: Set<string | null>;
  onEdit: (t: TablaKm) => void;
  onDelete: (id: string) => void;
  /** Archivar = ocultar una fila sin actividad reciente; el motor la sigue usando. */
  onArchivar?: (t: TablaKm) => void;
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
            <col className="w-[17%]" />
            <col className="w-[26%]" />
            <col className="w-[21%]" />
            <col className="w-[9%]" />
            <col className="w-[9%]" />
            <col className="w-[7%]" />
            <col className="w-[11%]" />
          </colgroup>
          <thead>
            <tr className="bg-muted/40">
              <SortableHeader column={{ key: "empresa", label: "Empresa" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "sucursal", label: "Sucursal" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <th className={thCls} title="Determina qué tarifa se le cobra al incidente: SPST → tarifario">SPST → Tarifa</th>
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
                  className={`transition-colors hover:bg-muted/30 ${firstOfGroup ? "border-t border-border" : "border-t border-transparent"} ${t.archivada ? "opacity-60" : ""}`}
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
                  <td className={tdCls}>
                    <CeldaSpst fila={t} spstsPorId={spstsPorId} spstsConTarifa={spstsConTarifa} onEdit={onEdit} />
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
                        {onArchivar && (
                          <button onClick={() => onArchivar(t)} className="mr-3 font-body text-sm text-muted-foreground hover:underline" title={t.archivada ? "Volver a mostrar esta fila" : "Ocultar esta fila sin borrarla (el motor la sigue usando)"}>
                            {t.archivada ? "Restaurar" : "Archivar"}
                          </button>
                        )}
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
