"use client";

import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Download, Plus } from "lucide-react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { contadoresApi } from "../api/contadores-api";
import { CONFIG, type ClientOption, type PickerClientType } from "./client-picker-config";
import { ClientSelect } from "./client-select";
import { ManageMeterClientsModal } from "./manage-meter-clients-modal";
import { ManageFtpClientsModal } from "./manage-ftp-clients-modal";
import { FtpClientModal } from "./ftp-client-modal";

export type { PickerClientType } from "./client-picker-config";

interface Props {
  isOpen: boolean;
  type: PickerClientType;
  onClose: () => void;
}

/** Modal combinado "elegir un cliente + fecha + procesar" para SDS/ERS/FTP,
 * tal como lo muestra el design handoff (a diferencia del mock, acá el
 * selector es real: carga los clientes de la API real). El link "Gestionar
 * clientes" abre un segundo modal con la lista completa (ver
 * manage-meter-clients-modal.tsx / manage-ftp-clients-modal.tsx). */
export function ClientPickerProcessModal({ isOpen, type, onClose }: Props) {
  const config = CONFIG[type];
  const [clients, setClients] = useState<ClientOption[]>([]);
  const [loadingClients, setLoadingClients] = useState(true);
  const [selectedId, setSelectedId] = useState("");
  const [fechaMaxima, setFechaMaxima] = useState(new Date().toISOString().split("T")[0]);
  const [submitting, setSubmitting] = useState(false);
  const [generatedCsv, setGeneratedCsv] = useState<string | null>(null);
  const [generatedDb3, setGeneratedDb3] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [manageOpen, setManageOpen] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);

  const loadClients = () => {
    setLoadingClients(true);
    config
      .listClients()
      .then((data) => setClients(data))
      .catch((err: unknown) => {
        toast.error(err instanceof Error ? err.message : config.loadErrorMessage);
      })
      .finally(() => setLoadingClients(false));
  };

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    config
      .listClients()
      .then((data) => {
        if (active) setClients(data);
      })
      .catch((err: unknown) => {
        if (active) toast.error(err instanceof Error ? err.message : config.loadErrorMessage);
      })
      .finally(() => {
        if (active) setLoadingClients(false);
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const client = clients.find((c) => c.id === selectedId);
    if (!client) {
      setError("Elegí un cliente antes de continuar");
      return;
    }

    setSubmitting(true);
    setGeneratedCsv(null);
    setGeneratedDb3(null);
    setError(null);

    try {
      const res = await config.process(client.id, client.name, fechaMaxima);
      setGeneratedCsv(res.csv_filename);
      setGeneratedDb3(res.db3_filename ?? null);
      toast.success(`${config.title} procesado exitosamente`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al procesar");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <BrandModal isOpen={isOpen} onClose={onClose} title={config.title} widthPx={420} error={error}>
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                {config.clientLabel}
              </span>
              <button
                type="button"
                onClick={() => setManageOpen(true)}
                className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:text-brand-orange-hover"
              >
                Gestionar clientes
              </button>
            </div>
            <div className="flex items-center gap-2">
              <ClientSelect
                value={selectedId}
                onChange={setSelectedId}
                options={clients}
                loading={loadingClients}
                placeholder="Selecciona un cliente..."
                ariaLabel={config.clientLabel}
              />
              {type === "ftp" && (
                <button
                  type="button"
                  onClick={() => setQuickAddOpen(true)}
                  aria-label="Nuevo cliente FTP"
                  title="Nuevo cliente FTP"
                  className="flex h-10 w-10 flex-none items-center justify-center rounded-full border border-border text-muted-foreground hover:border-brand-orange hover:text-brand-orange"
                >
                  <Plus className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Fecha máxima de proceso
            </span>
            <input
              type="date"
              value={fechaMaxima}
              onChange={(e) => setFechaMaxima(e.target.value)}
              required
              className="rounded-[10px] border border-border px-[14px] py-[11px] font-body text-[14.5px] text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
            />
          </div>

          {generatedCsv && (
            <div className="flex flex-col gap-2 rounded-[10px] border border-brand-orange/20 bg-brand-orange/5 p-3">
              <p className="font-body text-xs font-semibold text-brand-orange">
                {generatedDb3 ? "Archivos generados:" : "Archivo CSV generado:"}
              </p>
              <a
                href={contadoresApi.getOutputUrl(generatedCsv)}
                download={generatedCsv}
                className="inline-flex items-center justify-center gap-2 rounded-[8px] bg-brand-orange px-4 py-2 font-body text-sm font-bold text-white transition-colors hover:bg-brand-orange-hover"
              >
                <Download className="h-4 w-4" />
                Descargar {generatedCsv}
              </a>
              {generatedDb3 && (
                <a
                  href={contadoresApi.getOutputUrl(generatedDb3)}
                  download={generatedDb3}
                  className="inline-flex items-center justify-center gap-2 rounded-[8px] border border-brand-orange px-4 py-2 font-body text-sm font-bold text-brand-orange transition-colors hover:bg-brand-orange/10"
                >
                  <Download className="h-4 w-4" />
                  Descargar {generatedDb3}
                </a>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting || loadingClients}
            className="flex items-center justify-center gap-2 rounded-[10px] bg-brand-orange px-4 py-[13px] font-body text-[15px] font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {submitting ? "Procesando..." : config.processLabel}
          </button>
        </form>
      </BrandModal>

      {type === "ftp" ? (
        <ManageFtpClientsModal isOpen={manageOpen} onClose={() => setManageOpen(false)} />
      ) : (
        <ManageMeterClientsModal
          isOpen={manageOpen}
          type={type}
          onClose={() => setManageOpen(false)}
        />
      )}

      {type === "ftp" && (
        <FtpClientModal
          isOpen={quickAddOpen}
          client={null}
          onClose={() => setQuickAddOpen(false)}
          onSuccess={loadClients}
        />
      )}
    </>
  );
}
