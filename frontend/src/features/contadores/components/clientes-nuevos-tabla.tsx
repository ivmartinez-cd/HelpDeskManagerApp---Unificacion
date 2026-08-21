"use client";

import { useMemo } from "react";
import { Pencil, Trash2 } from "lucide-react";
import type { Operador } from "../types/calendario";
import type { ClienteNuevo } from "../types/clientes-nuevos";
import {
  ESTADO_META,
  RUBRO_LABEL,
  detalleInstalados,
  formatFecha,
  textoInstalados,
} from "../lib/clientes-nuevos";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { UserAvatar } from "@/shared/components/ui/user-avatar";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";

type SortKey = "cliente" | "operador" | "corte" | "fc" | "instalados" | "estado";
const SORT_KEYS: readonly SortKey[] = ["cliente", "operador", "corte", "fc", "instalados", "estado"];

interface ClientesNuevosTablaProps {
  rows: ClienteNuevo[];
  operadorMeta: Map<string, Operador>;
  canEdit: boolean;
  onEdit: (ficha: ClienteNuevo) => void;
  onDelete: (ficha: ClienteNuevo) => void;
}

const TH = "px-4 py-3 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";

function valorOrden(f: ClienteNuevo, key: SortKey, operadorMeta: Map<string, Operador>) {
  switch (key) {
    case "cliente":
      return f.cliente;
    case "operador":
      return f.operador_id ? (operadorMeta.get(f.operador_id)?.nombre ?? f.operador_id) : null;
    case "corte":
      return f.dia_corte;
    case "fc":
      return f.fecha_estimada_primera_facturacion;
    case "instalados":
      return f.siges?.equipos_instalados ?? null;
    case "estado":
      return f.estado;
  }
}

function ClienteCell({ f }: { f: ClienteNuevo }) {
  const rubro = f.siges?.rubro;
  const contrato = f.contrato_nro ?? f.siges?.contrato_nro;
  const firma = f.fecha_firma ?? f.siges?.fecha_firma;
  return (
    <div className="min-w-0 leading-tight">
      <div className="flex items-center gap-2">
        <p className="truncate font-body text-sm font-semibold text-foreground">{f.cliente}</p>
        {rubro && rubro !== "DESCONOCIDO" && (
          <BrandBadge variant={rubro === "IMPRESION" ? "accent" : "neutral"}>
            {RUBRO_LABEL[rubro] ?? rubro}
          </BrandBadge>
        )}
      </div>
      <p className="truncate font-body text-xs text-muted-foreground">
        {contrato ?? "Sin contrato"}
        {firma ? ` · firma ${formatFecha(firma)}` : ""}
        {f.implementacion_servicio ? ` · ${f.implementacion_servicio}` : ""}
      </p>
    </div>
  );
}

function OperadorCell({ id, meta }: { id: string | null; meta: Operador | undefined }) {
  if (!id) return <span className="font-body text-xs text-muted-foreground">Sin asignar</span>;
  const nombre = meta?.nombre ?? id;
  return (
    <div className="flex items-center gap-2.5">
      <UserAvatar fullName={nombre} color={meta?.color ?? null} size="sm" />
      <span className="truncate font-body text-sm text-foreground">{nombre}</span>
    </div>
  );
}

function InstaladosCell({ f }: { f: ClienteNuevo }) {
  return (
    <div className="flex flex-col gap-1 leading-tight">
      <span
        title={detalleInstalados(f) || undefined}
        className="font-body text-sm tabular-nums text-foreground"
      >
        {textoInstalados(f)}
      </span>
      {f.listo_para_stc && <BrandBadge variant="accent">Listo para STC</BrandBadge>}
    </div>
  );
}

function EstadoCell({ f }: { f: ClienteNuevo }) {
  const meta = ESTADO_META[f.estado];
  return (
    <div className="flex flex-col gap-1">
      <BrandBadge variant={meta.variant}>{meta.label}</BrandBadge>
      {f.estado === "STC_ENVIADO" && f.stc_enviado_el && (
        <span className="font-body text-xs text-muted-foreground">
          el {formatFecha(f.stc_enviado_el)}
        </span>
      )}
    </div>
  );
}

export function ClientesNuevosTabla({
  rows,
  operadorMeta,
  canEdit,
  onEdit,
  onDelete,
}: ClientesNuevosTablaProps) {
  const { sort, toggleSort } = useTableSort<SortKey>({
    initial: { key: "fc", direction: "asc" },
    keys: SORT_KEYS,
    storageKey: "contadores-clientes-nuevos-sort",
  });

  const ordenadas = useMemo(
    () =>
      [...rows].sort((a, b) =>
        compareSortValues(
          valorOrden(a, sort.key, operadorMeta),
          valorOrden(b, sort.key, operadorMeta),
          sort.direction,
        ),
      ),
    [rows, sort, operadorMeta],
  );

  const col = (key: SortKey, label: string) => (
    <SortableHeader column={{ key, label }} sort={sort} onToggleSort={toggleSort} thClassName={TH} />
  );

  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-border">
            {col("cliente", "Cliente")}
            {col("operador", "Operador")}
            <th className={TH}>Vendedor</th>
            {col("corte", "Corte")}
            {col("fc", "1ª facturación")}
            <th className={TH}>Impl. estimada</th>
            {col("instalados", "Instalados (Siges)")}
            {col("estado", "Estado")}
            {canEdit && <th className={TH} />}
          </tr>
        </thead>
        <tbody>
          {ordenadas.map((f) => (
            <tr key={f.id} className="border-b border-border align-middle last:border-b-0">
              <td className="max-w-[320px] px-4 py-3">
                <ClienteCell f={f} />
              </td>
              <td className="px-4 py-3">
                <OperadorCell
                  id={f.operador_id}
                  meta={f.operador_id ? operadorMeta.get(f.operador_id) : undefined}
                />
              </td>
              <td className="px-4 py-3 font-body text-sm text-foreground">{f.vendedor ?? "—"}</td>
              <td className="px-4 py-3 font-body text-sm tabular-nums text-foreground">
                {f.dia_corte ?? "A definir"}
              </td>
              <td className="px-4 py-3 font-body text-sm tabular-nums text-foreground">
                {formatFecha(f.fecha_estimada_primera_facturacion)}
              </td>
              <td className="px-4 py-3 font-body text-sm tabular-nums text-foreground">
                {formatFecha(f.fecha_estimada_implementacion)}
              </td>
              <td className="px-4 py-3">
                <InstaladosCell f={f} />
              </td>
              <td className="px-4 py-3">
                <EstadoCell f={f} />
              </td>
              {canEdit && (
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      type="button"
                      onClick={() => onEdit(f)}
                      aria-label={`Editar ficha de ${f.cliente}`}
                      className="rounded-[8px] p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(f)}
                      aria-label={`Borrar ficha de ${f.cliente}`}
                      className="rounded-[8px] p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
