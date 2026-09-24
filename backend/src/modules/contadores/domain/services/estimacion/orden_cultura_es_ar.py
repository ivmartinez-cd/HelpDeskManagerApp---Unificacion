"""Orden de strings como el `OrderBy` de .NET 8 con la cultura es-AR (ICU):
comparación lingüística en tres niveles — letra base, después acento,
después mayúscula/minúscula (minúscula primero) —, puntuación antes que
dígitos y dígitos antes que letras, la "ñ" como letra aparte después de la
"n". El export a SiGes ordena las máquinas así (empresa, sucursal, serie).

`_ORDEN` se generó con el comparador real de .NET 8 (es-AR) sobre ASCII,
Latin-1 y Latin Extendido A/B: cada tupla es un grupo de igual letra base,
en orden; dentro, cada string es un grupo de igual acento y cada caracter
difiere del siguiente solo en mayúscula/minúscula. El guion blando (U+00AD)
se ignora. Un caracter fuera de la tabla toma el lugar de su letra base (sin
diacríticos) o, si tampoco está, va al final por punto de código."""

import unicodedata

# fmt: off
_ORDEN: tuple[tuple[str, ...], ...] = (
    ("\u0020\u00a0",), ("\u005f",), ("\u002d",), ("\u002c",), ("\u003b",), ("\u003a",),
    ("\u0021",), ("\u00a1",), ("\u003f",), ("\u00bf",), ("\u002e",), ("\u00b7",), ("\u0027",),
    ("\u0022",), ("\u00ab",), ("\u00bb",), ("\u0028",), ("\u0029",), ("\u005b",), ("\u005d",),
    ("\u007b",), ("\u007d",), ("\u00a7",), ("\u00b6",), ("\u0040",), ("\u002a",), ("\u002f",),
    ("\u005c",), ("\u0026",), ("\u0023",), ("\u0025",), ("\u0060",), ("\u00b4",), ("\u005e",),
    ("\u00af",), ("\u00a8",), ("\u00b8",), ("\u00b0",), ("\u00a9",), ("\u00ae",), ("\u002b",),
    ("\u00b1",), ("\u00f7",), ("\u00d7",), ("\u003c",), ("\u003d",), ("\u003e",), ("\u00ac",),
    ("\u007c",), ("\u00a6",), ("\u007e",), ("\u00a4",), ("\u00a2",), ("\u0024",), ("\u00a3",),
    ("\u00a5",), ("0",), ("1\u00b9",), ("\u00bd",), ("\u00bc",), ("2\u00b2",), ("3\u00b3",),
    ("\u00be",), ("4",), ("5",), ("6",), ("7",), ("8",), ("9",),
    ("aA\u00aa", "\u00e1\u00c1", "\u00e0\u00c0", "\u0103\u0102", "\u00e2\u00c2",
     "\u01ce\u01cd", "\u00e5\u00c5", "\u01fb\u01fa", "\u00e4\u00c4", "\u01df\u01de",
     "\u00e3\u00c3", "\u0227\u0226", "\u01e1\u01e0", "\u0105\u0104", "\u0101\u0100",
     "\u0201\u0200", "\u0203\u0202"),
    ("\u00e6\u00c6", "\u01fd\u01fc", "\u01e3\u01e2"), ("\u023a",), ("bB",), ("\u0180\u0243",),
    ("\u0181",), ("\u0183\u0182",),
    ("cC", "\u0107\u0106", "\u0109\u0108", "\u010d\u010c", "\u010b\u010a", "\u00e7\u00c7"),
    ("\u023c\u023b",), ("\u0188\u0187",),
    ("dD", "\u010f\u010e", "\u0111\u0110", "\u00f0\u00d0"), ("\u0238",),
    ("\u01f3\u01f2\u01f1", "\u01c6\u01c5\u01c4"), ("\u0189",), ("\u018a",), ("\u018c\u018b",),
    ("\u0221",),
    ("eE", "\u00e9\u00c9", "\u00e8\u00c8", "\u0115\u0114", "\u00ea\u00ca", "\u011b\u011a",
     "\u00eb\u00cb", "\u0117\u0116", "\u0229\u0228", "\u0119\u0118", "\u0113\u0112",
     "\u0205\u0204", "\u0207\u0206"),
    ("\u0247\u0246",), ("\u01dd\u018e",), ("\u018f",), ("\u0190",), ("fF",), ("\u0192\u0191",),
    ("gG", "\u01f5\u01f4", "\u011f\u011e", "\u011d\u011c", "\u01e7\u01e6", "\u0121\u0120",
     "\u0123\u0122"),
    ("\u01e5\u01e4",), ("\u0193",), ("\u0194",), ("\u01a3\u01a2",),
    ("hH", "\u0125\u0124", "\u021f\u021e", "\u0127\u0126"), ("\u0195\u01f6",),
    ("iI", "\u00ed\u00cd", "\u00ec\u00cc", "\u012d\u012c", "\u00ee\u00ce", "\u01d0\u01cf",
     "\u00ef\u00cf", "\u0129\u0128", "\u0130", "\u012f\u012e", "\u012b\u012a", "\u0209\u0208",
     "\u020b\u020a"),
    ("\u0133\u0132",), ("\u0131",), ("\u0197",), ("\u0196",), ("jJ", "\u0135\u0134", "\u01f0"),
    ("\u0237",), ("\u0249\u0248",), ("kK", "\u01e9\u01e8", "\u0137\u0136"), ("\u0199\u0198",),
    ("lL", "\u013a\u0139", "\u013e\u013d", "\u013c\u013b", "\u0142\u0141", "\u0140\u013f"),
    ("\u01c9\u01c8\u01c7",), ("\u019a\u023d",), ("\u0234",), ("\u019b",), ("mM",),
    ("nN", "\u0144\u0143", "\u01f9\u01f8", "\u0148\u0147", "\u0146\u0145"),
    ("\u01cc\u01cb\u01ca",), ("\u00f1\u00d1",), ("\u019d",), ("\u019e\u0220",), ("\u0235",),
    ("\u014b\u014a",),
    ("oO\u00ba", "\u00f3\u00d3", "\u00f2\u00d2", "\u014f\u014e", "\u00f4\u00d4",
     "\u01d2\u01d1", "\u00f6\u00d6", "\u022b\u022a", "\u0151\u0150", "\u00f5\u00d5",
     "\u022d\u022c", "\u022f\u022e", "\u0231\u0230", "\u00f8\u00d8", "\u01ff\u01fe",
     "\u01eb\u01ea", "\u01ed\u01ec", "\u014d\u014c", "\u020d\u020c", "\u020f\u020e",
     "\u01a1\u01a0"),
    ("\u0153\u0152",), ("\u0186",), ("\u019f",), ("\u0223\u0222",), ("pP",), ("\u01a5\u01a4",),
    ("qQ",), ("\u0239",), ("\u024b\u024a",), ("\u0138",),
    ("rR", "\u0155\u0154", "\u0159\u0158", "\u0157\u0156", "\u0211\u0210", "\u0213\u0212"),
    ("\u01a6",), ("\u024d\u024c",),
    ("sS", "\u015b\u015a", "\u015d\u015c", "\u0161\u0160", "\u015f\u015e", "\u0219\u0218",
     "\u017f"),
    ("\u00df",), ("\u023f",), ("\u01a9",), ("\u01aa",),
    ("tT", "\u0165\u0164", "\u0163\u0162", "\u021b\u021a"), ("\u01be",), ("\u0167\u0166",),
    ("\u023e",), ("\u01ab",), ("\u01ad\u01ac",), ("\u01ae",), ("\u0236",),
    ("uU", "\u00fa\u00da", "\u00f9\u00d9", "\u016d\u016c", "\u00fb\u00db", "\u01d4\u01d3",
     "\u016f\u016e", "\u00fc\u00dc", "\u01d8\u01d7", "\u01dc\u01db", "\u01da\u01d9",
     "\u01d6\u01d5", "\u0171\u0170", "\u0169\u0168", "\u0173\u0172", "\u016b\u016a",
     "\u0215\u0214", "\u0217\u0216", "\u01b0\u01af"),
    ("\u0244",), ("\u019c",), ("\u01b1",), ("vV",), ("\u01b2",), ("\u0245",),
    ("wW", "\u0175\u0174"), ("xX",),
    ("yY", "\u00fd\u00dd", "\u0177\u0176", "\u00ff\u0178", "\u0233\u0232"), ("\u024f\u024e",),
    ("\u01b4\u01b3",), ("\u021d\u021c",),
    ("zZ", "\u017a\u0179", "\u017e\u017d", "\u017c\u017b"), ("\u018d",), ("\u01b6\u01b5",),
    ("\u0225\u0224",), ("\u0240",), ("\u01b7", "\u01ef\u01ee"), ("\u01b9\u01b8",), ("\u01ba",),
    ("\u00fe\u00de",), ("\u01bf\u01f7",), ("\u01bb",), ("\u01a8\u01a7",), ("\u01bd\u01bc",),
    ("\u0185\u0184",), ("\u0242\u0241",), ("\u0149",), ("\u01c0",), ("\u01c1",), ("\u01c2",),
    ("\u01c3",), ("\u00b5",),
)
# fmt: on

