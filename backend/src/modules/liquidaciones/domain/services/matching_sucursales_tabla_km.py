"""Matching de sucursales de Tabla KM ↔ Siges, niveles N1/N2 (Fase 1 del plan
de matching sucursales + geovalidación, medido sobre SAN JUAN 2026-08-19 —
ver docs/liquidaciones/MATCHING_SUCURSALES_TABLA_KM.md).

N0 (existente, sin cambios): igualdad exacta con `normalizar_nombre` — la usa
`RefrescarDatosSiges`. N1 (acá): igualdad exacta con `normalizar_nombre_fuerte`,
que además unifica símbolo de número (Nº/N°/N.º/Nro → "n"), siglas con puntos
(E.N.I./EEE/E.P.E.T.) y abreviaturas de palabra frecuentes en el dataset real
(Secundaria/Superior/Provincia/Nacional/Primaria/República/Presidente/Técnica/
General/Escuela). Aprobado para auto-vínculo (decisión 0.4.a). N2 (acá):
comparador difuso con score compuesto — SIEMPRE requiere confirmación humana,
nunca auto-vincula (regla de negocio explícita, no ambigua).
"""

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal
from uuid import UUID

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)

NivelMatch = Literal["N1", "N2"]

# Mismo prefijo que `vinculacion_siges.normalizar_nombre` (ADR-014) — duplicado
# a propósito en vez de importar el símbolo privado del otro módulo.
_PREFIJOS = ("spst", "pst", "pr")

# Reglas de símbolo/sigla: tienen que correr sobre el texto CRUDO, antes de
# NFKD — NFKD ya descompone 'º' (U+00BA) a la letra suelta 'o' (a diferencia
# de '°' U+00B0 signo de grado, que no se descompone), así que si corrieran
# después ya no podrían distinguir "Nº" de una "N" seguida de letra 'o' real.
_REGLAS_SIMBOLO: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(patron, re.IGNORECASE), reemplazo)
    for patron, reemplazo in (
        # Siglas institucionales con puntos ("E.N.I." → "ENI"): el paso de
        # puntuación→espacio de normalizar_nombre las tokeniza letra por letra
        # y por eso nunca igualan a la forma plana que usa Siges.
        (r"\bE\.\s*N\.\s*I\.?", "ENI"),
        (r"\bE\.\s*E\.\s*E\.?", "EEE"),
        (r"\bE\.\s*P\.\s*E\.\s*T\.?", "EPET"),
        # Símbolo/puntuación del número de sucursal: Nº(U+00BA)/N°(U+00B0
        # signo de grado)/N.º/Nro/Nro. — bug confirmado en datos reales
        # (JINZ N°41 vs JINZ N.º 41 son la misma sucursal).
        (r"\bNro\.?\s*(?=\d)", "N "),
        (r"\bN\.?\s*[°º]?\.?\s*(?=\d)", "N "),
    )
)

# Abreviaturas de palabra observadas repetidas veces en la muestra SAN JUAN
# (Fase 0.2) — corren DESPUÉS de sacar acentos, sobre texto ya plano.
_REGLAS_ABREVIATURA: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(patron, re.IGNORECASE), reemplazo)
    for patron, reemplazo in (
        (r"\bProvincia\b", "Pcia"),
        (r"\bProvincial\b", "Pcia"),
        (r"\bProv\b", "Pcia"),
        (r"\bSecundaria\b", "Sec"),
        (r"\bSuperior\b", "Sup"),
        (r"\bNacional\b", "Nac"),
        (r"\bPrimaria\b", "Prim"),
        (r"\bRepublica\b", "Rep"),
        (r"\bPresidente\b", "Pte"),
        (r"\bTecnica\b", "Tec"),
        (r"\bGeneral\b", "Gral"),
        (r"\bEscuela\b", "Esc"),
    )
)

_RE_NUMERO = re.compile(r"\bn\s+(\d+)\b")


def normalizar_nombre_fuerte(nombre: str) -> str:
    """N1: como `normalizar_nombre` pero NFKD (mapea º/ª a letra ASCII, a
    diferencia de la NFD de `normalizar_nombre` — ahí está el bug del º) más
    la tabla de equivalencias de siglas/abreviaturas de arriba."""
    sin_simbolos = nombre
    for patron, reemplazo in _REGLAS_SIMBOLO:
        sin_simbolos = patron.sub(reemplazo, sin_simbolos)
    sin_compat = unicodedata.normalize("NFKD", sin_simbolos)
    sin_acentos = "".join(ch for ch in sin_compat if not unicodedata.combining(ch))
    for patron, reemplazo in _REGLAS_ABREVIATURA:
        sin_acentos = patron.sub(reemplazo, sin_acentos)
    alfanumerico = "".join(ch if ch.isalnum() else " " for ch in sin_acentos.lower())
    tokens = alfanumerico.split()
    if tokens and tokens[0] in _PREFIJOS:
        tokens = tokens[1:]
    return " ".join(tokens)


def _numero_sucursal(nombre_fuerte: str) -> str | None:
    """Número de sucursal ya aislado como token propio tras la regla de
    símbolo (ej. 'eni n 60' → '60'). Sirve de ancla fuerte del comparador N2:
    si dos sucursales declaran números distintos, NUNCA son la misma."""
    m = _RE_NUMERO.search(nombre_fuerte)
    return m.group(1).lstrip("0") or "0" if m else None


