"use client";

import { Handshake } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandEmptyState } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { formatARS } from "../lib/format";
import type { AcuerdoPrecioCliente, PrestadorLiquidacion } from "../types/liquidaciones";
import { AcuerdoModal, type PlantillaAcuerdo } from "./acuerdo-modal";

const thCls = "px-4 py-2 text-left font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground";
const tdCls = "px-4 py-2 font-body text-sm text-foreground";

function precioLabel(a: AcuerdoPrecioCliente): string {
  if (a.precioFijo !== null) return `${formatARS(a.precioFijo)} fijo`;
  return `×${a.factor} del tarifario`;
}

export function AcuerdosConfig({
  deepLink = null,
}: {
  /** Llega desde una alerta ALT001 del detalle: precarga prestador + alta con
   * el cliente, tipo y precio cobrado ya completos. */
  deepLink?: { prestadorId: string; empresaNombre: string; tipoServicio: string; cobrado: string } | null;
} = {}) {
  const { can } = useSession();
  const puedeEditar = can("liquidaciones", "update");
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loadingPrestadores, setLoadingPrestadores] = useState(true);
  const [filtroPst, setFiltroPst] = useState(() => deepLink?.prestadorId ?? "");
  const [acuerdos, setAcuerdos] = useState<AcuerdoPrecioCliente[]>([]);
  const [acuerdosPstId, setAcuerdosPstId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(() => deepLink !== null);
  const [editing, setEditing] = useState<AcuerdoPrecioCliente | null>(null);
  const [plantilla, setPlantilla] = useState<PlantillaAcuerdo | null>(() =>
    deepLink
      ? { empresaNombre: deepLink.empresaNombre, tipoServicio: deepLink.tipoServicio, precioFijo: deepLink.cobrado }
      : null,
  );
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    void liquidacionesApi.listPrestadores(false)
      .then(setPrestadores)
      .finally(() => setLoadingPrestadores(false));
  }, []);

  const loadAcuerdos = useCallback(async () => {
    if (!filtroPst) return;
    try {
      setAcuerdos(await liquidacionesApi.listAcuerdos(filtroPst));
    } finally {
      setAcuerdosPstId(filtroPst);
    }
  }, [filtroPst]);

  useEffect(() => { void loadAcuerdos(); }, [loadAcuerdos]);

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await liquidacionesApi.deleteAcuerdo(deletingId);
      toast.success("Acuerdo eliminado — las liquidaciones abiertas se reanalizaron");
      setDeletingId(null);
      void loadAcuerdos();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const abrirModal = (a: AcuerdoPrecioCliente | null) => { setEditing(a); setPlantilla(null); setModalOpen(true); };
  const pstSeleccionado = prestadores.find((p) => p.id === filtroPst) ?? null;
  const loading = filtroPst !== "" && filtroPst !== acuerdosPstId;
  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-xl font-extrabold text-foreground">Acuerdos de precio por cliente</h1>
          <p className="font-body text-sm text-muted-foreground">
            Precios pactados con un cliente puntual que se apartan del tarifario. El motor los toma como
            el precio esperado: solo alerta si el prestador cobra algo distinto a lo acordado.
          </p>
        </div>
        {puedeEditar && <BrandButton size="sm" disabled={!filtroPst} onClick={() => abrirModal(null)}>+ Nuevo acuerdo</BrandButton>}
      </div>

      <select value={filtroPst} onChange={(e) => setFiltroPst(e.target.value)} className={`${selectCls} w-fit`} aria-label="Filtrar por prestador" disabled={loadingPrestadores}>
        <option value="">Seleccioná un prestador...</option>
        {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto}</option>)}
      </select>

      {!filtroPst ? (
        <BrandEmptyState icon={Handshake} title="Ningún prestador seleccionado" description="Elegí un prestador arriba para ver sus acuerdos." />
      ) : loading ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : acuerdos.length === 0 ? (
        <BrandEmptyState icon={Handshake} title={`${pstSeleccionado?.nombreCorto} no tiene acuerdos`} description="Usá '+ Nuevo acuerdo', o el atajo 'Cargar acuerdo' desde una alerta de precio." />
      ) : (
        <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
          <table className="w-full">
            <thead className="border-b border-border">
              <tr>
                <th className={thCls}>Cliente</th>
                <th className={thCls}>Tipo</th>
                <th className={thCls}>Precio acordado</th>
                <th className={thCls}>Motivo</th>
                <th className={thCls}>Vigencia</th>
                <th className={thCls}></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {acuerdos.map((a) => (
                <tr key={a.id}>
                  <td className={`${tdCls} font-semibold`}>{a.empresaNombre}</td>
                  <td className={tdCls}>{a.tipoServicio ?? "Todos"}</td>
                  <td className={`${tdCls} tabular-nums`}>{precioLabel(a)}</td>
                  <td className={`${tdCls} text-muted-foreground`}>{a.motivo}</td>
                  <td className={`${tdCls} tabular-nums`}>{a.vigenciaDesde}{a.vigenciaHasta ? ` → ${a.vigenciaHasta}` : " → vigente"}</td>
                  <td className={`${tdCls} text-right`}>
                    {puedeEditar && (
                      <>
                        <button onClick={() => abrirModal(a)} className="font-body text-xs text-brand-orange hover:underline">Editar</button>
                        <button onClick={() => setDeletingId(a.id)} className="ml-3 font-body text-xs text-muted-foreground hover:text-destructive">Eliminar</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AcuerdoModal key={editing?.id ?? (plantilla ? `plantilla:${Object.values(plantilla).join("::")}` : "nuevo")} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); setPlantilla(null); }} prestadores={prestadores} editing={editing} plantilla={plantilla} defaultPrestadorId={filtroPst} onSuccess={loadAcuerdos} />
      <BrandModal isOpen={!!deletingId} onClose={() => setDeletingId(null)} title="Eliminar acuerdo">
        <p className="font-body text-sm text-muted-foreground mb-5">Las liquidaciones abiertas de este prestador se van a reanalizar contra el tarifario. ¿Confirmás?</p>
        <div className="flex justify-end gap-3">
          <BrandButton variant="outline" onClick={() => setDeletingId(null)}>Cancelar</BrandButton>
          <BrandButton onClick={handleDelete}>Sí, eliminar</BrandButton>
        </div>
      </BrandModal>
    </div>
  );
}