_IGNORADOS = frozenset("\u00ad")

# Ligaduras y fracciones que ICU compara como su expansión ("æ" como "ae"),
# desempatando después de ella.
_EXPANSIONES = {
    "\u00e6": "ae",
    "\u00c6": "AE",
    "\u0153": "oe",
    "\u0152": "OE",
    "\u00df": "ss",
    "\u0133": "ij",
    "\u0132": "IJ",
    "\u00bd": "1/2",
    "\u00bc": "1/4",
    "\u00be": "3/4",
    "\u0149": "\u02bcn",
}


def _pesos() -> dict[str, tuple[int, int, int]]:
    pesos: dict[str, tuple[int, int, int]] = {}
    secundario = terciario = 0
    for primario, grupo in enumerate(_ORDEN, start=1):
        for acento in grupo:
            secundario += 1
            for caracter in acento:
                terciario += 1
                pesos[caracter] = (primario, secundario, terciario)
    return pesos


_PESOS = _pesos()
_FUERA_DE_TABLA = len(_ORDEN) + 1
_DESEMPATE = len(_PESOS) + 1


def clave_orden_es_ar(texto: str) -> tuple[tuple[int, ...], ...]:
    """Clave de orden: letra base, acento y mayúscula de todo el texto, en
    ese orden de prioridad (una diferencia de acento solo desempata)."""
    pesos = [p for c in texto if c not in _IGNORADOS for p in _pesos_de(c)]
    return tuple(tuple(p[nivel] for p in pesos) for nivel in range(3))


def _pesos_de(caracter: str) -> list[tuple[int, int, int]]:
    expansion = _EXPANSIONES.get(caracter)
    if expansion is None:
        return [_peso(caracter)]
    pesos = [_peso(c) for c in expansion]
    primario, secundario, terciario = pesos[-1]
    return [*pesos[:-1], (primario, secundario, terciario + _DESEMPATE)]


def _peso(caracter: str) -> tuple[int, int, int]:
    if caracter in _PESOS:
        return _PESOS[caracter]
    base = unicodedata.normalize("NFD", caracter)[0]
    if base in _PESOS:
        primario, secundario, terciario = _PESOS[base]
        return primario, secundario, terciario
    return _FUERA_DE_TABLA, ord(caracter), ord(caracter)
