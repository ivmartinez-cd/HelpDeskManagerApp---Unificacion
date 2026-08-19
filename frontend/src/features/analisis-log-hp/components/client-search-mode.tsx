"use client";

import { Loader2, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import type { ClientDevice, FleetClient } from "../types/analisis-log-hp";

interface Props {
  loading: boolean;
  onAnalyze: (serial: string) => void;
}

/** Búsqueda por cliente: cliente → equipo del cliente → dispara el mismo análisis por serie. */
export function ClientSearchMode({ loading, onAnalyze }: Props) {
  const [clients, setClients] = useState<FleetClient[] | null>(null);
  const [clientsError, setClientsError] = useState<string | null>(null);
  const [selectedClient, setSelectedClient] = useState("");
  const [devices, setDevices] = useState<ClientDevice[] | null>(null);
  const [selectedSerial, setSelectedSerial] = useState("");
  const devicesLoading = Boolean(selectedClient) && devices === null;

  useEffect(() => {
    let cancelled = false;
    analisisLogHpApi.listClients()
      .then((data) => { if (!cancelled) setClients(data); })
      .catch(() => { if (!cancelled) setClientsError("No se pudo cargar la lista de clientes."); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!selectedClient) return;
    let cancelled = false;
    analisisLogHpApi.getClientDevices(Number(selectedClient))
      .then((data) => { if (!cancelled) setDevices(data); })
      .catch(() => { if (!cancelled) setDevices([]); });
    return () => { cancelled = true; };
  }, [selectedClient]);

  function handleClientChange(value: string) {
    setSelectedClient(value);
    setDevices(null);
    setSelectedSerial("");
  }

  return (
    <div className="w-full flex flex-col gap-3">
      <select
        value={selectedClient}
        onChange={(e) => handleClientChange(e.target.value)}
        disabled={loading || !clients}
        className="w-full rounded-[10px] border border-border bg-card px-4 py-3 font-body text-sm text-foreground focus:border-brand-orange/60 focus:outline-none"
      >
        <option value="">{clients ? "Seleccioná un cliente..." : "Cargando clientes..."}</option>
        {clients?.map((c) => (
          <option key={c.customer_id} value={c.customer_id}>
            {c.name} ({c.device_count} equipos)
          </option>
        ))}
      </select>

      {clientsError && <p className="font-body text-[12px] text-destructive">{clientsError}</p>}

      {selectedClient && (
        <select
          value={selectedSerial}
          onChange={(e) => setSelectedSerial(e.target.value)}
          disabled={loading || devicesLoading}
          className="w-full rounded-[10px] border border-border bg-card px-4 py-3 font-body text-sm text-foreground focus:border-brand-orange/60 focus:outline-none"
        >
          <option value="">
            {devicesLoading ? "Cargando equipos..." : devices?.length ? "Seleccioná un equipo..." : "Sin equipos para este cliente"}
          </option>
          {devices?.map((d) => (
            <option key={d.device_id} value={d.serial}>
              {d.serial}{d.location ? ` - ${d.location}` : ""}{d.model ? ` (${d.model})` : ""}
            </option>
          ))}
        </select>
      )}

      <button
        type="button"
        onClick={() => onAnalyze(selectedSerial)}
        disabled={loading || !selectedSerial}
        className="flex items-center justify-center gap-2 rounded-[10px] bg-brand-orange px-5 py-3 font-body text-sm font-bold text-white hover:bg-brand-orange/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
        Analizar
      </button>
    </div>
  );
}
