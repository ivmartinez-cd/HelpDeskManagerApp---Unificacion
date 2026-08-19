"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PropuestaN2Match, ResultadoAutoVinculoN1 } from "../types/liquidaciones";

function Tarjeta({ numero, titulo, descripcion, badge, children }: {
  numero: string; titulo: string; descripcion: string;
  badge?: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <div className="rounded-[8px] border border-border p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-body text-sm font-semibold text-foreground">
            <span className="text-brand-orange">{numero}</span> · {titulo}
          </p>
          <p className="font-body text-xs text-muted-foreground">{descripcion}</p>
        </div>
        {badge}
      </div>
      {children}
    </div>
  );
}

function SeccionAutoVincularN1({ prestadorId, onCambio }: {
  prestadorId: string; onCambio: () => void;
}) {
  const [ejecutando, setEjecutando] = useState(false);
  const [resultado, setResultado] = useState<ResultadoAutoVinculoN1 | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ejecutar = async () => {
    setEjecutando(true); setError(null);
    try {
      setResultado(await liquidacionesApi.autoVincularN1(prestadorId));
      onCambio();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error al vincular"); }
    finally { setEjecutando(false); }
  };
  return (
    <Tarjeta
      numero="3a"
      titulo="Vincular automáticamente (símbolo/abreviatura)"
      descripcion={'Sucursales que difieren solo en el símbolo del número (Nº/N°/N.º) o en una abreviatura de palabra (Sec./Sup./Pcia....) — misma confianza que un match exacto. No consulta Google.'}
      badge={<Badge variant="success">no usa Google</Badge>}
    >
      <BrandButton size="sm" variant="outline" loading={ejecutando} onClick={ejecutar} className="self-start">
        Vincular automáticamente
      </BrandButton>
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      {resultado && (
        <div className="flex flex-wrap gap-2">
          <Badge variant="success">{resultado.vinculadas} vinculadas</Badge>
          <Badge variant="neutral">{resultado.sinCambios} ya estaban al día</Badge>
        </div>
      )}
    </Tarjeta>
  );
}

function Candidato({ tablaKmId, candidato, onResuelto }: {
  tablaKmId: string;
  candidato: PropuestaN2Match["candidatos"][number];
  onResuelto: () => void;
}) {
  const [ejecutando, setEjecutando] = useState<"confirmar" | "rechazar" | null>(null);

  const confirmar = async () => {
    setEjecutando("confirmar");
    try {
      await liquidacionesApi.confirmarVinculo(tablaKmId, candidato.sigesSucursalId);
      toast.success(`${candidato.sucursalNombre}: vínculo confirmado`);
      onResuelto();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al confirmar");
    } finally { setEjecutando(null); }
  };

  const rechazar = async () => {
    setEjecutando("rechazar");
    try {
      await liquidacionesApi.rechazarPropuesta(tablaKmId, candidato.sigesSucursalId);
      onResuelto();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al rechazar");
    } finally { setEjecutando(null); }
  };

  return (
    <div className="flex items-center justify-between gap-3 rounded-[6px] border border-border/70 bg-muted/20 px-3 py-2">
      <div className="min-w-0">
        <p className="font-body text-sm font-semibold text-foreground truncate">{candidato.sucursalNombre}</p>
        <p className="font-body text-xs text-muted-foreground truncate">
          {candidato.domicilio ?? "sin domicilio"} · {candidato.motivo}
        </p>
      </div>
      <div className="flex flex-shrink-0 items-center gap-2">
        <Badge variant="neutral">{Math.round(candidato.score * 100)}%</Badge>
        <BrandButton size="sm" variant="outline" loading={ejecutando === "rechazar"} onClick={rechazar}>
          Rechazar
        </BrandButton>
        <BrandButton size="sm" loading={ejecutando === "confirmar"} onClick={confirmar}>
          Confirmar
        </BrandButton>
      </div>
    </div>
  );
}

function PropuestaItem({ propuesta, onResuelto }: {
  propuesta: PropuestaN2Match; onResuelto: () => void;
}) {
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <p className="font-body text-sm font-semibold text-foreground">
        {propuesta.empresaNombre} — {propuesta.sucursalNombre}
      </p>
      <div className="mt-2 flex flex-col gap-1.5">
        {propuesta.candidatos.map((c) => (
          <Candidato
            key={c.sigesSucursalId}
            tablaKmId={propuesta.tablaKmId}
            candidato={c}
            onResuelto={onResuelto}
          />
        ))}
      </div>
    </div>
  );
}

/** Paso "Sin match" del wizard APB: N1 se vincula en bloque (3a); los
 * candidatos N2 SIEMPRE requieren confirmación humana (3b) — un rechazo se
 * recuerda y no vuelve a proponerse. */
export function PasoMatching({ prestadorId, onCambio }: {
  prestadorId: string; onCambio: () => void;
}) {
  const [propuestas, setPropuestas] = useState<PropuestaN2Match[] | null>(null);

  const refresh = () =>
    liquidacionesApi.listPropuestasN2(prestadorId).then(setPropuestas).catch(() => setPropuestas([]));
  useEffect(() => { void refresh(); }, [prestadorId]); // eslint-disable-line react-hooks/exhaustive-deps

  const onResuelto = () => { void refresh(); onCambio(); };

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Estas filas de tu Tabla KM no aparecen con el mismo nombre en Gestión — puede ser
        un símbolo distinto (Nº vs N°), una abreviatura, o que la sucursal cambió de
        nombre. Acá revisás candidato por candidato: nada se vincula sin que lo confirmes.
      </p>

      <SeccionAutoVincularN1 prestadorId={prestadorId} onCambio={onCambio} />

      <Tarjeta
        numero="3b"
        titulo="Confirmar candidatos"
        descripcion="Cada candidato muestra qué difiere del nombre local — confirmá el correcto o rechazalo si no es esa sucursal."
      >
        {propuestas === null ? (
          <p className="font-body text-sm text-muted-foreground italic">Cargando…</p>
        ) : propuestas.length > 0 ? (
          <div className="flex max-h-[38vh] flex-col gap-2 overflow-y-auto pr-1">
            {propuestas.map((p) => (
              <PropuestaItem key={p.tablaKmId} propuesta={p} onResuelto={onResuelto} />
            ))}
          </div>
        ) : (
          <p className="font-body text-sm text-muted-foreground italic">
            ✓ No hay candidatos pendientes de confirmación.
          </p>
        )}
      </Tarjeta>
    </div>
  );
}
