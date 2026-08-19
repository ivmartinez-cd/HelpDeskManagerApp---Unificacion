"use client";

import { useEffect, useMemo, useState } from "react";
import { useSession } from "@/services/session-provider";
import { BrandSelect } from "@/shared/components/ui/brand-form";
import { solicitudesApi } from "../api/solicitudes-api";
import {
  diasDelMes,
  estadoCelda,
  fechaIso,
  statsDelAnio,
} from "../lib/asistencias-stats";
import { formatFecha } from "../lib/fechas";
import { COLOR_VACACIONES, TIPO_AUSENCIA } from "../lib/tipos-ausencia";
import type { Ausencia, EmpleadoListItem, Solicitud } from "../types/vacaciones";

const MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

const LEYENDA = [
  { label: "Vacaciones", color: COLOR_VACACIONES },
  { label: "Enfermedad", color: TIPO_AUSENCIA.BAJA_ENFERMEDAD.color },
  { label: "Trámites", color: TIPO_AUSENCIA.TRAMITE_PERSONAL.color },
  { label: "Home", color: TIPO_AUSENCIA.HOME_OFFICE.color },
  { label: "Descuento", color: TIPO_AUSENCIA.DESCUENTO_DIA.color },
  { label: "Guardia", color: TIPO_AUSENCIA.GUARDIA.color },
  { label: "Examen", color: TIPO_AUSENCIA.DIA_ESTUDIO.color },
];

interface Props {
  ausencias: Ausencia[];
  empleados: EmpleadoListItem[];
  feriados: Set<string>;
  esAdminOJefe: boolean;
}

