"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Copy, Download, Plus } from "lucide-react";
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
import { formatDiaMes, hhmm, hoyIso } from "../../lib/variante-estado";
import { VarianteAdvertencias } from "./variante-advertencias";
import { VarianteFranjaFila } from "./variante-franja-fila";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";

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

      <div className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_160px_160px_auto]">
        <SearchableSelect
          label="¿Quién falta?"
          options={opcionesAusente}
          value={ausenteId}
          onChange={setAusenteId}
          placeholder="Buscá operador…"
          disabled={Boolean(variante)}
        />
        <BrandInput
          label="Desde"
          type="date"
          value={desde}
          min={variante ? undefined : hoyIso()}
          onChange={(e) => setDesde(e.target.value)}
        />
        <BrandInput
          label="Hasta"
          type="date"
          value={hasta}
          min={desde || hoyIso()}
          onChange={(e) => setHasta(e.target.value)}
        />
        <div className="flex items-end">
          <BrandButton
            type="button"
            variant="outline"
            onClick={precargar}
            loading={precargando}
            disabled={!ausenteId || !desde || !hasta || rangoInvalido}
            title="Trae la grilla titular con las franjas del ausente marcadas como huecos a resolver"
          >
            <Download className="h-4 w-4" />
            Precargar
          </BrandButton>
        </div>
      </div>
      {rangoInvalido && (
        <p className="font-body text-xs text-destructive">La fecha de fin es anterior a la de inicio.</p>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <BrandInput
          label="Motivo"
          value={motivo}
          maxLength={200}
          placeholder="Vacaciones M. J. Vela"
          onChange={(e) => setMotivo(e.target.value)}
        />
        <BrandInput
          label="Origen (opcional)"
          value={origenTexto}
          maxLength={200}
          placeholder="Solicitud de vacaciones aprobada el 20/08"
          hint="Texto libre para trazabilidad; no enlaza con Gestión de Personal."
          onChange={(e) => setOrigenTexto(e.target.value)}
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2">
        <div role="tablist" aria-label="Día de semana" className="flex flex-wrap items-center gap-1">
          {DIAS_SEMANA.map((dia, idx) => {
            const cantidad = franjas.filter((f) => f.diaSemana === idx).length;
            return (
              <button
                key={dia}
                type="button"
                role="tab"
                aria-selected={diaActivo === idx}
                onClick={() => setDiaActivo(idx)}
                className={`rounded-[6px] px-3 py-1.5 font-body text-xs font-semibold transition-colors ${
                  diaActivo === idx
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted"
                }`}
              >
                {dia}
                {cantidad > 0 && <span className="ml-1 opacity-70">({cantidad})</span>}
              </button>
            );
          })}
        </div>
        {diaActivo <= 4 && franjasDelDia.length > 0 && (
          <BrandButton type="button" variant="outline" size="sm" onClick={copiarDiaALaborables}>
            <Copy className="h-3.5 w-3.5" />
            Aplicar este día a lunes–viernes
          </BrandButton>
        )}
      </div>

      <div className="flex flex-col gap-4">
        {casillas.map((casilla) => {
          const filas = franjasDelDia
            .filter((f) => f.casillaId === casilla.id)
            .sort((a, b) => a.horaInicio.localeCompare(b.horaInicio));
          return (
            <div key={casilla.id} className="flex flex-col gap-2" data-testid={`casilla-${casilla.nombre}`}>
              <div className="flex items-center justify-between">
                <span className="font-heading text-sm font-bold text-foreground">
                  {casilla.nombre} · {DIAS_SEMANA[diaActivo]}
                </span>
                <BrandButton type="button" variant="outline" size="sm" onClick={() => agregar(casilla.id)}>
                  <Plus className="h-3.5 w-3.5" />
                  Agregar franja en {casilla.nombre}
                </BrandButton>
              </div>
              {filas.length === 0 ? (
                <p className="rounded-[10px] border border-dashed border-border px-4 py-3 font-body text-xs text-muted-foreground">
                  Sin franjas para {casilla.nombre} este día.
                </p>
              ) : (
                filas.map((f) => (
                  <VarianteFranjaFila
                    key={f.key}
                    franja={f}
                    casillaNombre={casilla.nombre}
                    operadores={opcionesOperador}
                    conError={keysConError.has(f.key)}
                    onChange={(cambios) => actualizar(f.key, cambios)}
                    onRemove={() => eliminar(f.key)}
                  />
                ))
              )}
            </div>
          );
        })}
      </div>

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
