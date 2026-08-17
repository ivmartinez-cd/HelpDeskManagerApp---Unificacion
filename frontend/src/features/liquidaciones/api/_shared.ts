import { httpClient } from "@/services/http-client";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

// Tope de `size` que acepta el backend (Query le=1000 en config_routers).
const CATALOGO_SIZE_MAX = 1000;

// Los catálogos por prestador pueden superar incluso el tope de una página
// (INFOMAC: 960 tarifas y creciendo) — se piden páginas hasta cubrir `total`
// en vez de truncar en silencio al default de 500.
export async function fetchCatalogoCompleto<T>(
  path: string,
  params: URLSearchParams,
): Promise<T[]> {
  params.set("size", String(CATALOGO_SIZE_MAX));
  params.set("page", "1");
  const primera = await httpClient.get<Page<T>>(`${path}?${params}`);
  const items = [...primera.items];
  for (let page = 2; items.length < primera.total; page++) {
    params.set("page", String(page));
    const siguiente = await httpClient.get<Page<T>>(`${path}?${params}`);
    if (siguiente.items.length === 0) break;
    items.push(...siguiente.items);
  }
  return items;
}
