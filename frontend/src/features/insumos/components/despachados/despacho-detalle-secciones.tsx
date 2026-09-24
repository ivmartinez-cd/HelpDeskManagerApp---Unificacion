"use client";

import type { ReactNode } from "react";
import { formatPlainDate } from "@/shared/utils/date-arg";
import { cn } from "@/shared/utils/cn";
import { formatArgDateTime } from "../../utils/format";
import type { DetalleDespacho } from "../../types/despachados";
import { ResultadoBadge } from "./despacho-celdas";
import { TONO, etiquetaTipo, tieneMotivo, textoLimite } from "./semaforo";

/** Secciones del cuerpo del panel lateral de una guía (sin el recuadro de la
 * alerta, que vive en `despacho-drawer.tsx` porque dispara una escritura). */

export function Seccion({ titulo, accion, children, className }: {
  titulo: string;
  accion?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("border-b border-border py-[18px] last:border-b-0", className)}>
      <h3 className="mb-3 flex items-center justify-between gap-2 font-body text-[11px] font-bold uppercase leading-[1.4] tracking-[.05em] text-muted-foreground">
        {titulo}
        {accion}
      </h3>
      {children}
    </section>
  );
}

export function Kv({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-1 gap-x-3 gap-y-0.5 sm:grid-cols-[124px_1fr] sm:gap-y-2">
      {items.map(([dt, dd]) => (
        <div key={dt} className="contents">
          <dt className="font-body text-[13px] text-muted-foreground">{dt}</dt>
          <dd className="mb-2 min-w-0 font-body text-[13px] font-semibold [overflow-wrap:anywhere] sm:mb-0">{dd}</dd>
        </div>
      ))}
    </dl>
  );
}

export function EstadoActual({ detalle }: { detalle: DetalleDespacho }) {
  const { envio } = detalle;
  const oca = envio.estadoOca;
  const tono = TONO[envio.color];
  const items: [string, ReactNode][] = [];
  if (oca) {
    items.push(
      ["Motivo", <span key="m" className={cn(tieneMotivo(oca.motivo) && tono.text)}>{oca.motivo || "Sin Motivo"}</span>],
      ["Sucursal", oca.sucursalActual || "—"],
      ["Fecha del estado", <span key="f" className="tabular-nums">{formatPlainDate(oca.fechaEstado)}</span>],
    );
  }
  if (envio.fechaLimite) {
    items.push([
      "Límite de retiro",
      <span key="l" className="tabular-nums">
        {formatPlainDate(envio.fechaLimite)} ·{" "}
        <span className={cn("font-bold", TONO.rojo.text)}>
          {textoLimite(envio.fechaLimite, detalle.diasHabilesParaLimite)}
        </span>
      </span>,
    ]);
  }
  if (envio.observacion) {
    const clase = envio.color === "amarillo" ? cn("font-semibold", TONO.amarillo.text) : undefined;
    items.push(["Aviso", <span key="a" className={clase}>{envio.observacion}</span>]);
  }
  items.push(["Última consulta", formatArgDateTime(envio.consultadoEn)]);
  if (envio.ultimoError) {
    items.push([
      "Último error",
      <span key="e" className={TONO.rojo.text}>
        {envio.ultimoError.mensaje} ({formatArgDateTime(envio.ultimoError.ocurridoEn)})
      </span>,
    ]);
  }
  return (
    <>
      <p className="mb-1 font-heading text-base font-bold leading-[22px] text-foreground">
        {oca?.estado || "Sin datos en OCA"}
      </p>
      <Kv items={items} />
    </>
  );
}

