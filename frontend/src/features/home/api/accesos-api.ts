import { httpClient } from "@/services/http-client";

interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

interface RouteVisitWire {
  route: string;
  moduleKey: string;
  visits: number;
  lastVisit: string;
}

export const accesosApi = {
  recordVisit: (route: string): Promise<void> =>
    httpClient.post<void>("/api/me/route-visits", { route }),
  getTopRoutes: (size = 6): Promise<string[]> =>
    httpClient
      .get<Page<RouteVisitWire>>(`/api/me/route-visits/top?size=${size}`)
      .then((p) => p.items.map((i) => i.route)),
};
