"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiError } from "@/services/http-client";
import { grillaVariantesApi } from "../../api/grilla-variantes-api";
import type { Casilla, Slot, UserOption } from "../../types/turnos";
import type {
  AdvertenciaCobertura,
  FranjaEditable,
  GrillaVariante,
  GrillaVariantePayload,
} from "../../types/grilla-variantes";
import {
  DIAS_SEMANA,
  erroresDeFranjas,
  franjasSinOperador,
  huecosDeCobertura,
} from "../../lib/variante-validacion";
import { formatDiaMes, hhmm } from "../../lib/variante-estado";
import { VarianteAdvertencias } from "./variante-advertencias";
import { VarianteDiaTabs } from "./variante-dia-tabs";
import { VarianteFranjasPorDia } from "./variante-franjas-por-dia";
import { VarianteIdentificacionFields } from "./variante-identificacion-fields";
import { BrandButton } from "@/shared/components/ui/brand-form";

export interface PrecargaInicial {
  ausenteId: string | null;
  desde: string;
  hasta: string;
  motivo: string;
}

interface VarianteEditorProps {
  /** Con variante = edición in-place (mismo id); sin ella, alta. */
  variante?: GrillaVariante | null;
  precargaInicial?: PrecargaInicial | null;
  casillas: Casilla[];
  titular: Slot[];
  users: UserOption[];
  onClose: () => void;
  onSaved: (guardada: GrillaVariante) => void;
}

let keySeq = 0;
const nuevaKey = () => `f${++keySeq}`;

function desdeVariante(v: GrillaVariante): FranjaEditable[] {
  return v.slots.map((s) => ({
    key: nuevaKey(),
    casillaId: s.casillaId,
    diaSemana: s.diaSemana,
    horaInicio: hhmm(s.horaInicio),
    horaFin: hhmm(s.horaFin),
    userIds: s.operadores.map((o) => o.userId),
    requiereCobertura: false,
  }));
}

/** Editor de la grilla de vacaciones (ADR-025): elegir ausente + rango,
 * precargar la titular, re-cortar/crear/eliminar franjas por casilla y día,
 * asignar operadores y guardar el payload completo. Valida en vivo espejando
 * las reglas del backend; el backend revalida al guardar. */
