import { httpClient } from "@/services/http-client";

export interface NotaWire {
  content: string;
  updatedAt: string | null;
  maxChars: number;
}

/** Nota personal de Inicio (`/api/me/nota`, ADR-033): una por usuario,
 * privada; el `user_id` sale de la sesión. */
export const notaApi = {
  get: (): Promise<NotaWire> => httpClient.get<NotaWire>("/api/me/nota"),
  put: (content: string): Promise<NotaWire> => httpClient.put<NotaWire>("/api/me/nota", { content }),
};