export function Remitos({ detalle }: { detalle: DetalleDespacho }) {
  const operativa = detalle.envio.estadoOca?.operativa;
  return (
    <Seccion titulo={detalle.remitos.length > 1 ? `Remitos (${detalle.remitos.length})` : "Remito"}>
      <div className="flex flex-col gap-4">
        {detalle.remitos.map((r) => (
          <Kv
            key={r.idRemito}
            items={[
              ["Número", <span key="n" className="tabular-nums">{r.numeroRemito}</span>],
              ["Fecha", <span key="f" className="tabular-nums">{formatPlainDate(r.fechaRemito)}</span>],
              ...(operativa ? [["Operativa OCA", <span key="o" className="tabular-nums">{operativa}</span>] as [string, ReactNode]] : []),
              ["Bultos", <span key="b" className="tabular-nums">{r.bultos}</span>],
              ["Entrega a", r.entregaA || "—"],
              [
                "Incidentes",
                r.incidentes.length
                  ? r.incidentes.map((i) => `${i.numero}${i.numeroCliente ? ` · N° cliente ${i.numeroCliente}` : ""}`).join(", ")
                  : "—",
              ],
            ]}
          />
        ))}
      </div>
    </Seccion>
  );
}

export function Cliente({ detalle }: { detalle: DetalleDespacho }) {
  const incidentes = detalle.remitos.flatMap((r) => r.incidentes.map((i) => i.numero));
  return (
    <Seccion titulo="Cliente e incidente">
      <Kv
        items={[
          ["Cliente", detalle.envio.cliente],
          ["Sucursal del cliente", detalle.envio.sucursalCliente || "—"],
          ["Incidente", incidentes.length ? `${[...new Set(incidentes)].join(", ")} · pedido de insumos` : "—"],
        ]}
      />
    </Seccion>
  );
}

export function Cambios({ detalle }: { detalle: DetalleDespacho }) {
  return (
    <Seccion titulo="Cambios de estado observados">
      {detalle.cambios.length === 0 ? (
        <p className="font-body text-[13px] text-muted-foreground">Todavía no se observaron cambios de estado.</p>
      ) : (
        <ol className="m-0 list-none p-0">
          {detalle.cambios.map((c, i) => (
            <li key={`${c.observadoEn}-${i}`} className="relative pb-3.5 pl-[22px] last:pb-0">
              {i < detalle.cambios.length - 1 && (
                <span className="absolute top-3.5 -bottom-0.5 left-[5px] w-0.5 bg-border" aria-hidden="true" />
              )}
              <span className={cn("absolute top-1 left-0 h-3 w-3 rounded-full ring-[3px] ring-card", TONO[c.color].dot)} aria-hidden="true" />
              <div className="font-body text-xs tabular-nums text-muted-foreground">
                {formatPlainDate(c.fechaEstado)} · {c.sucursal || "—"}
              </div>
              <div className="font-body text-[13px] font-semibold text-foreground">
                {c.estado}
                {i === 0 && (
                  <span className="ml-2 rounded-full bg-muted px-1.5 py-px align-[1px] font-body text-[9px] font-bold uppercase leading-[14px] tracking-[.05em] text-muted-foreground">
                    Actual
                  </span>
                )}
              </div>
              {tieneMotivo(c.motivo) && (
                <div className={cn("font-body text-[13px] font-bold", TONO[c.color].text)}>{c.motivo}</div>
              )}
            </li>
          ))}
        </ol>
      )}
    </Seccion>
  );
}

export function Acciones({ detalle, accion }: { detalle: DetalleDespacho; accion?: ReactNode }) {
  return (
    <Seccion titulo="Acciones registradas" accion={accion}>
      {detalle.acciones.length === 0 ? (
        <p className="font-body text-[13px] text-muted-foreground">Todavía no hay acciones registradas para este envío.</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
          {detalle.acciones.map((a) => (
            <li key={a.id} className="rounded-[10px] bg-surface-2 px-3 py-2.5">
              <div className="flex flex-wrap items-center justify-between gap-1.5">
                <span className="font-body text-[13px] font-bold text-foreground">{etiquetaTipo(a.tipo)}</span>
                <ResultadoBadge resultado={a.resultado} />
              </div>
              <p className="my-1 whitespace-pre-line font-body text-[13px] text-foreground">{a.detalle}</p>
              <div className="font-body text-xs text-muted-foreground">
                {a.usuarioNombre} · {formatArgDateTime(a.creadaEn)}
                {a.cerroAlerta && " · cerró la alerta"}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Seccion>
  );
}