export function VarianteEditor({
  variante = null,
  precargaInicial = null,
  casillas,
  titular,
  users,
  onClose,
  onSaved,
}: VarianteEditorProps) {
  const [ausenteId, setAusenteId] = useState<string | null>(precargaInicial?.ausenteId ?? null);
  const [desde, setDesde] = useState(variante?.desde ?? precargaInicial?.desde ?? "");
  const [hasta, setHasta] = useState(variante?.hasta ?? precargaInicial?.hasta ?? "");
  const [motivo, setMotivo] = useState(variante?.motivo ?? precargaInicial?.motivo ?? "");
  const [origenTexto, setOrigenTexto] = useState(variante?.origenTexto ?? "");
  const [franjas, setFranjas] = useState<FranjaEditable[]>(() =>
    variante ? desdeVariante(variante) : [],
  );
  const [diaActivo, setDiaActivo] = useState(0);
  const [ausencias, setAusencias] = useState<AdvertenciaCobertura[]>([]);
  const [precargando, setPrecargando] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nombreCasilla = useCallback(
    (id: string) => casillas.find((c) => c.id === id)?.nombre ?? "?",
    [casillas],
  );
  const nombreUser = useCallback(
    (id: string) => users.find((u) => u.id === id)?.fullName ?? id,
    [users],
  );
  const ausenciaPorUser = useMemo(
    () => new Map(ausencias.filter((a) => a.userId).map((a) => [a.userId as string, a])),
    [ausencias],
  );
  const opcionesOperador = useMemo(
    () =>
      users.map((u) => {
        const aus = ausenciaPorUser.get(u.id);
        return {
          id: u.id,
          label: u.fullName,
          sublabel:
            aus && aus.desde && aus.hasta
              ? `vacaciones ${formatDiaMes(aus.desde)}–${formatDiaMes(aus.hasta)}`
              : undefined,
        };
      }),
    [users, ausenciaPorUser],
  );

  const errores = useMemo(
    () => erroresDeFranjas(franjas, nombreCasilla, nombreUser),
    [franjas, nombreCasilla, nombreUser],
  );
  const huecos = useMemo(() => huecosDeCobertura(franjas, titular), [franjas, titular]);
  const sinOperador = useMemo(() => franjasSinOperador(franjas), [franjas]);
  const keysConError = useMemo(() => new Set(errores.flatMap((e) => e.keys)), [errores]);
  const rangoInvalido = Boolean(desde && hasta && hasta < desde);
  const puedeGuardar =
    Boolean(desde && hasta) && !rangoInvalido && franjas.length > 0 && errores.length === 0;

  const precargar = useCallback(() => {
    if (!ausenteId || !desde || !hasta || hasta < desde) return;
    setPrecargando(true);
    setError(null);
    grillaVariantesApi
      .precargar(ausenteId, desde, hasta)
      .then((p) => {
        setFranjas(
          p.slots.map((s) => ({
            key: nuevaKey(),
            casillaId: s.casillaId,
            diaSemana: s.diaSemana,
            horaInicio: hhmm(s.horaInicio),
            horaFin: hhmm(s.horaFin),
            userIds: s.operadores.map((o) => o.userId),
            requiereCobertura: s.requiereCobertura,
          })),
        );
        setAusencias(p.advertencias);
        setMotivo((m) => m || `Vacaciones ${p.ausenteNombre ?? ""}`.trim());
        const primerDia = p.slots.find((s) => s.requiereCobertura)?.diaSemana ?? p.slots[0]?.diaSemana;
        if (primerDia !== undefined) setDiaActivo(primerDia);
      })
      .catch((err: unknown) => {
        console.error("Error al precargar la grilla titular:", err);
        setError(err instanceof ApiError ? err.message : "No se pudo precargar la grilla titular.");
      })
      .finally(() => setPrecargando(false));
  }, [ausenteId, desde, hasta]);

  // Llegada desde Aprobaciones (query params): precarga una sola vez al montar.
  const autoPrecargado = useRef(false);
  useEffect(() => {
    if (autoPrecargado.current || !precargaInicial?.ausenteId || variante) return;
    autoPrecargado.current = true;
    precargar();
  }, [precargaInicial, variante, precargar]);

  const actualizar = (key: string, cambios: Partial<FranjaEditable>) =>
    setFranjas((prev) => prev.map((f) => (f.key === key ? { ...f, ...cambios } : f)));
  const eliminar = (key: string) => setFranjas((prev) => prev.filter((f) => f.key !== key));
  const agregar = (casillaId: string) =>
    setFranjas((prev) => [
      ...prev,
      { key: nuevaKey(), casillaId, diaSemana: diaActivo, horaInicio: "", horaFin: "", userIds: [], requiereCobertura: false },
    ]);
  const copiarDiaALaborables = () =>
    setFranjas((prev) => {
      const base = prev.filter((f) => f.diaSemana === diaActivo);
      const otros = prev.filter((f) => f.diaSemana === diaActivo || f.diaSemana > 4);
      const copias = [0, 1, 2, 3, 4]
        .filter((d) => d !== diaActivo)
        .flatMap((d) => base.map((f) => ({ ...f, key: nuevaKey(), diaSemana: d })));
      return [...otros, ...copias];
    });

  const guardar = () => {
    if (!puedeGuardar) return;
    setSaving(true);
    setError(null);
    const payload: GrillaVariantePayload = {
      motivo: motivo.trim() || null,
      origenTexto: origenTexto.trim() || null,
      desde,
      hasta,
      slots: franjas.map((f) => ({
        casillaId: f.casillaId,
        diaSemana: f.diaSemana,
        horaInicio: f.horaInicio,
        horaFin: f.horaFin,
        userIds: f.userIds,
      })),
    };
    (variante ? grillaVariantesApi.update(variante.id, payload) : grillaVariantesApi.create(payload))
      .then(onSaved)
      .catch((err: unknown) => {
        console.error("Error al guardar la grilla de vacaciones:", err);
        setError(err instanceof ApiError ? err.message : "No se pudo guardar la grilla.");
      })
      .finally(() => setSaving(false));
  };

  const franjasDelDia = franjas.filter((f) => f.diaSemana === diaActivo);
  const opcionesAusente = users.map((u) => ({ id: u.id, label: u.fullName }));

  return (
    <section
      aria-label={variante ? "Editar grilla de vacaciones" : "Nueva grilla de vacaciones"}
      className="flex flex-col gap-5 rounded-[14px] border border-border bg-card p-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="font-heading text-lg font-extrabold text-foreground">
          {variante ? "Editar grilla de vacaciones" : "Nueva grilla de vacaciones"}
        </h2>
        <p className="max-w-xl font-body text-xs text-muted-foreground">
          La grilla titular no se toca: durante la vigencia, Turnos del día muestra esta grilla y
          al vencer vuelve sola a la titular. Los huecos de cobertura se avisan pero no bloquean.
        </p>
      </div>

      {error && (
        <p className="rounded-[10px] border border-destructive/20 bg-destructive/10 px-4 py-3 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      <VarianteIdentificacionFields
        esEdicion={Boolean(variante)}
        opcionesAusente={opcionesAusente}
        ausenteId={ausenteId}
        setAusenteId={setAusenteId}
        desde={desde}
        setDesde={setDesde}
        hasta={hasta}
        setHasta={setHasta}
        rangoInvalido={rangoInvalido}
        precargar={precargar}
        precargando={precargando}
        motivo={motivo}
        setMotivo={setMotivo}
        origenTexto={origenTexto}
        setOrigenTexto={setOrigenTexto}
      />

      <VarianteDiaTabs
        franjas={franjas}
        diaActivo={diaActivo}
        setDiaActivo={setDiaActivo}
        hayFranjasDelDia={franjasDelDia.length > 0}
        onCopiarALaborables={copiarDiaALaborables}
      />

      <VarianteFranjasPorDia
        casillas={casillas}
        diaLabel={DIAS_SEMANA[diaActivo]}
        franjasDelDia={franjasDelDia}
        opcionesOperador={opcionesOperador}
        keysConError={keysConError}
        onAgregar={agregar}
        onActualizar={actualizar}
        onEliminar={eliminar}
      />

      <VarianteAdvertencias
        errores={errores}
        huecos={huecos}
        sinOperador={sinOperador}
        ausencias={ausencias}
        nombreCasilla={nombreCasilla}
      />

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <BrandButton type="button" variant="outline" onClick={onClose}>
          Cancelar
        </BrandButton>
        <BrandButton type="button" onClick={guardar} loading={saving} disabled={!puedeGuardar}>
          {variante ? "Guardar cambios" : "Guardar grilla"}
        </BrandButton>
      </div>
    </section>
  );
}
