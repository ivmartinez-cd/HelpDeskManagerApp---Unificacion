"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { asistenciasApi } from "../api/asistencias-api";
import { gestionApi } from "../api/gestion-api";
import type { Ausencia, EmpleadoListItem, Feriado } from "../types/vacaciones";
import { AsistenciasCalendario } from "./asistencias-calendario";
import { AsistenciasDescuentos } from "./asistencias-descuentos";
import { AsistenciasListado } from "./asistencias-listado";
import { AusenciaModal } from "./ausencia-modal";
import { MisNovedades } from "./mis-novedades";

type Tab = "calendario" | "listado" | "reportes" | "novedades";

/** Pestañas del registro (calendario/listado/reportes): piden la función
 * `vacaciones-asistencias`. "Home office y horario" (las solicitudes
 * propias, antes en Mis Solicitudes) se abre con `create`, así un operador
 * entra a pedir home office sin ver el registro del equipo. */
const TABS_REGISTRO: { value: Tab; label: string }[] = [
  { value: "calendario", label: "Calendario" },
  { value: "listado", label: "Listado y registros" },
  { value: "reportes", label: "Reportes descuentos" },
];
const TAB_NOVEDADES: { value: Tab; label: string } = {
  value: "novedades",
  label: "Home office y horario",
};

export function AsistenciasView() {
  const { user, can, hasFeature } = useSession();
  const esAdmin = user.isSuperadmin || can("vacaciones", "manage");
  // Paridad legacy: el botón "Registrar baja" es de admin/jefe (el backend
  // igualmente restringe al empleado a registrar solo lo propio).
  const puedeRegistrar = esAdmin || can("vacaciones", "approve");
  const veRegistro = hasFeature("vacaciones-asistencias");
  const puedeSolicitar = esAdmin || can("vacaciones", "create");
  const tabs = [...(veRegistro ? TABS_REGISTRO : []), ...(puedeSolicitar ? [TAB_NOVEDADES] : [])];

  const [tab, setTab] = useState<Tab>(veRegistro ? "calendario" : "novedades");
  const [ausencias, setAusencias] = useState<Ausencia[] | null>(null);
  const [empleados, setEmpleados] = useState<EmpleadoListItem[]>([]);
  const [feriados, setFeriados] = useState<Feriado[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [editando, setEditando] = useState<Ausencia | null>(null);

  const load = useCallback(() => {
    return Promise.all([
      asistenciasApi.list(),
      gestionApi.listEmpleados(),
      gestionApi.listFeriados(),
    ])
      .then(([aus, emps, fers]) => {
        setAusencias(aus);
        setEmpleados(emps.filter((e) => e.status === "ACTIVE"));
        setFeriados(fers);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar Asistencias:", err);
        setError("No se pudieron cargar los datos. Intentá de nuevo.");
      });
  }, []);

  useEffect(() => {
    // Sin la función, el registro no se carga (empleados/feriados devolverían 403).
    if (veRegistro) void load();
  }, [load, veRegistro]);

  const feriadosSet = useMemo(
    () => new Set(feriados.map((f) => f.date.slice(0, 10))),
    [feriados],
  );

  const enRegistro = tab !== "novedades";
  const cargando = enRegistro && ausencias === null && !error;

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Asistencias
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Registro de bajas, ausentismo, home office y cambios de horario
          </p>
        </div>
        {puedeRegistrar && enRegistro && (
          <BrandButton onClick={() => setModalAbierto(true)}>
            <Plus className="h-4 w-4" />
            Registrar baja
          </BrandButton>
        )}
      </div>

      <div className="flex gap-1 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => {
              // Al volver de las novedades al registro, refrescar: una
              // solicitud creada/cancelada ahí aparece en el listado.
              if (tab === "novedades" && t.value !== "novedades" && veRegistro) void load();
              setTab(t.value);
            }}
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

      {tab === "novedades" && <MisNovedades />}

      {enRegistro && error && (
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

      {enRegistro && !cargando && !error && (
        <>
          {tab === "calendario" && (
            <AsistenciasCalendario
              // Solo lo aprobado pinta el calendario; las PENDING/REJECTED
              // (pedidos de home office / cambio de horario) se ven en el listado.
              ausencias={(ausencias ?? []).filter((a) => a.status === "APPROVED")}
              empleados={empleados}
              feriados={feriadosSet}
              esAdminOJefe={puedeRegistrar}
            />
          )}
          {tab === "listado" && (
            <AsistenciasListado
              ausencias={ausencias ?? []}
              puedeGestionar={puedeRegistrar}
              onEditar={(a) => setEditando(a)}
              onChanged={() => void load()}
            />
          )}
          {tab === "reportes" && <AsistenciasDescuentos esAdmin={esAdmin} />}
        </>
      )}

      {(modalAbierto || editando) && (
        <AusenciaModal
          ausencia={editando}
          empleados={empleados}
          esAdmin={esAdmin}
          onClose={() => {
            setModalAbierto(false);
            setEditando(null);
          }}
          onSaved={() => {
            setModalAbierto(false);
            setEditando(null);
            void load();
          }}
        />
      )}
    </div>
  );
}
