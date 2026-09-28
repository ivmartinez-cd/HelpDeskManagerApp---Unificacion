"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Users } from "lucide-react";
import { SigesVinculoModal } from "@/features/vacaciones/components/siges-vinculo-modal";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { usePersonas } from "../hooks/use-personas";
import { NuevaPersonaModal } from "./nueva-persona-modal";
import { PersonasFiltros } from "./personas-filtros";
import { PersonasTabla } from "./personas-tabla";

export function PersonasView() {
  const { can } = useSession();
  // Alta de ficha y vínculo con Siges son del ABM de empleados (vacaciones.manage).
  const puedeGestionarFichas = can("vacaciones", "manage");
  const router = useRouter();
  const p = usePersonas();
  const [abrirAlta, setAbrirAlta] = useState(false);
  const [abrirSiges, setAbrirSiges] = useState(false);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Personas
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Todo el personal, con sus datos laborales y su acceso a la app
          </p>
        </div>
        {puedeGestionarFichas && (
          <div className="flex items-center gap-2">
            <BrandButton variant="outline" onClick={() => setAbrirSiges(true)}>
              Vincular con Siges
            </BrandButton>
            <BrandButton onClick={() => setAbrirAlta(true)}>
              <Plus className="h-4 w-4" />
              Nueva persona
            </BrandButton>
          </div>
        )}
      </div>

      <PersonasFiltros filtros={p.filtros} onChange={p.setFiltros} sectores={p.sectores} />

      {p.error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{p.error}</p>
          <BrandButton variant="outline" size="sm" onClick={p.recargar}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {p.cargando && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }, (_, i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!p.cargando && !p.error && (p.filas.length === 0 ? (
        <BrandEmptyState icon={Users} title="No se encontraron personas" description="Ajustá la búsqueda o los filtros." />
      ) : (
        <>
          <p className="-mb-3 font-body text-xs text-muted-foreground">
            {p.filas.length} persona{p.filas.length === 1 ? "" : "s"}
            {p.incompleta && " · la lista está cortada: hay más personas de las que entran en una carga"}
          </p>
          <PersonasTabla filas={p.filas} conLaboral={p.conLaboral} sort={p.sort} onToggleSort={p.toggleSort} />
        </>
      ))}

      {abrirAlta && (
        <NuevaPersonaModal
          onClose={() => setAbrirAlta(false)}
          onCreada={(id) => router.push(`/personas/${id}`)}
        />
      )}
      {abrirSiges && <SigesVinculoModal onClose={() => setAbrirSiges(false)} onChanged={p.recargar} />}
    </div>
  );
}
