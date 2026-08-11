"use client";

import { useState, type FormEvent, type InputHTMLAttributes } from "react";
import { toast } from "sonner";
import {
  contadoresApi,
  type CreateFtpClientPayload,
  type FtpClient,
  type UpdateFtpClientPayload,
} from "../api/contadores-api";
import { BrandModal } from "@/shared/components/ui/brand-modal";

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

export function FtpClientModal({ isOpen, client, onClose, onSuccess }: Props) {
  const [name, setName] = useState(client?.name ?? "");
  const [host, setHost] = useState(client?.host ?? "");
  const [user, setUser] = useState(client?.user ?? "");
  const [password, setPassword] = useState("");
  const [path, setPath] = useState(client?.path || "/");
  const [pattern, setPattern] = useState(client?.pattern || "PrinterMonitorClient.db3.*");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [prevClient, setPrevClient] = useState<FtpClient | null>(client);
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);

  if (isOpen !== prevIsOpen || client !== prevClient) {
    setPrevIsOpen(isOpen);
    setPrevClient(client);
    setName(client?.name ?? "");
    setHost(client?.host ?? "");
    setUser(client?.user ?? "");
    setPassword("");
    setPath(client?.path || "/");
    setPattern(client?.pattern || "PrinterMonitorClient.db3.*");
    setError(null);
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (client) {
        // password vacío = "conservar la actual" (ver UpdateFtpClientPayload).
        const payload: UpdateFtpClientPayload = { name, host, user, path, pattern };
        if (password) payload.password = password;
        await contadoresApi.updateFtpClient(client.id, payload);
        toast.success("Cliente FTP actualizado correctamente");
      } else {
        const payload: CreateFtpClientPayload = { name, host, user, password, path, pattern };
        await contadoresApi.createFtpClient(payload);
        toast.success("Cliente FTP creado correctamente");
      }
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar cliente FTP");
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
      error={error}
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

        <Field
          id="ftp-client-host"
          label="Servidor (Host / IP)"
          type="text"
          value={host}
          onChange={(e) => setHost(e.target.value)}
          placeholder="Ej: ftp.cliente.com.ar"
          required
        />

        <div className="grid grid-cols-2 gap-3">
          <Field
            id="ftp-client-user"
            label="Usuario FTP"
            type="text"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            required
          />
          <Field
            id="ftp-client-password"
            label={`Contraseña ${client ? "(dejar en blanco para conservar)" : ""}`}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required={!client}
          />
        </div>

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
            disabled={loading}
            className="rounded-[8px] bg-brand-orange px-4 py-2 font-body text-sm font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:opacity-50"
          >
            {loading ? "Guardando..." : "Guardar"}
          </button>
        </div>
      </form>
    </BrandModal>
  );
}