export function AsistenciasCalendario({
  ausencias,
  empleados,
  feriados,
  esAdminOJefe,
}: Props) {
  const { user } = useSession();
  const anioActual = new Date().getFullYear();
  const anios = useMemo(() => {
    const desde = 2017;
    return Array.from({ length: anioActual + 2 - desde + 1 }, (_, i) => desde + i);
  }, [anioActual]);

  const propio = empleados.find((e) => e.userId === user.id);
  const [empleadoId, setEmpleadoId] = useState(propio?.id ?? empleados[0]?.id ?? "");
  const [anio, setAnio] = useState(anioActual);
  const [vacaciones, setVacaciones] = useState<Solicitud[]>([]);

  useEffect(() => {
    if (!empleadoId) return;
    solicitudesApi
      .list({ empleadoId })
      .then(setVacaciones)
      .catch((err: unknown) => {
        console.error("Error al cargar vacaciones del empleado:", err);
        setVacaciones([]);
      });
  }, [empleadoId]);

  const empleado = empleados.find((e) => e.id === empleadoId);
  const propias = useMemo(
    () => ausencias.filter((a) => a.empleadoId === empleadoId),
    [ausencias, empleadoId],
  );
  const delAnio = useMemo(
    () => propias.filter((a) => a.startDate.slice(0, 4) === String(anio)),
    [propias, anio],
  );
  const stats = useMemo(
    () => statsDelAnio(anio, propias, vacaciones, feriados),
    [anio, propias, vacaciones, feriados],
  );

  const kpis = [
    { label: "Días de baja", valor: stats.totalBajas, color: "#ef4444" },
    { label: "Días trabajados", valor: stats.diasTrabajados, color: "#059669" },
    { label: "Días de enfermedad", valor: stats.enfermedad, color: TIPO_AUSENCIA.BAJA_ENFERMEDAD.color },
    { label: "De vacaciones", valor: stats.vacaciones, color: COLOR_VACACIONES },
    { label: "Trámites y estudio", valor: stats.tramitesEstudio, color: "#2563eb" },
    { label: "Descuento día", valor: stats.descuento, color: "#ef4444" },
  ];

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-2.5 md:grid-cols-3 xl:grid-cols-6">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-[10px] border border-border bg-card px-3 py-3.5">
            <p className="mb-2 font-heading text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
              {k.label}
            </p>
            <p className="font-heading text-[22px] font-extrabold leading-none" style={{ color: k.color }}>
              {k.valor}
            </p>
            <p className="mt-1 font-body text-[11px] text-muted-foreground">en {anio}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {esAdminOJefe && (
          <div className="w-64">
            <BrandSelect
              label="Empleado"
              value={empleadoId}
              onChange={(e) => setEmpleadoId(e.target.value)}
            >
              {empleados.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.lastName}, {e.firstName}
                </option>
              ))}
            </BrandSelect>
          </div>
        )}
        <div className="w-28">
          <BrandSelect
            label="Año"
            value={String(anio)}
            onChange={(e) => setAnio(Number(e.target.value))}
          >
            {anios.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </BrandSelect>
        </div>
        {empleado && (
          <p className="self-end pb-2 font-body text-[12.5px] text-muted-foreground">
            {empleado.sectorNombre} · {empleado.cargoNombre} · Ingreso:{" "}
            {formatFecha(empleado.hireDate)}
          </p>
        )}
      </div>

      <div className="grid items-start gap-4 xl:grid-cols-[1fr_240px]">
        <div className="overflow-hidden rounded-[12px] border border-border bg-card">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-[18px] py-3.5">
            <h3 className="font-heading text-sm font-bold text-foreground">
              Calendario de bajas · {anio}
            </h3>
            <div className="flex flex-wrap gap-2.5">
              {LEYENDA.map((l) => (
                <span key={l.label} className="flex items-center gap-1">
                  <span
                    className="h-2.5 w-2.5 rounded-[2px]"
                    style={{ backgroundColor: l.color }}
                  />
                  <span className="font-body text-[10.5px] text-muted-foreground">
                    {l.label}
                  </span>
                </span>
              ))}
            </div>
          </div>
          <div className="overflow-x-auto p-4">
            <div className="mb-1.5 flex items-center gap-0.5 pl-[46px]">
              {Array.from({ length: 31 }, (_, i) => (
                <span
                  key={i}
                  className="w-[18px] flex-none text-center font-heading text-[8.5px] font-bold text-muted-foreground/60"
                >
                  {i + 1}
                </span>
              ))}
            </div>
            {MESES.map((mes, mi) => (
              <div key={mes} className="mb-[3px] flex items-center gap-0.5">
                <span className="w-[42px] flex-none pr-1.5 text-right font-body text-[11.5px] font-semibold text-muted-foreground">
                  {mes}
                </span>
                {Array.from({ length: 31 }, (_, di) => {
                  const dia = di + 1;
                  if (dia > diasDelMes(anio, mi + 1)) {
                    return <span key={di} className="h-[22px] w-[18px] flex-none" />;
                  }
                  const fecha = fechaIso(anio, mi + 1, dia);
                  const celda = estadoCelda(fecha, propias, vacaciones, feriados);
                  const dow = new Date(anio, mi, dia).getDay();
                  const finde = dow === 0 || dow === 6;
                  const fondo = celda
                    ? celda.halfDay
                      ? `linear-gradient(135deg, ${celda.color} 50%, rgba(127,127,127,.12) 50%)`
                      : celda.color
                    : finde
                      ? "rgba(127,127,127,.10)"
                      : "rgba(127,127,127,.16)";
                  return (
                    <span
                      key={di}
                      title={`${dia}/${mi + 1}${celda ? ` — ${celda.label}` : ""}`}
                      className="h-[22px] w-[18px] flex-none rounded-[3px]"
                      style={{ background: fondo }}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[12px] border border-border bg-card">
          <div className="border-b border-border px-4 py-3.5">
            <h3 className="font-heading text-[13.5px] font-bold text-foreground">
              Resumen de bajas · {anio}
            </h3>
            {empleado && (
              <p className="mt-0.5 font-body text-[11.5px] text-muted-foreground">
                {empleado.firstName} {empleado.lastName}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2 p-3.5">
            <ResumenFila label="Vacaciones" color={COLOR_VACACIONES} total={stats.vacaciones} />
            {(
              [
                "BAJA_ENFERMEDAD",
                "TRAMITE_PERSONAL",
                "HOME_OFFICE",
                "DESCUENTO_DIA",
                "GUARDIA",
                "DIA_ESTUDIO",
              ] as const
            ).map((tipo) => (
              <ResumenFila
                key={tipo}
                label={TIPO_AUSENCIA[tipo].label}
                color={TIPO_AUSENCIA[tipo].color}
                total={stats.porTipo[tipo]}
              />
            ))}
          </div>
          <div className="border-t border-border px-4 py-3">
            <p className="mb-1 font-body text-[11.5px] text-muted-foreground">
              Total días con baja
            </p>
            <p className="font-heading text-[22px] font-extrabold text-foreground">
              {stats.totalBajas}{" "}
              <span className="font-body text-[13px] font-normal text-muted-foreground">
                días
              </span>
            </p>
          </div>
        </div>
      </div>

      {delAnio.length === 0 && vacaciones.length === 0 && (
        <p className="font-body text-xs text-muted-foreground">
          Sin bajas registradas este año.
        </p>
      )}
    </div>
  );
}

function ResumenFila({
  label,
  color,
  total,
}: {
  label: string;
  color: string;
  total: number;
}) {
  return (
    <div className="flex items-center gap-2 rounded-[8px] bg-muted/30 px-2.5 py-2">
      <span className="h-2 w-2 flex-none rounded-full" style={{ backgroundColor: color }} />
      <span className="flex-1 font-body text-[12.5px] text-foreground">{label}</span>
      <span className="font-heading text-sm font-bold" style={{ color }}>
        {total}
      </span>
    </div>
  );
}
