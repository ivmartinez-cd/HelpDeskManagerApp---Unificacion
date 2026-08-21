"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, RefreshCw, Sparkles, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { clientesNuevosApi } from "../api/clientes-nuevos-api";
import { contadoresApi } from "../api/contadores-api";
import type { Operador } from "../types/calendario";
import type { CandidatoClienteNuevo, ClienteNuevo, ClienteNuevoPayload } from "../types/clientes-nuevos";
import {
  FILTROS_ESTADO,
  type FiltroEstado,
  coincideBusqueda,
  cumpleFiltro,
  payloadDesdeCandidato,
} from "../lib/clientes-nuevos";
import { ClienteNuevoModal } from "./cliente-nuevo-modal";
import { ClientesNuevosCandidatosModal } from "./clientes-nuevos-candidatos-modal";
import { ClientesNuevosTabla } from "./clientes-nuevos-tabla";
import { useSession } from "@/services/session-provider";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";

function KpiCard({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="flex min-w-[120px] flex-col gap-0.5 rounded-[12px] border border-border bg-card px-4 py-3">
      <span className={`font-heading text-2xl font-extrabold tabular-nums ${tone}`}>{value}</span>
      <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
    </div>
  );
}

export function ClientesNuevosView() {
  const { user, can } = useSession();
  const puedeEditar = user.isSuperadmin || can("contadores", "manage");

  const [fichas, setFichas] = useState<ClienteNuevo[] | null>(null);
  const [operadores, setOperadores] = useState<Operador[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [filtro, setFiltro] = useState<FiltroEstado>("abiertas");
  const [busqueda, setBusqueda] = useState("");
  const [creando, setCreando] = useState<ClienteNuevoPayload | null | false>(false);
  const [editando, setEditando] = useState<ClienteNuevo | null>(null);
  const [verCandidatos, setVerCandidatos] = useState(false);

  const load = useCallback(
    (refresh = false) =>
      Promise.all([
        clientesNuevosApi.list(refresh),
        contadoresApi.listCalendarioOperadores().catch(() => [] as Operador[]),
      ])
        .then(([items, ops]) => {
          setFichas(items);
          setOperadores(ops);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar clientes nuevos:", err);
          setError("No se pudieron cargar las fichas. Intentá de nuevo.");
        }),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const operadorMeta = useMemo(() => new Map(operadores.map((o) => [o.id, o])), [operadores]);

  const visibles = useMemo(() => {
    if (!fichas) return [];
    const q = busqueda.trim().toLowerCase();
    return fichas.filter((f) => cumpleFiltro(f, filtro) && coincideBusqueda(f, q));
  }, [fichas, filtro, busqueda]);

  const kpis = useMemo(() => {
    const abiertas = (fichas ?? []).filter((f) => f.estado !== "CERRADO");
    return {
      abiertas: abiertas.length,
      esperando: abiertas.filter((f) => f.estado === "ESPERANDO_INSTALACION").length,
      listas: abiertas.filter((f) => f.listo_para_stc).length,
      stcPendiente: abiertas.filter((f) => f.estado === "STC_PENDIENTE").length,
      stcEnviado: abiertas.filter((f) => f.estado === "STC_ENVIADO").length,
    };
  }, [fichas]);

  const handleRefresh = () => {
    setRefreshing(true);
    void load(true).finally(() => setRefreshing(false));
  };

  const handleDelete = (f: ClienteNuevo) => {
    if (!window.confirm(`¿Borrar la ficha de ${f.cliente}? Esta acción no se puede deshacer.`)) {
      return;
    }
    clientesNuevosApi
      .remove(f.id)
      .then(() => {
        toast.success(`Ficha de ${f.cliente} borrada`);
        return load();
      })
      .catch((err: unknown) => {
        console.error("Error al borrar la ficha:", err);
        toast.error("No se pudo borrar la ficha.");
      });
  };

  const handleElegirCandidato = (c: CandidatoClienteNuevo) => {
    setVerCandidatos(false);
    setCreando(payloadDesdeCandidato(c));
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Clientes nuevos
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Seguimiento del alta de cada cliente nuevo hasta enviar el STC · Lo que trae el mail
            &quot;Nuevo Negocio&quot; de Comercial + instalaciones reales de Siges.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <BrandButton variant="outline" loading={refreshing} onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
            Actualizar Siges
          </BrandButton>
          {puedeEditar && (
            <>
              <BrandButton variant="outline" onClick={() => setVerCandidatos(true)}>
                <Sparkles className="h-4 w-4" />
                Sugerencias de Siges
              </BrandButton>
              <BrandButton onClick={() => setCreando(null)}>
                <Plus className="h-4 w-4" />
                Nueva ficha
              </BrandButton>
            </>
          )}
        </div>
      </div>

      {fichas && (
        <div className="flex flex-wrap gap-3">
          <KpiCard label="Abiertas" value={kpis.abiertas} tone="text-foreground" />
          <KpiCard label="Esperando instalación" value={kpis.esperando} tone="text-foreground" />
          <KpiCard label="Listas para STC" value={kpis.listas} tone="text-brand-orange" />
          <KpiCard label="STC pendiente" value={kpis.stcPendiente} tone="text-warning" />
          <KpiCard label="STC enviado" value={kpis.stcEnviado} tone="text-success" />
        </div>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl
          label="Filtrar por estado"
          size="sm"
          options={FILTROS_ESTADO}
          value={filtro}
          onChange={(v) => setFiltro(v as FiltroEstado)}
        />
        <div className="min-w-[240px]">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Cliente, contrato, vendedor, operador, notas…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
      </div>

      {fichas === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }, (_, i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {fichas !== null && !error && (
        <>
          {visibles.length === 0 ? (
            <BrandEmptyState
              icon={UserPlus}
              title={fichas.length === 0 ? "Todavía no hay fichas" : "Sin resultados"}
              description={
                fichas.length === 0
                  ? "Creá la primera desde el mail de Comercial o desde las sugerencias de Siges."
                  : "Ninguna ficha cumple el filtro actual."
              }
            />
          ) : (
            <ClientesNuevosTabla
              rows={visibles}
              operadorMeta={operadorMeta}
              canEdit={puedeEditar}
              onEdit={setEditando}
              onDelete={handleDelete}
            />
          )}
          <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
            &quot;Instalados&quot; son las máquinas con alta en cliente registrada en Siges
            (instalas reales, no la orden de trabajo). &quot;Listo para STC&quot; avisa cuando ya
            están todos los equipos previstos (o al menos uno si no se cargó cantidad) y la ficha
            sigue esperando instalación — el pase de estado lo hacés vos. Los datos de Siges se
            cachean 5 minutos; &quot;Actualizar Siges&quot; fuerza una consulta nueva.
          </p>
        </>
      )}

      {creando !== false && (
        <ClienteNuevoModal
          ficha={null}
          inicial={creando}
          operadores={operadores}
          onClose={() => setCreando(false)}
          onSaved={() => {
            setCreando(false);
            toast.success("Ficha creada");
            void load();
          }}
        />
      )}
      {editando && (
        <ClienteNuevoModal
          ficha={editando}
          operadores={operadores}
          onClose={() => setEditando(null)}
          onSaved={() => {
            setEditando(null);
            toast.success("Ficha actualizada");
            void load();
          }}
        />
      )}
      {verCandidatos && (
        <ClientesNuevosCandidatosModal
          onClose={() => setVerCandidatos(false)}
          onElegir={handleElegirCandidato}
        />
      )}
    </div>
  );
}
