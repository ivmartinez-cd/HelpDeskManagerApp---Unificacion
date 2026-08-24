"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { Plus } from "lucide-react";
import { gestionApi } from "../api/gestion-api";
import type {
  Cargo,
  EmpleadoListItem,
  Feriado,
  Sector,
  UsuarioOption,
} from "../types/vacaciones";
import { CargosTab } from "./cargos-tab";
import { EmpleadosTab } from "./empleados-tab";
import { FeriadosTab } from "./feriados-tab";
import { SectoresTab } from "./sectores-tab";
import { SigesVinculoModal } from "./siges-vinculo-modal";

type Tab = "empleados" | "sectores" | "cargos" | "feriados";
const TAB_VALUES: readonly Tab[] = ["empleados", "sectores", "cargos", "feriados"];

const TABS: { value: Tab; label: string }[] = [
  { value: "empleados", label: "Empleados" },
  { value: "sectores", label: "Sectores" },
  { value: "cargos", label: "Cargos" },
  { value: "feriados", label: "Feriados" },
];

function tabDesdeQuery(raw: string | null): Tab {
  return (TAB_VALUES as readonly string[]).includes(raw ?? "") ? (raw as Tab) : "empleados";
}

const NUEVO_LABEL: Record<Tab, string> = {
  empleados: "Nuevo empleado",
  sectores: "Nuevo sector",
  cargos: "Nuevo cargo",
  feriados: "Nuevo feriado",
};

export function GestionView() {
  const { user, can } = useSession();
  const puedeGestionar = user.isSuperadmin || can("vacaciones", "manage");
  const router = useRouter();
  const searchParams = useSearchParams();
  // El tab es derivado de la URL (?tab=…), no estado propio — así el
  // sidebar puede linkear directo a cada pestaña. Antes solo existía
  // "Personal" con Empleados por default, y Sectores/Cargos/Feriados
  // quedaban a 2 clics sin acceso directo.
  const tab = tabDesdeQuery(searchParams.get("tab"));
  const setTab = useCallback(
    (next: Tab) => {
      router.replace(next === "empleados" ? "/vacaciones/gestion" : `/vacaciones/gestion?tab=${next}`);
    },
    [router],
  );
  const [empleados, setEmpleados] = useState<EmpleadoListItem[] | null>(null);
  const [sectores, setSectores] = useState<Sector[] | null>(null);
  const [cargos, setCargos] = useState<Cargo[] | null>(null);
  const [feriados, setFeriados] = useState<Feriado[] | null>(null);
  const [usuarios, setUsuarios] = useState<UsuarioOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [abrirAlta, setAbrirAlta] = useState(false);
  const [abrirSigesVinculo, setAbrirSigesVinculo] = useState(false);

  const load = useCallback(() => {
    const base = Promise.all([
      gestionApi.listEmpleados(),
      gestionApi.listSectores(),
      gestionApi.listCargos(),
      gestionApi.listFeriados(),
    ]);
    const conUsuarios = puedeGestionar
      ? Promise.all([base, gestionApi.listUsuarios()])
      : Promise.all([base, Promise.resolve([] as UsuarioOption[])]);
    return conUsuarios
      .then(([[emps, secs, cars, fers], users]) => {
        setEmpleados(emps);
        setSectores(secs);
        setCargos(cars);
        setFeriados(fers);
        setUsuarios(users);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar Gestión Humana:", err);
        setError("No se pudieron cargar los datos. Intentá de nuevo.");
      });
  }, [puedeGestionar]);

  useEffect(() => {
    void load();
  }, [load]);

  const cargando = empleados === null && !error;

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Personal
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Empleados, sectores, cargos y feriados
          </p>
        </div>
        {puedeGestionar && (
          <div className="flex items-center gap-2">
            {tab === "empleados" && (
              <BrandButton variant="outline" onClick={() => setAbrirSigesVinculo(true)}>
                Vincular con Siges
              </BrandButton>
            )}
            <BrandButton onClick={() => setAbrirAlta(true)}>
              <Plus className="h-4 w-4" />
              {NUEVO_LABEL[tab]}
            </BrandButton>
          </div>
        )}
      </div>

      <div className="flex gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setTab(t.value)}
            className={
              tab === t.value
                ? "border-b-2 border-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-brand-orange"
                : "border-b-2 border-transparent px-4 py-2.5 font-body text-sm text-muted-foreground hover:text-foreground"
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {cargando && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }, (_, i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!cargando && !error && (
        <>
          {tab === "empleados" && (
            <EmpleadosTab
              empleados={empleados ?? []}
              sectores={sectores ?? []}
              cargos={cargos ?? []}
              usuarios={usuarios}
              puedeGestionar={puedeGestionar}
              abrirAlta={abrirAlta}
              onCerrarAlta={() => setAbrirAlta(false)}
              onChanged={() => void load()}
            />
          )}
          {tab === "sectores" && (
            <SectoresTab
              sectores={sectores ?? []}
              usuarios={usuarios}
              puedeGestionar={puedeGestionar}
              abrirAlta={abrirAlta}
              onCerrarAlta={() => setAbrirAlta(false)}
              onChanged={() => void load()}
            />
          )}
          {tab === "cargos" && (
            <CargosTab
              cargos={cargos ?? []}
              puedeGestionar={puedeGestionar}
              abrirAlta={abrirAlta}
              onCerrarAlta={() => setAbrirAlta(false)}
              onChanged={() => void load()}
            />
          )}
          {tab === "feriados" && (
            <FeriadosTab
              feriados={feriados ?? []}
              puedeGestionar={puedeGestionar}
              abrirAlta={abrirAlta}
              onCerrarAlta={() => setAbrirAlta(false)}
              onChanged={() => void load()}
            />
          )}
        </>
      )}

      {abrirSigesVinculo && (
        <SigesVinculoModal
          onClose={() => setAbrirSigesVinculo(false)}
          onChanged={() => void load()}
        />
      )}
    </div>
  );
}
