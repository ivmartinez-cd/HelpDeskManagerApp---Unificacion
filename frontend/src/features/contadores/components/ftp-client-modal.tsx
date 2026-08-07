"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Loader2, X } from "lucide-react";
import {
  contadoresApi,
  type CreateFtpClientPayload,
  type FtpClient,
} from "../api/contadores-api";

interface Props {
  isOpen: boolean;
  client: FtpClient | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function FtpClientModal({ isOpen, client, onClose, onSuccess }: Props) {
  const [name, setName] = useState(client?.name ?? "");
  const [host, setHost] = useState(client?.host ?? "");
  const [port, setPort] = useState<number>(client?.port || 21);
  const [username, setUsername] = useState(client?.username ?? "");
  const [password, setPassword] = useState("");
  const [remoteDir, setRemoteDir] = useState(client?.remote_dir || "/");
  const [loading, setLoading] = useState(false);

  const [prevClient, setPrevClient] = useState<FtpClient | null>(client);
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);

  if (isOpen !== prevIsOpen || client !== prevClient) {
    setPrevIsOpen(isOpen);
    setPrevClient(client);
    setName(client?.name ?? "");
    setHost(client?.host ?? "");
    setPort(client?.port || 21);
    setUsername(client?.username ?? "");
    setPassword("");
    setRemoteDir(client?.remote_dir || "/");
  }

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (client) {
        await contadoresApi.updateFtpClient(client.id, {
          name,
          host,
          port,
          username,
          password: password || undefined,
          remote_dir: remoteDir,
        });
        toast.success("Cliente FTP actualizado correctamente");
      } else {
        const payload: CreateFtpClientPayload = {
          name,
          host,
          port,
          username,
          password,
          remote_dir: remoteDir,
        };
        await contadoresApi.createFtpClient(payload);
        toast.success("Cliente FTP creado correctamente");
      }
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al guardar cliente FTP";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="text-lg font-bold text-foreground">
            {client ? "Editar Cliente FTP" : "Nuevo Cliente FTP"}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Nombre del Cliente
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej: CLIENTE CENTRO"
              className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
              required
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Servidor (Host / IP)
              </label>
              <input
                type="text"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="Ej: ftp.cliente.com.ar"
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Puerto
              </label>
              <input
                type="number"
                value={port}
                onChange={(e) => setPort(Number(e.target.value))}
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
                required
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Usuario FTP
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Contraseña {client && "(Dejar en blanco para conservar)"}
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
                required={!client}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Directorio Remoto
            </label>
            <input
              type="text"
              value={remoteDir}
              onChange={(e) => setRemoteDir(e.target.value)}
              placeholder="Ej: /"
              className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-semibold text-muted-foreground hover:bg-muted"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2 text-xs font-bold text-primary-foreground shadow-md hover:bg-primary/90 disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Guardar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
