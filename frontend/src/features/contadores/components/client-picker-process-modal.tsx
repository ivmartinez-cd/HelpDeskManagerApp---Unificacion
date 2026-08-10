"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { ChevronDown, Download, Plus } from "lucide-react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { cn } from "@/shared/utils/cn";
import { contadoresApi } from "../api/contadores-api";
import { ManageMeterClientsModal } from "./manage-meter-clients-modal";
import { ManageFtpClientsModal } from "./manage-ftp-clients-modal";
import { FtpClientModal } from "./ftp-client-modal";

export type PickerClientType = "sds" | "ers" | "ftp";

interface ClientOption {
  id: string;
  name: string;
}

interface TypeConfig {
  title: string;
  clientLabel: string;
  processLabel: string;
  loadErrorMessage: string;
  listClients: () => Promise<ClientOption[]>;
  process: (
    clientId: string,
    clientName: string,
    fechaMaxima: string,
  ) => Promise<{ csv_filename: string; db3_filename?: string }>;
}

const CONFIG: Record<PickerClientType, TypeConfig> = {
  sds: {
    title: "Descargar SDS",
    clientLabel: "Seleccionar cliente SDS",
    processLabel: "Descargar Contadores",
    loadErrorMessage: "Error al cargar clientes HP SDS",
    listClients: contadoresApi.listSdsClients,
    process: (id, name, fecha) =>
      contadoresApi.processSds({ customer_id: id, customer_name: name, fecha_maxima: fecha }),
  },
  ers: {
    title: "Descargar ERS",
    clientLabel: "Seleccionar grupo Epson ERS",
    processLabel: "Descargar Telemetría",
    loadErrorMessage: "Error al cargar grupos Epson ERS",
    listClients: contadoresApi.listErsClients,
    process: (id, name, fecha) =>
      contadoresApi.processErs({ customer_id: id, customer_name: name, fecha_maxima: fecha }),
  },
  ftp: {
    title: "Descarga FTP",
    clientLabel: "Seleccionar cliente FTP",
    processLabel: "Procesar DB3",
    loadErrorMessage: "Error al cargar clientes FTP",
    listClients: contadoresApi.listFtpClients,
    process: (id, _name, fecha) => contadoresApi.processFtpClient(id, fecha),
  },
};

const selectClass =
  "w-full rounded-[10px] border border-black/[0.14] bg-white px-[14px] py-[11px] font-body text-sm text-brand-charcoal outline-none focus:ring-2 focus:ring-brand-orange/40 disabled:opacity-60";

/** Reemplaza al `<select>` nativo: el navegador decide de qué lado abre la
 * lista de opciones según el espacio disponible (y en estos modales elegía
 * hacia arriba, tapando el título), algo que no se puede forzar por CSS en
 * un `<select>` real. Este dropdown siempre despliega hacia abajo. */
function ClientSelect({
  value,
  onChange,
  options,
  loading,
  placeholder,
  ariaLabel,
}: {
  value: string;
  onChange: (id: string) => void;
  options: ClientOption[];
  loading: boolean;
  placeholder: string;
  ariaLabel: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  useEffect(() => {
    if (open) {
      setSearch("");
      // Sin el timeout el foco compite con el que BrandModal le pone al
      // primer elemento enfocable del modal al abrirse.
      const timer = setTimeout(() => searchRef.current?.focus(), 0);
      return () => clearTimeout(timer);
    }
  }, [open]);

  const selected = options.find((o) => o.id === value);
  const filtered = options.filter((o) => o.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div
      ref={containerRef}
      className="relative w-full"
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          e.stopPropagation();
          setOpen(false);
        }
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={loading}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        className={cn(selectClass, "flex items-center justify-between gap-2 text-left")}
      >
        <span className={cn("truncate", !selected && "text-[#a8a8a8]")}>
          {loading ? "Cargando clientes..." : (selected?.name ?? placeholder)}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 flex-none text-[#9a9a9a] transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open && (
        <div className="absolute left-0 right-0 top-[calc(100%+4px)] z-20 flex flex-col overflow-hidden rounded-[10px] border border-black/[0.12] bg-white shadow-lg">
          <div className="border-b border-black/[0.08] p-1.5">
            <input
              ref={searchRef}
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  if (filtered.length === 1) {
                    onChange(filtered[0].id);
                    setOpen(false);
                  }
                }
              }}
              placeholder="Buscar cliente..."
              aria-label={`Buscar en ${ariaLabel}`}
              className="w-full rounded-[6px] border border-black/[0.12] px-2.5 py-1.5 font-body text-sm text-brand-charcoal outline-none focus:ring-2 focus:ring-brand-orange/40"
            />
          </div>
          <ul role="listbox" aria-label={ariaLabel} className="max-h-56 overflow-y-auto thin-scrollbar py-1">
            {filtered.length === 0 ? (
              <li className="px-[14px] py-2 font-body text-sm text-[#9a9a9a]">
                {options.length === 0 ? "Sin clientes disponibles." : "Sin resultados."}
              </li>
            ) : (
              filtered.map((option) => (
                <li key={option.id} role="option" aria-selected={option.id === value}>
                  <button
                    type="button"
                    onClick={() => {
                      onChange(option.id);
                      setOpen(false);
                    }}
                    className={cn(
                      "block w-full truncate px-[14px] py-2 text-left font-body text-sm",
                      option.id === value
                        ? "bg-brand-orange/10 font-semibold text-brand-orange"
                        : "text-brand-charcoal hover:bg-black/[0.03]",
                    )}
                  >
                    {option.name}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

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
              <span className="font-body text-[11px] font-bold uppercase tracking-wide text-[#7a7a7a]">
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
                  className="flex h-10 w-10 flex-none items-center justify-center rounded-full border border-[#c8c8c8] text-[#9a9a9a] hover:border-brand-orange hover:text-brand-orange"
                >
                  <Plus className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <span className="font-body text-[11px] font-bold uppercase tracking-wide text-[#7a7a7a]">
              Fecha máxima de proceso
            </span>
            <input
              type="date"
              value={fechaMaxima}
              onChange={(e) => setFechaMaxima(e.target.value)}
              required
              className="rounded-[10px] border border-black/[0.14] px-[14px] py-[11px] font-body text-[14.5px] text-brand-charcoal outline-none focus:ring-2 focus:ring-brand-orange/40"
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
