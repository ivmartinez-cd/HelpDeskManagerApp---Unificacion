"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { iniciales } from "@/features/vacaciones/lib/fechas";
import { BrandBadge, BrandButton, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { nombrePersona } from "../../api/personas-api";
import { useFichaPersona, type PestanaFicha } from "../../hooks/use-ficha-persona";
import { AccesoTab } from "./acceso-tab";
import { DatosTab } from "./datos-tab";
import { LaboralTab } from "./laboral-tab";

export function FichaPersonaView({ id }: { id: string }) {
  const { persona, setPersona, laboral, error, recargar, pestanas } = useFichaPersona(id);
  const [pestana, setPestana] = useState<PestanaFicha>("datos");

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <Link
        href="/personas"
        className="inline-flex w-fit items-center gap-1.5 font-body text-xs font-bold uppercase tracking-wide text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Personas
      </Link>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={recargar}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {!persona && !error && <BrandSkeleton className="h-16 w-full max-w-[560px]" />}

      {persona && (
        <>
          <div className="flex items-center gap-4">
            <span
              className="flex h-14 w-14 shrink-0 items-center justify-center rounded-[12px] font-heading text-lg font-bold text-white"
              style={{ backgroundColor: persona.color }}
            >
              {iniciales(nombrePersona(persona))}
            </span>
            <div className="flex flex-col gap-1">
              <h1 className="font-heading text-[25px] font-extrabold tracking-[-.03em] text-foreground">
                {nombrePersona(persona)}
              </h1>
              <div className="flex flex-wrap items-center gap-2 font-body text-sm text-muted-foreground">
                <span>{persona.cargoNombre} · {persona.sectorNombre}</span>
                <BrandBadge variant={persona.activa ? "success" : "neutral"}>
                  {persona.activa ? "Activa" : "Inactiva"}
                </BrandBadge>
                {persona.entraALaApp && <BrandBadge variant="accent">Entra a la app</BrandBadge>}
              </div>
            </div>
          </div>

          <div className="flex gap-1 border-b border-border">
            {pestanas.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setPestana(t.value)}
                className={
                  pestana === t.value
                    ? "border-b-2 border-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-brand-orange"
                    : "border-b-2 border-transparent px-4 py-2.5 font-body text-sm text-muted-foreground hover:text-foreground"
                }
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* `key` remonta el formulario con los valores nuevos después de guardar. */}
          {pestana === "datos" && (
            <DatosTab key={JSON.stringify(persona)} persona={persona} onGuardada={(p) => { setPersona(p); recargar(); }} />
          )}
          {pestana === "laboral" && laboral && (
            <LaboralTab
              key={JSON.stringify(laboral)}
              laboral={laboral}
              entraALaApp={persona.entraALaApp}
              onGuardada={recargar}
            />
          )}
          {pestana === "acceso" && <AccesoTab persona={persona} onCambio={setPersona} />}
        </>
      )}
    </div>
  );
}
