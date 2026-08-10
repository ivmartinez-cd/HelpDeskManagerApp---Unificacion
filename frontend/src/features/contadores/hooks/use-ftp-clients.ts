import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { contadoresApi, type FtpClient } from "../api/contadores-api";

function loadErrorMessage(err: unknown) {
  return err instanceof Error ? err.message : "Error al cargar clientes FTP";
}

export function useFtpClients() {
  const [clients, setClients] = useState<FtpClient[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await contadoresApi.listFtpClients();
      setClients(data);
    } catch (err: unknown) {
      toast.error(loadErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    contadoresApi
      .listFtpClients()
      .then((data) => {
        if (active) {
          setClients(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          toast.error(loadErrorMessage(err));
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return { clients, loading, refetch };
}
