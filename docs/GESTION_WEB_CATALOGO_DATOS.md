# gestion.cdsa.com.ar — Catálogo de datos y fuentes alternativas

Relevado el 2026-08-15. Todo acceso fue de solo lectura con el usuario `imartinez`.

---

## 1. Qué es la aplicación

App Symfony (PHP 8.3 / Apache) con Bootstrap 3 + jQuery. No tiene API REST pública — todo es
server-side rendered HTML con algunos endpoints AJAX/JSON para los formularios. El backend ya la
accede vía scraping de sesión (módulo `sla`/planificación, `gestion_session_refresher.py`).

**Dato clave**: gestion.cdsa.com.ar es una UI directa sobre la base de datos Siges/MERCURIO.
El conteo de sucursales activas es idéntico en ambas fuentes (12.455), y una fila real
(id=14554) verificó coincidencia exacta campo por campo. Salvo los tres campos marcados abajo
como "solo Gestión", **todos los datos del módulo Gestión están disponibles en SigesReadOnly
sin necesidad de scraping.**

---

## 2. Módulos accesibles (usuario `imartinez`)

| Módulo | URL | Registros | Fuente Siges equivalente |
|--------|-----|-----------|--------------------------|
| Sucursales | `/sucursal/` | 12.455 activas | `dbo.Sucursal` (VIEW) |
| Empresas | `/empresa/` | 1.092 | `dbo.Empresa` (VIEW) |
| Sectores | `/sector/` | — | `dbo.Sector` |
| Contactos | `/contacto/` | 19.430 | `dbo.Contacto` |
| Centro de Costos | `/centro-costos/` | 9.134 | sin equivalente confirmado |
| Instalas/Desinstalas | `/instalacion/` | 35.286 | `dbo.Incidente` (tipo 103) — no explorado |
| Inclusiones de Contrato | `/inclusion-contrato/` | 1.310 | `dbo.Incidente` (tipo 104) — no explorado |
| Facturas | `/factura` | 2.843 | dominio de facturación — no explorado |
| Órdenes de Trabajo | `/produccion/orden-trabajo` | 9 (activas) | no explorado |

Módulos con acceso 403 (usuario sin permiso): `/contrato/`, `/costo-servicio/`, `/logistica/`.

---

## 3. Mapa de campos: Gestión ↔ Siges

### 3.1 Sucursal

| Campo en Gestión (`/sucursal/{id}`) | Columna en `dbo.Sucursal` | Notas |
|--------------------------------------|--------------------------|-------|
| Nro | `Id_Sucursal` | PK, int |
| Descripción | `descripcion` | varchar |
| Empresa | `Id_Empresa` → `Empresa.Den_Comercial` | |
| Tipo (de empresa) | `Id_Empresa` → `Empresa.ID_Tipo_Empresa` | 101=cliente, 201=CD, 301=proveedor, 401=PST, 402=SPST |
| Distribución | `Distribucion` → `dbo.Distribucion.Descripcion` | FK a transportista (OCA, Andreani, Propio…) |
| Calle / Número / Piso / Dpto | `Domicilio` | un solo varchar desnormalizado |
| Localidad | `Id_Ciudad` → `Ciudad.DesCiudad` | |
| Provincia | `Id_Ciudad` → `Ciudad.DesProvincia` | |
| Código Postal | `Cod_Postal` (también `Ciudad.CodCiudad`) | |
| Observaciones | `Observ` | |
| Teléfono 1 | `Telefono` | |
| Teléfono 2 | `Fax` | En Siges se llama Fax |
| Latitud | `Latitud` | varchar, texto libre |
| Longitud | `Longitud` | varchar, texto libre |
| Preventivo (días) | `TipoPreventivo` → `TipoPreventivo(Tipo,Dias).Dias` | 0/30/60/90/120/180/360 días |
| Opera Feriados | `OperaFeriados` | int (0/1) |
| Opera F. Semana | `OPFS` | int (0/1) |
| Cod. Agrupación | `Cuadricula` | varchar, texto libre — también es la "zona" de preventivos |
| SLA | `sla` | int, horas; `heredaSla`=1 hereda de la empresa |
| Prestador | `ID_Prestador` → `Empresa.Den_Comercial` | |
| Costo Servicios | `IDCostoServicios` → `CostoServicio.descripcion` | zona del tarifario del PST (ej. `TMTB122`) |
| Estado activo/eliminado | `Estado` | **0=activo, 1=inactivo** (invertido respecto intuición) |
| **Sucursal base de atención** | **solo Gestión** | No existe columna en `dbo.Sucursal` |
| **Distancia a base (Kms)** | posible `CostoViaticos` (int) | pendiente confirmar; en Gestión aparece "Sin Calcular" cuando es 0 |
| **Ruta** | **solo Gestión** | Tabla `dbo.Ruta` no existe en Siges; campo aparece vacío en Gestión también |
| **Ubicación** (mapa) | calculado | link de Google Maps generado en frontend a partir de lat/lon |

