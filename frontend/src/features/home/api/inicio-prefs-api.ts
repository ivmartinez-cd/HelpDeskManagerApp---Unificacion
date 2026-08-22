import { httpClient } from "@/services/http-client";

export interface InicioPrefsWire {
  hiddenCards: string[];
  initialView: string;
}

/** Preferencias de Inicio del usuario logueado (`/api/me/inicio-prefs`,
 * ADR-033): el backend las guarda por cuenta, el `user_id` sale de la sesión. */
export const inicioPrefsApi = {
  get: (): Promise<InicioPrefsWire> => httpClient.get<InicioPrefsWire>("/api/me/inicio-prefs"),
  put: (prefs: InicioPrefsWire): Promise<InicioPrefsWire> =>
    httpClient.put<InicioPrefsWire>("/api/me/inicio-prefs", prefs),
};
