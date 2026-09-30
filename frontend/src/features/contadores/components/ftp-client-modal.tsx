"use client";

import { useState, type FormEvent, type InputHTMLAttributes } from "react";
import { toast } from "sonner";
import { contadoresApi, type FtpClient } from "../api/contadores-api";
import { useGruposEconomicosFtp } from "../hooks/use-grupos-economicos-ftp";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";

interface Props {
  isOpen: boolean;
  client: FtpClient | null;
  onClose: () => void;
  onSuccess: () => void;
}

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

function Field({ label, id, ...props }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground"
      >
        {label}
      </label>
      <input
        id={id}
        {...props}
        className="rounded-[8px] border border-border px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
      />
    </div>
  );
}

function grupoInicial(client: FtpClient | null): string | null {
  return client?.grupo_economico_id != null
    ? String(client.grupo_economico_id)
    : null;
}

export function FtpClientModal({ isOpen, client, onClose, onSuccess }: Props) {
  const [name, setName] = useState(client?.name ?? "");
  const [grupoId, setGrupoId] = useState<string | null>(grupoInicial(client));
  const { grupos, error: errorGrupos } = useGruposEconomicosFtp(isOpen);
  const [path, setPath] = useState(client?.path || "/");
  const [pattern, setPattern] = useState(
    client?.pattern || "PrinterMonitorClient.db3.*",
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [prevClient, setPrevClient] = useState<FtpClient | null>(client);
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);

  if (isOpen !== prevIsOpen || client !== prevClient) {
    setPrevIsOpen(isOpen);
    setPrevClient(client);
    setName(client?.name ?? "");
    setGrupoId(grupoInicial(client));
    setPath(client?.path || "/");
    setPattern(client?.pattern || "PrinterMonitorClient.db3.*");
    setError(null);
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        name,
        grupo_economico_id: grupoId ? Number(grupoId) : null,
        path,
        pattern,
      };
      if (client) {
        await contadoresApi.updateFtpClient(client.id, payload);
        toast.success("Cliente FTP actualizado correctamente");
      } else {
        await contadoresApi.createFtpClient(payload);
        toast.success("Cliente FTP creado correctamente");
      }
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Error al guardar cliente FTP",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <BrandModal
      isOpen={isOpen}
      onClose={onClose}
      title={client ? "Editar Cliente FTP" : "Nuevo Cliente FTP"}
      widthPx={520}
      error={error ?? errorGrupos}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field
          id="ftp-client-name"
          label="Nombre del Cliente"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ej: CLIENTE CENTRO"
          required
        />

        <SearchableSelect
          label="Grupo económico (Siges)"
          options={grupos.map((g) => ({
            id: String(g.id),
            label: g.descripcion,
            sublabel: g.usuario,
          }))}
          value={grupoId}
          onChange={setGrupoId}
          placeholder="Buscá el grupo económico…"
        />
        <p className="font-body text-xs text-muted-foreground">
          {client && client.grupo_economico_id === null
            ? `Usa credenciales locales (usuario ${client.user} en ${client.host}), pendiente de revisar. Elegí su grupo para pasar a leerlas de Siges.`
            : "Usuario y contraseña FTP se leen de Siges al procesar; no se cargan acá."}
        </p>

        <div className="grid grid-cols-2 gap-3">
          <Field
            id="ftp-client-path"
            label="Directorio Remoto"
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="Ej: /"
            required
          />
          <Field
            id="ftp-client-pattern"
            label="Patrón de Archivos"
            type="text"
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            placeholder="Ej: PrinterMonitorClient.db3.*"
            required
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-[8px] border border-border px-4 py-2 font-body text-sm font-bold text-foreground transition-colors hover:bg-muted"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={loading || (!client && !grupoId)}
            className="rounded-[8px] bg-brand-orange px-4 py-2 font-body text-sm font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:opacity-50"
          >
            {loading ? "Guardando..." : "Guardar"}
          </button>
        </div>
      </form>
    </BrandModal>
  );
}