### 3.2 Empresa

| Campo en Gestión (`/empresa/{id}`) | Columna en `dbo.Empresa` | Notas |
|------------------------------------|--------------------------|-------|
| Razón Social | `razon_social` | |
| Denominación Comercial | `Den_Comercial` | nombre operativo, prefijo `PST ` / `SPST` para prestadores |
| CUIT | `cuit` | |
| Grupo Económico | `ID_GrupoE` → `GrupoEconomico.descripcion` | |
| Tipo | `ID_Tipo_Empresa` | sin tabla catálogo; semántica documentada en §3.1 |
| SLA | `sla` | |
| Operador | sin columna directa | probablemente `UsuariosWebEmpresa`; ver §5 de SIGES_READONLY_CATALOGO_DATOS.md |
| Email de Seguimiento | `EmailSeguimiento` | |
| Observaciones | `Observ` | |
| Estado activo | `Estado` | **0=activo, 1=inactivo** |

### 3.3 Sector

| Campo en Gestión | Columna en `dbo.Sector` |
|------------------|-------------------------|
| Nro | `Id_Sector` |
| Descripción | `descripcion` |
| Empresa | `Id_Empresa` |
| Sucursal | `Id_Sucursal` |
| Observaciones (aviso) | `aviso` |
| Estado | `Estado` (0=activo) |

### 3.4 Contacto

| Campo en Gestión | Columna en `dbo.Contacto` |
|------------------|---------------------------|
| Nombre | `Nombre` |
| Apellido | `Apellido` |
| Empresa | `Id_Empresa` |
| Sucursal | `Id_Sucursal` |
| Sector | `Id_Sector` |
| Cargo / Función | `Cargo` |
| Teléfono | `Telefono` |
| Celular | `Celular` |
| Email | `E_Mail` |
| Responsable | `Responsable` (bit) |
| Estado | `Estado` (0=activo) |

---

## 4. Endpoints AJAX/JSON de la app web

Los únicos endpoints que devuelven JSON (sin Content-Type JSON pero formato válido):

| Endpoint | Qué devuelve | Usado por |
|----------|--------------|-----------|
| `GET /sucursal/ajax-by-id?id={id}` | `[{id, domicilio, localidad, latitud, longitud, centro_costos, contactos:[{id,nombre}]}]` | formularios de instalación |
| `GET /sucursal/empresa-ajax-by-id?id={id}` | `[{id, descripcion}]` lista de sucursales de la misma empresa | formularios |
| `GET /contrato/ajax-by-cliente?id={empresa_id}` | `[{…}]` contratos del cliente (puede ser `[]`) | formulario nueva instalación |
| `GET /contrato-anexo/ajax-by-contrato?id={contrato_id}` | `[{…}]` anexos del contrato | formulario nueva instalación |
| `GET /localidad/ajax-by-provincia?id={provincia_id}` | array de localidades | filtro del listado |
| `GET /provincia/ajax-by-pais?id={pais_id}` | array de provincias | filtro del listado |
| `GET /costo-servicio/ajax-by-prestador` | costos de servicio por prestador | formulario de sucursal |

Nota: todos requieren cookie de sesión activa (`PHPSESSID`). La sesión la mantiene
`gestion_session_refresher.py` en el backend.

---

## 5. Filtros disponibles en `/sucursal/`

Parámetros GET del form `sucursal_filter[*]`:

