"use client";

import { useState, type FormEvent } from "react";
import { useMisSolicitudesTv } from "../hooks/use-mis-solicitudes-tv";
import type { EstadoSolicitudTv } from "../types/bono-tecnicos";
import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";

const ESTADO_BADGE: Record<EstadoSolicitudTv, BadgeVariant> = {
  PENDIENTE: "warning",
  APROBADA: "success",
  RECHAZADA: "danger",
};

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export function MisSolicitudesTv() {
  const { monthValue, setMonthValue, solicitudes, loading, submitting, error, enviarSolicitud } =
    useMisSolicitudesTv();
  const [fecha, setFecha] = useState(todayIso());
  const [razonSocial, setRazonSocial] = useState("");
  const [sucursal, setSucursal] = useState("");
  const [tareaRealizada, setTareaRealizada] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);
    enviarSolicitud({
      fecha,
      razon_social: razonSocial,
      sucursal,
      tarea_realizada: tareaRealizada,
    })
      .then(() => {
        setRazonSocial("");
        setSucursal("");
        setTareaRealizada("");
        setFecha(todayIso());
      })
      .catch(() => setFormError("No se pudo enviar la solicitud."));
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold text-foreground">
          Mis Tareas Varias
        </h1>
        <p className="font-body text-sm text-muted-foreground">
          Cargá una Tarea Varia (TV) realizada. Queda pendiente hasta que un supervisor la
          apruebe.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 rounded-[12px] border border-border bg-card p-6"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <BrandInput
            label="Fecha"
            type="date"
            value={fecha}
            max={todayIso()}
            required
            onChange={(e) => setFecha(e.target.value)}
          />
          <BrandInput
            label="Razón Social"
            placeholder="Ej. Exolgan"
            value={razonSocial}
            required
            maxLength={200}
            onChange={(e) => setRazonSocial(e.target.value)}
          />
          <BrandInput
            label="Sucursal"
            placeholder="Ej. Dock Sur"
            value={sucursal}
            required
            maxLength={200}
            onChange={(e) => setSucursal(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            Tarea Realizada
          </label>
          <textarea
            value={tareaRealizada}
            required
            maxLength={2000}
            rows={3}
            placeholder="Describí la tarea realizada"
            onChange={(e) => setTareaRealizada(e.target.value)}
            className="rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
          />
        </div>
        {formError && <p className="font-body text-sm text-destructive">{formError}</p>}
        <div>
          <BrandButton type="submit" loading={submitting}>
            Enviar solicitud
          </BrandButton>
        </div>
      </form>

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-heading text-lg font-bold text-foreground">Mis solicitudes</h2>
          <input
            type="month"
            value={monthValue}
            onChange={(e) => setMonthValue(e.target.value)}
            className="rounded-[8px] border border-border bg-card px-3 py-1.5 font-body text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-orange/60"
          />
        </div>

        {loading && (
          <div className="flex h-32 items-center justify-center">
            <Spinner />
          </div>
        )}
        {!loading && error && (
          <p className="font-body text-sm text-destructive">{error}</p>
        )}
        {!loading && !error && solicitudes.length === 0 && (
          <p className="font-body text-sm text-muted-foreground">
            Sin solicitudes en este período.
          </p>
        )}
        {!loading && !error && solicitudes.length > 0 && (
          <div className="overflow-x-auto rounded-[12px] border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2">Fecha</th>
                  <th className="px-4 py-2">Razón Social</th>
                  <th className="px-4 py-2">Sucursal</th>
                  <th className="px-4 py-2">Tarea</th>
                  <th className="px-4 py-2">Estado</th>
                </tr>
              </thead>
              <tbody>
                {solicitudes.map((s) => (
                  <tr key={s.id} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2 font-body text-foreground">{s.fecha}</td>
                    <td className="px-4 py-2 font-body text-foreground">{s.razon_social}</td>
                    <td className="px-4 py-2 font-body text-foreground">{s.sucursal}</td>
                    <td className="px-4 py-2 font-body text-foreground">{s.tarea_realizada}</td>
                    <td className="px-4 py-2">
                      <Badge variant={ESTADO_BADGE[s.estado]}>{s.estado}</Badge>
                      {s.estado === "RECHAZADA" && s.motivo_rechazo && (
                        <p className="mt-1 font-body text-xs text-muted-foreground">
                          {s.motivo_rechazo}
                        </p>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
