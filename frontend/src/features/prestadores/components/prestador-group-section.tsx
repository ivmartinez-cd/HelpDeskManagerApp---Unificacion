"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { OperadorGroup, Prestador } from "../types/prestadores";
import { cn } from "@/shared/utils/cn";
import { BrandBadge, brandButtonClasses } from "@/shared/components/ui/brand-form";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { UserAvatar } from "@/shared/components/ui/user-avatar";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";

type SortKey = "razonSocial" | "parque" | "telefono" | "nombre" | "correo";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "razonSocial", label: "Razón social" },
  { key: "parque", label: "Parque de impresoras" },
  { key: "telefono", label: "Tel. contacto" },
  { key: "nombre", label: "Nombre" },
  { key: "correo", label: "Correo" },
];

/** Parque: el primer clic pone arriba al de más equipos. */
const DESC_PRIMERO: readonly SortKey[] = ["parque"];

/** Contacto que muestra la fila: el principal, o el primero si no hay. */
const contactoPrincipal = (p: Prestador) => p.contactos.find((c) => c.isPrincipal) ?? p.contactos[0];

function valorOrden(p: Prestador, key: SortKey) {
  const principal = contactoPrincipal(p);
  switch (key) {
    case "razonSocial": return p.denComercial;
    case "parque": return p.equipos;
    case "telefono": return principal?.telefono;
    case "nombre": return principal?.nombre;
    case "correo": return principal?.email;
  }
}

interface PrestadorGroupSectionProps {
  grupo: OperadorGroup;
  onVer: (prestadorId: string) => void;
}

export function PrestadorGroupSection({ grupo, onVer }: PrestadorGroupSectionProps) {
  const [expanded, setExpanded] = useState(false);
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const filas = useSortedRows(grupo.prestadores, sort, valorOrden);
  const activos = grupo.prestadores.filter((p) => p.isActive).length;

  return (
    <div className="rounded-[12px] border border-border bg-card">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3"
      >
        <div className="flex items-center gap-2.5">
          <ChevronDown
            className={cn("h-4 w-4 text-muted-foreground transition-transform", !expanded && "-rotate-90")}
          />
          {grupo.operadorId ? (
            <UserAvatar fullName={grupo.operadorNombre ?? "?"} color={grupo.operadorColor} size="sm" />
          ) : null}
          <span className="font-heading text-sm font-bold text-foreground">
            {grupo.operadorNombre ?? "Sin asignar"}
          </span>
          <span className="font-body text-xs text-muted-foreground">
            {grupo.prestadores.length} prestador{grupo.prestadores.length !== 1 ? "es" : ""}
          </span>
        </div>
        <BrandBadge variant={activos > 0 ? "accent" : "neutral"}>{activos} activos</BrandBadge>
      </button>

      {expanded && (
        <div className="overflow-x-auto border-t border-border">
          <table className="w-full min-w-[640px] text-left">
            <thead>
              <tr className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                {COLUMNAS.map((c) => (
                  <SortableHeader
                    key={c.key}
                    column={c}
                    sort={sort}
                    onToggleSort={toggleSort}
                    thClassName="px-4 py-2.5"
                  />
                ))}
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filas.map((p) => {
                const principal = contactoPrincipal(p);
                return (
                  <tr key={p.id} className="font-body text-sm">
                    <td className="px-4 py-2.5">
                      <p className="font-semibold text-foreground">{p.denComercial}</p>
                      {!p.isActive && (
                        <span className="font-body text-[10px] font-bold uppercase text-muted-foreground">
                          inactivo
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {p.equipos ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {principal?.telefono ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {principal?.nombre ?? "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      {principal?.email ? (
                        <a
                          href={`mailto:${principal.email}`}
                          className="text-brand-orange hover:underline"
                        >
                          {principal.email}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        type="button"
                        onClick={() => onVer(p.id)}
                        className={brandButtonClasses({ variant: "outline", size: "sm" })}
                      >
                        Ver
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