| Parámetro | Tipo | Valores |
|-----------|------|---------|
| `id` | número | id exacto |
| `descripcion` | texto | búsqueda parcial |
| `tipo_empresa` | enum | `CLI`, `PROVE`, `PREST`, `ORIG` |
| `estado` | enum | `1`=activos (default), `0`=eliminados |
| `provincia` | int | id de provincia (lista completa en la página) |
| `localidad` | int | id de localidad (dependiente de provincia, via AJAX) |
| `calle` | texto | búsqueda parcial |
| `numero_calle` | texto | |

Paginación: `?page=N` (20 registros/página).

---

## 6. Recomendación: usar Siges en vez de scraping

La app web no expone un endpoint de exportación ni una API REST. Las opciones para obtener
los datos masivamente son:

1. **Scraping HTML paginado** — 623 páginas × 20 registros en `/sucursal/?page=N`, más GET
   por id para los campos extra (lat/lon, contactos). Frágil ante cambios de template.

2. **Endpoint AJAX por id** — `GET /sucursal/ajax-by-id?id=X` itera IDs 1..14554 vía sesión.
   Más estructurado que el HTML pero igual de frágil y lento (14k requests).

3. **SigesReadOnly directo (recomendado)** — Una sola consulta SQL a MERCURIO con los joins
   `Sucursal → Empresa → Ciudad → TipoPreventivo` devuelve todos los campos en <1 s.
   Sin dependencia de la app web, sin sesión, sin fraguamiento ante cambios de UI.

```sql
-- Todas las sucursales activas con sus campos de Gestión
SELECT
    S.Id_Sucursal,
    S.descripcion,
    S.Domicilio,
    S.Cod_Postal,
    S.Telefono,
    S.Fax                           AS Telefono2,
    S.Latitud,
    S.Longitud,
    S.OperaFeriados,
    S.OPFS                          AS OperaFinDeSemana,
    S.sla,
    S.heredaSla,
    S.Cuadricula                    AS CodAgrupacion,
    S.IDCostoServicios,
    S.CostoViaticos,
    S.Observ,
    S.Estado,
    TP.Dias                         AS PreventivoDias,
    C.DesCiudad                     AS Localidad,
    C.DesProvincia                  AS Provincia,
    E.Den_Comercial                 AS Empresa,
    E.ID_Tipo_Empresa               AS TipoEmpresa,
    EP.Den_Comercial                AS Prestador
FROM dbo.Sucursal S
JOIN dbo.Ciudad C           ON C.Id_Ciudad    = S.Id_Ciudad
JOIN dbo.Empresa E          ON E.ID_Empresa   = S.Id_Empresa
JOIN dbo.TipoPreventivo TP  ON TP.Tipo        = S.TipoPreventivo
LEFT JOIN dbo.Empresa EP    ON EP.ID_Empresa  = S.ID_Prestador
WHERE S.Estado = 0          -- activas
ORDER BY S.Id_Sucursal DESC;
```

Acceso vía el `MercurioQueryRunner` ya configurado en el backend
(`shared/infrastructure/mercurio/`), misma cuenta `SiGesReadOnly`, mismo patrón que todos
los módulos existentes.

---

## 7. Lo que NO está en Siges

Estos datos solo viven en la app web y no tienen equivalente confirmado en Siges:

- **Sucursal base de atención**: el nombre de la sucursal del PST que atiende a esta
  sucursal. No hay columna en `dbo.Sucursal`. Podría derivarse cruzando el PST
  (`ID_Prestador`) con las sucursales de ese PST en `dbo.Sucursal`.
- **Ruta**: aparece vacío en Gestión también para la mayoría de las sucursales.
  `dbo.Ruta` no existe en Siges (tabla no encontrada).
- **Órdenes de trabajo / Producciones**: 9 registros activos — dominio operativo interno,
  no investigado en Siges.
- **Planificación de eventos** (Calendario `/planificacion/ver`): ya documentado como
  "solo Gestión" en ADR-012 — no existe en Siges.

---

## 8. wsAyC SOAP

Las operaciones conocidas del WS (`https://wsg.cdsisa.com.ar/wsAyC_server.php`) son todas
de insumos e incidentes (detalladas en `docs/INTEGRACIONES_EXTERNAS.md §2`). No expone
operaciones de catálogo de sucursales, empresas ni sectores — no es una fuente útil para
estos datos. La alternativa es exclusivamente SigesReadOnly.
