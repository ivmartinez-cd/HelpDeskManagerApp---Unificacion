"use client";

import { useCallback, useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { ReglaAlerta } from "../types/liquidaciones";

export function useReglasAlerta() {
  const [reglas, setReglas] = useState<ReglaAlerta[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      setReglas(await liquidacionesApi.listReglasAlerta());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);

  return { reglas, loading, refetch };
}
