"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import {
  contadoresApi,
  type CreateFtpClientPayload,
  type FtpClient,
} from "../api/contadores-api";
import { Modal } from "@/shared/components/ui/modal";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";

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
  const [error, setError] = useState<string | null>(null);

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
    setError(null);
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

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
      setError(err instanceof Error ? err.message : "Error al guardar cliente FTP");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={client ? "Editar Cliente FTP" : "Nuevo Cliente FTP"}
      maxWidth="max-w-lg"
      error={error}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="ftp-client-name"
          label="Nombre del Cliente"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ej: CLIENTE CENTRO"
          required
        />

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="sm:col-span-2">
            <Input
              id="ftp-client-host"
              label="Servidor (Host / IP)"
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="Ej: ftp.cliente.com.ar"
              required
            />
          </div>
          <Input
            id="ftp-client-port"
            label="Puerto"
            type="number"
            value={port}
            onChange={(e) => setPort(Number(e.target.value))}
            required
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <Input
            id="ftp-client-username"
            label="Usuario FTP"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <Input
            id="ftp-client-password"
            label={`Contraseña ${client ? "(Dejar en blanco para conservar)" : ""}`}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required={!client}
          />
        </div>

        <Input
          id="ftp-client-remote-dir"
          label="Directorio Remoto"
          type="text"
          value={remoteDir}
          onChange={(e) => setRemoteDir(e.target.value)}
          placeholder="Ej: /"
          required
        />

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" loading={loading}>
            Guardar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
