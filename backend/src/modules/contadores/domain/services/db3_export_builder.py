from dataclasses import dataclass
from datetime import date

from src.modules.contadores.domain.value_objects.db3_counter_row import Db3CounterRow
from src.modules.contadores.domain.value_objects.db3_export_row import Db3ExportRow

# Modelos que, con counter_class_id=40 (total), en realidad son un contador de
# COLOR y no de Mono — lista tal cual la app vieja (`db3_to_csv.py`).
MODELOS_ESPECIALES = frozenset(
    {
        "C4010ND",
        "CLX_6260_Series",
        "CLX_9201",
        "HP_PageWide_Color_MFP_E58650",
        "X4300LX",
        "CLP_680_Series",
        "FD_E8_48_50_20_50_61_67_65_57_69_64_65_20_50_72_6F_20_34_35_32_64_77_20_50_72_69_6E_74_65_72",
        "FD_E8_48_50_20_43_6F_6C_6F_72_20_4C_61_73_65_72_4A_65_74_20_4D_46_50_20_4D_35_37_37",
        "Samsung_CLP_680_Series",
        "CLP_670_Series",
        "P774ADM05",
        "FD_E8_48_50_20_50_61_67_65_57_69_64_65_20_4D_46_50_20_50_35_37_37_35_30",
        "FD_E8_48_50_20_43_6F_6C_6F_72_20_4C_61_73_65_72_4A_65_74_20_4D_36_35_31",
        "FD_E8_48_50_20_43_6F_6C_6F_72_20_4C_61_73_65_72_4A_65_74_20_4D_36_35_32",
        "FD_E8_48_50_20_4C_61_73_65_72_4A_65_74_20_4D_35_30_36",
        "FD_E8_48_50_20_4C_61_73_65_72_4A_65_74_20_4D_36_30_35",
        "FD_E8_48_50_20_4C_61_73_65_72_4A_65_74_20_4D_36_30_38",
        "HP_PageWide_MFP_P57750",
        "HP_Color_LaserJet_MFP_M577",
    }
)
_RELEVANT_CLASSES = (10, 20, 40)


@dataclass(frozen=True, slots=True)
class _ClassifiedRow:
    serie: str
    fecha: date
    tipo: int
    clase: str
    contador: int


def build_db3_export_rows(
    rows: list[Db3CounterRow], fecha_maxima: date | None = None
) -> list[Db3ExportRow]:
    filtered = [r for r in rows if fecha_maxima is None or r.read_date <= fecha_maxima]
    classified = _dedupe_most_recent(_classify(filtered))
    grouped = _group_by_serie_fecha_tipo(classified)
    return sorted(
        (_build_export_row(key, acc) for key, acc in grouped.items()),
        key=lambda r: (r.serie, r.fecha, r.tipo),
    )


def _classify(rows: list[Db3CounterRow]) -> list[_ClassifiedRow]:
    return [_classify_row(r) for r in rows if r.counter_class_id in _RELEVANT_CLASSES]


def _classify_row(r: Db3CounterRow) -> _ClassifiedRow:
    is_total = r.counter_class_id == 40
    tipo = 15 if is_total else 7
    if is_total:
        clase = "20" if r.model in MODELOS_ESPECIALES else "10"
    else:
        clase = str(r.counter_class_id)
    return _ClassifiedRow(r.serial_number, r.read_date, tipo, clase, r.read_value)


def _dedupe_most_recent(rows: list[_ClassifiedRow]) -> list[_ClassifiedRow]:
    """Una sola lectura por (serie, clase): la más reciente."""
    best: dict[tuple[str, str], _ClassifiedRow] = {}
    for r in sorted(rows, key=lambda x: x.fecha, reverse=True):
        best.setdefault((r.serie, r.clase), r)
    return list(best.values())


@dataclass(slots=True)
class _Accumulator:
    clase_10: str = ""
    contador_10: int = 0
    clase_20: str = ""
    contador_20: int = 0


def _group_by_serie_fecha_tipo(
    rows: list[_ClassifiedRow],
) -> dict[tuple[str, date, int], _Accumulator]:
    grouped: dict[tuple[str, date, int], _Accumulator] = {}
    for r in rows:
        acc = grouped.setdefault((r.serie, r.fecha, r.tipo), _Accumulator())
        # Herencia 40->20: un total (tipo=15) de un modelo especial también
        # cuenta como "columna 10" — así nace la duplicación intencional que
        # ve el sistema de facturación (ver CONTADORES_CARACTERIZACION.md).
        if r.clase == "10" or (r.clase == "20" and r.tipo == 15):
            acc.clase_10, acc.contador_10 = r.clase, r.contador
        if r.clase == "20":
            acc.clase_20, acc.contador_20 = "20", r.contador
    return grouped


def _build_export_row(key: tuple[str, date, int], acc: _Accumulator) -> Db3ExportRow:
    serie, fecha, tipo = key
    if acc.contador_10 == 0 and acc.contador_20 > 0:
        return Db3ExportRow(serie, fecha, tipo, acc.clase_20, acc.contador_20, "", 0)
    return Db3ExportRow(
        serie, fecha, tipo, acc.clase_10, acc.contador_10, acc.clase_20, acc.contador_20
    )
