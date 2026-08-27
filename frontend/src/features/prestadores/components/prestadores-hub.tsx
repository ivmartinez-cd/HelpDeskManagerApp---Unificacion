"use client";

import { useMemo, useState } from "react";
import { RefreshCw, Wrench } from "lucide-react";
import { usePrestadoresHub } from "../hooks/use-prestadores-hub";
import { PrestadorDetailModal } from "./prestador-detail-modal";
import { PrestadorFormModal } from "./prestador-form-modal";
import { PrestadorGroupSection } from "./prestador-group-section";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandEmptyState, BrandInput, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { Spinner } from "@/shared/components/ui/spinner";

export function PrestadoresHub() {
  const { user, can } = useSession();
  const canEdit = user.isSuperadmin || can("prestadores", "update");
  const canCreate = user.isSuperadmin || can("prestadores", "create");
  const canDelete = user.isSuperadmin || can("prestadores", "delete");

  const {
    resumen,
    operadores,
    loading,
    error,
    syncing,
    syncMessage,
    search,
    setSearch,
    gruposFiltrados,
    handleSync,
    reload,
  } = usePrestadoresHub();
  const [creating, setCreating] = useState(false);
  const [viewingId, setViewingId] = useState<string | null>(null);

  const prestadorViendo = useMemo(() => {
    if (!viewingId || !resumen) return null;
    for (const grupo of resumen.grupos) {
      const found = grupo.prestadores.find((p) => p.id === viewingId);
      if (found) return found;
    }
    return null;
  }, [viewingId, resumen]);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">
            Prestadores de Servicio Técnico
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Directorio de PST agrupados por operador asignado.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="flex gap-2">
            <BrandButton variant="outline" loading={syncing} onClick={handleSync}>
              <RefreshCw className="h-4 w-4" />
              Sincronizar
            </BrandButton>
            {canCreate && (
              <BrandButton onClick={() => setCreating(true)}>
                <Wrench className="h-4 w-4" />
                Nuevo PST
              </BrandButton>
            )}
          </div>
          {syncMessage && (
            <span className="font-body text-[11px] text-muted-foreground">{syncMessage}</span>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {!loading && !error && resumen && (
        <div className="flex flex-col gap-6">
          <KpiGrid>
            <KpiTile label="Total PST" value={String(resumen.totalPrestadores)} tone="neutral" />
            <KpiTile label="Operadores activos" value={String(resumen.operadoresConPst)} tone="orange" />
            <KpiTile label="Sin asignar" value={String(resumen.sinAsignar)} tone="neutral" />
          </KpiGrid>

          <BrandInput
            label="Buscar"
            placeholder="Razón social o nombre comercial..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          {gruposFiltrados.length === 0 ? (
            <BrandEmptyState icon={Wrench} title="Sin resultados" description="No hay PST que coincidan con la búsqueda." />
          ) : (
            <div className="flex flex-col gap-4">
              {gruposFiltrados.map((grupo) => (
                <PrestadorGroupSection
                  key={grupo.operadorId ?? "sin-asignar"}
                  grupo={grupo}
                  onVer={setViewingId}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {syncing && !resumen && <BrandSkeleton className="h-40 w-full" />}

      {creating && (
        <PrestadorFormModal
          prestador={null}
          operadores={operadores}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            void reload();
          }}
        />
      )}

      {prestadorViendo && (
        <PrestadorDetailModal
          prestador={prestadorViendo}
          operadores={operadores}
          canEdit={canEdit}
          canDelete={canDelete}
          onClose={() => setViewingId(null)}
          onChanged={() => void reload()}
        />
      )}
    </div>
  );
}