def _score(local_fuerte: str, siges_fuerte: str) -> float:
    """Promedio de similitud de secuencia (difflib) y solapamiento de tokens
    (Jaccard) — el ratio de secuencia solo no separa bien falsos positivos de
    nombre propio parecido (medido en Fase 0.3: casos reales con ratio 0.85-
    0.92 que eran personas distintas)."""
    ratio_secuencia = SequenceMatcher(
        None, local_fuerte.replace(" ", ""), siges_fuerte.replace(" ", "")
    ).ratio()
    tokens_local = set(local_fuerte.split())
    tokens_siges = set(siges_fuerte.split())
    union = tokens_local | tokens_siges
    jaccard = len(tokens_local & tokens_siges) / len(union) if union else 0.0
    return (ratio_secuencia + jaccard) / 2


# Calibrado en Fase 0.3 sobre las 151 filas sin match reales de SAN JUAN. N2
# NUNCA auto-vincula (decisión de negocio) — el costo de un falso positivo acá
# es que el operador lo descarta con un vistazo (el motivo ya explicita qué
# difiere), mientras que el costo de dejar la fila sin ningún candidato es
# obligar a buscarla a mano en Siges. Por eso el umbral prioriza recall: 0.45
# capturó casos reales correctos (ej. 'Escuela Sec. Dr. Juan Carlos Navarro'
# ↔ 'Escuela Dr. J. C. Navarro', score 0.49) que 0.55 dejaba afuera.
UMBRAL_N2 = 0.45
TOP_N_CANDIDATOS = 3


@dataclass(frozen=True)
class FilaSinMatch:
    id: UUID
    empresa_nombre: str
    sucursal_nombre: str


@dataclass(frozen=True)
class CandidatoPropuesto:
    siges_sucursal_id: int
    score: float
    nivel: NivelMatch
    motivo: str


_MOTIVO_N1 = "símbolo/abreviatura normalizados (misma sucursal)"


def _motivo_n2(local_fuerte: str, siges_fuerte: str) -> str:
    solo_local = set(local_fuerte.split()) - set(siges_fuerte.split())
    solo_siges = set(siges_fuerte.split()) - set(local_fuerte.split())
    if not solo_local and not solo_siges:
        return "coincidencia total tras normalizar"
    partes = []
    if solo_local:
        partes.append(f"local trae: {' '.join(sorted(solo_local))}")
    if solo_siges:
        partes.append(f"Siges trae: {' '.join(sorted(solo_siges))}")
    return "difieren en — " + "; ".join(partes)


def proponer_matches_tabla_km(
    filas_sin_match: list[FilaSinMatch],
    sucursales_siges: list[SigesSucursalCliente],
) -> dict[UUID, list[CandidatoPropuesto]]:
    """Para cada fila local sin match en N0, top-N candidatos Siges de la
    MISMA empresa (normalizada), rankeados por score. Nivel N1 = igualdad
    exacta bajo `normalizar_nombre_fuerte` (auto-vinculable, decisión 0.4.a);
    N2 = score >= UMBRAL_N2 (SIEMPRE requiere confirmación humana). Un
    candidato con número de sucursal distinto al de la fila local nunca se
    propone (ancla dura, ver `_numero_sucursal`)."""
    por_empresa: dict[str, list[SigesSucursalCliente]] = {}
    for s in sucursales_siges:
        por_empresa.setdefault(normalizar_nombre_fuerte(s.empresa_nombre), []).append(s)

    resultado: dict[UUID, list[CandidatoPropuesto]] = {}
    for fila in filas_sin_match:
        candidatos_empresa = por_empresa.get(normalizar_nombre_fuerte(fila.empresa_nombre), [])
        if not candidatos_empresa:
            continue
        propuestas = _candidatos_para_fila(fila, candidatos_empresa)
        if propuestas:
            resultado[fila.id] = propuestas
    return resultado


def _candidatos_para_fila(
    fila: FilaSinMatch, candidatos_empresa: list[SigesSucursalCliente]
) -> list[CandidatoPropuesto]:
    local_fuerte = normalizar_nombre_fuerte(fila.sucursal_nombre)
    numero_local = _numero_sucursal(local_fuerte)
    evaluados: list[CandidatoPropuesto] = []
    for c in candidatos_empresa:
        siges_fuerte = normalizar_nombre_fuerte(c.sucursal_nombre)
        numero_siges = _numero_sucursal(siges_fuerte)
        if numero_local is not None and numero_siges is not None and numero_local != numero_siges:
            continue
        if local_fuerte == siges_fuerte:
            evaluados.append(CandidatoPropuesto(c.siges_sucursal_id, 1.0, "N1", _MOTIVO_N1))
            continue
        score = _score(local_fuerte, siges_fuerte)
        if score >= UMBRAL_N2:
            motivo = _motivo_n2(local_fuerte, siges_fuerte)
            evaluados.append(CandidatoPropuesto(c.siges_sucursal_id, score, "N2", motivo))
    evaluados.sort(key=lambda c: c.score, reverse=True)
    return evaluados[:TOP_N_CANDIDATOS]
