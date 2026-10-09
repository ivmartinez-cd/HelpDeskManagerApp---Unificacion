"use client";

import Link from "next/link";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import { formatAntiguedad, formatFecha, iniciales } from "@/features/vacaciones/lib/fechas";
import { diasDelCiclo } from "@/features/vacaciones/lib/saldo";
import { nombrePersona } from "../api/personas-api";
import type { FilaPersona, PersonaSortKey } from "../hooks/use-personas";

const COLUMNAS: SortableColumn<PersonaSortKey>[] = [
  { key: "nombre", label: "Nombre" },
  { key: "sector", label: "Sector" },
  { key: "cargo", label: "Cargo" },
];
const COLUMNAS_LABORALES: SortableColumn<PersonaSortKey>[] = [
  { key: "ingreso", label: "Ingreso / Antigüedad" },
  { key: "disponibles", label: "Disponibles", title: "Días de vacaciones disponibles este año" },
];
const COLUMNAS_FINALES: SortableColumn<PersonaSortKey>[] = [
  { key: "acceso", label: "Entra a la app" },
  { key: "estado", label: "Estado" },
];

interface Props {
  filas: FilaPersona[];
  conLaboral: boolean;
  sort: SortState<PersonaSortKey>;
  onToggleSort: (key: PersonaSortKey) => void;
}

export function PersonasTabla({ filas, conLaboral, sort, onToggleSort }: Props) {
  const columnas = [...COLUMNAS, ...(conLaboral ? COLUMNAS_LABORALES : []), ...COLUMNAS_FINALES];
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border">
      <table className="w-full min-w-[860px] font-body text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
            {columnas.map((c) => (
              <SortableHeader key={c.key} column={c} sort={sort} onToggleSort={onToggleSort} />
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <FilaTabla key={f.id} fila={f} conLaboral={conLaboral} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FilaTabla({ fila: f, conLaboral }: { fila: FilaPersona; conLaboral: boolean }) {
  return (
    <tr className="border-b border-border/60 last:border-0 hover:bg-muted/30">
      <td className="px-4 py-3">
        <Link href={`/personas/${f.id}`} className="group flex items-center gap-2.5">
          <span
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] font-heading text-[11px] font-bold text-white"
            style={{ backgroundColor: f.color }}
          >
            {iniciales(nombrePersona(f))}
          </span>
          <span>
            <span className="block font-semibold text-foreground group-hover:text-brand-orange">
              {nombrePersona(f)}
            </span>
            <span className="block text-xs text-muted-foreground">{f.email}</span>
          </span>
        </Link>
      </td>
      <td className="px-4 py-3">
        <span
          className="inline-block rounded-[20px] px-2.5 py-1 text-xs font-semibold text-white"
          style={{ backgroundColor: f.laboral?.sectorColor ?? "var(--muted-foreground)" }}
        >
          {f.sectorNombre}
        </span>
      </td>
      <td className="px-4 py-3 text-foreground">{f.cargoNombre}</td>
      {conLaboral && <CeldasLaborales fila={f} />}
      <td className="px-4 py-3">
        <BrandBadge variant={f.entraALaApp ? "accent" : "neutral"}>
          {f.entraALaApp ? (f.acceso?.superadmin ? "Sí · Admin" : "Sí") : "No"}
        </BrandBadge>
      </td>
      <td className="px-4 py-3">
        <BrandBadge variant={f.activa ? "success" : "neutral"}>
          {f.activa ? "Activa" : "Inactiva"}
        </BrandBadge>
      </td>
    </tr>
  );
}

function CeldasLaborales({ fila }: { fila: FilaPersona }) {
  const l = fila.laboral;
  if (!l) {
    return (
      <>
        <td className="px-4 py-3 text-muted-foreground">—</td>
        <td className="px-4 py-3 text-muted-foreground">—</td>
      </>
    );
  }
  return (
    <>
      <td className="px-4 py-3">
        <div className="text-foreground">{formatFecha(l.hireDate)}</div>
        <div className="text-xs text-muted-foreground">{formatAntiguedad(l.antiguedadAnios)}</div>
      </td>
      <td className="px-4 py-3">
        <span className="font-heading font-bold text-brand-orange">{l.saldo.available}</span>
        <span className="text-muted-foreground">/{diasDelCiclo(l.saldo)}</span>
      </td>
    </>
  );
}
