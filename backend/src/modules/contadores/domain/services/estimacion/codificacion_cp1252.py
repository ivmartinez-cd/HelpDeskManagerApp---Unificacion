"""Codificación Windows-1252 del archivo de exportación, idéntica a la del
Estimador de Contadores v1.7 (`Encoding.GetEncoding(1252)` de .NET): los
caracteres que no existen en cp1252 no caen todos a "?" como en el codec de
Python, sino que .NET aplica su tabla de "best fit" ("ā" → "a", "ł" → "l",
"−" → "-", "─" → "-"...). Sin esto una observación con esos caracteres
llegaría distinta a SiGes.

`_BEST_FIT` se generó recorriendo todo el plano básico de Unicode con el
encoder real de .NET 8 y guardando cada caracter cuyo byte difiere del codec
cp1252 de Python (incluye los 5 bytes que Python deja sin definir: 0x81,
0x8D, 0x8F, 0x90 y 0x9D). Fuera del plano básico .NET emite un "?" por cada
mitad del par sustituto."""

# byte de destino → caracteres que .NET mapea a ese byte.
_BEST_FIT: dict[int, str] = {
    0x20: "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u3000",
    0x21: "\u01c3\uff01",
    0x22: "\u02ba\u030e\uff02",
    0x23: "\uff03",
    0x24: "\uff04",
    0x25: "\u066a\uff05",
    0x26: "\uff06",
    0x27: "\u02b9\u02bc\u02c8\u2032\uff07",
    0x28: "\u2320\uff08",
    0x29: "\u2321\uff09",
    0x2A: "\u2217\uff0a",
    0x2B: (
        "\u250c\u2510\u2514\u2518\u251c\u253c\u2552\u2553\u2554\u2555\u2556\u2557"
        "\u2558\u2559\u255a\u255b\u255c\u255d\u256a\u256b\u256c\uff0b"
    ),
    0x2C: "\uff0c",
    0x2D: ("\u2010\u2011\u2212\u2500\u252c\u2534\u2550\u2564\u2565\u2566\u2567\u2568\u2569\uff0d"),
    0x2E: "\uff0e",
    0x2F: "\u2044\u2215\uff0f",
    0x30: "\u2080\uff10",
    0x31: "\u2081\uff11",
    0x32: "\u2082\uff12",
    0x33: "\u2083\uff13",
    0x34: "\u2074\u2084\uff14",
    0x35: "\u2075\u2085\uff15",
    0x36: "\u2076\u2086\uff16",
    0x37: "\u2077\u2087\uff17",
    0x38: "\u2078\u2088\u221e\uff18",
    0x39: "\u2089\uff19",
    0x3A: "\u0589\u2236\uff1a",
    0x3B: "\u037e\uff1b",
    0x3C: "\u2329\u3008\uff1c",
    0x3D: "\u2017\u2261\u2264\u2265\uff1d",
    0x3E: "\u232a\u3009\uff1e",
    0x40: "\uff20",
    0x41: "\u0100\u0102\u0104\u01cd\u01de\uff21",
    0x42: "\u212c\uff22",
    0x43: "\u0106\u0108\u010a\u010c\u2102\u212d\uff23",
    0x44: "\u010e\uff24",
    0x45: "\u0112\u0114\u0116\u0118\u011a\u2107\u2130\uff25",
    0x46: "\u03a6\u2131\uff26",
    0x47: "\u011c\u011e\u0120\u0122\u01e4\u01e6\u0393\uff27",
    0x48: "\u0124\u0126\u210b\u210c\u210d\uff28",
    0x49: "\u0128\u012a\u012c\u012e\u0130\u0197\u01cf\u2110\u2111\uff29",
    0x4A: "\u0134\uff2a",
    0x4B: "\u0136\u01e8\u212a\uff2b",
    0x4C: "\u0139\u013b\u013d\u0141\u2112\uff2c",
    0x4D: "\u2133\uff2d",
    0x4E: "\u0143\u0145\u0147\u2115\uff2e",
    0x4F: "\u014c\u014e\u0150\u019f\u01a0\u01d1\u01ea\u01ec\u03a9\uff2f",
    0x50: "\u20a7\u2118\u2119\uff30",
    0x51: "\u211a\uff31",
    0x52: "\u0154\u0156\u0158\u211b\u211c\u211d\uff32",
    0x53: "\u015a\u015c\u015e\u03a3\uff33",
    0x54: "\u0162\u0164\u0166\u01ae\u0398\uff34",
    0x55: ("\u0168\u016a\u016c\u016e\u0170\u0172\u01af\u01d3\u01d5\u01d7\u01d9\u01db\uff35"),
    0x56: "\uff36",
    0x57: "\u0174\uff37",
    0x58: "\uff38",
    0x59: "\u0176\uff39",
    0x5A: "\u0179\u017b\u2124\u2128\uff3a",
    0x5B: "\u301a\uff3b",
    0x5C: "\u2216\uff3c",
    0x5D: "\u301b\uff3d",
    0x5E: "\u02c4\u0302\u2303\uff3e",
    0x5F: "\u02cd\u0331\u0332\u2584\uff3f",
    0x60: "\u02cb\u0300\u2035\uff40",
    0x61: "\u0101\u0103\u0105\u01ce\u01df\u03b1\uff41",
    0x62: "\u0180\uff42",
    0x63: "\u0107\u0109\u010b\u010d\uff43",
    0x64: "\u010f\u0111\u03b4\uff44",
    0x65: "\u0113\u0115\u0117\u0119\u011b\u03b5\u212e\u212f\uff45",
    0x66: "\u03c6\uff46",
    0x67: "\u011d\u011f\u0121\u0123\u01e5\u01e7\u0261\u210a\uff47",
    0x68: "\u0125\u0127\u04bb\u210e\uff48",
    0x69: "\u0129\u012b\u012d\u012f\u0131\u01d0\uff49",
    0x6A: "\u0135\u01f0\uff4a",
    0x6B: "\u0137\u01e9\uff4b",
    0x6C: "\u013a\u013c\u013e\u0142\u019a\u2113\uff4c",
    0x6D: "\uff4d",
    0x6E: "\u0144\u0146\u0148\u207f\u2229\uff4e",
    0x6F: "\u014d\u014f\u0151\u01a1\u01d2\u01eb\u01ed\u2134\uff4f",
    0x70: "\u03c0\uff50",
    0x71: "\uff51",
    0x72: "\u0155\u0157\u0159\uff52",
    0x73: "\u015b\u015d\u015f\u03c3\uff53",
    0x74: "\u0163\u0165\u0167\u01ab\u03c4\uff54",
    0x75: ("\u0169\u016b\u016d\u016f\u0171\u0173\u01b0\u01d4\u01d6\u01d8\u01da\u01dc\uff55"),
    0x76: "\u221a\uff56",
    0x77: "\u0175\uff57",
    0x78: "\uff58",
    0x79: "\u0177\uff59",
    0x7A: "\u017a\u017c\u01b6\uff5a",
    0x7B: "\uff5b",
    0x7C: "\u01c0\u2223\u2758\uff5c",
    0x7D: "\uff5d",
    0x7E: "\u0303\u223c\uff5e",
    0x81: "\u0081",
    0x83: "\u0191",
    0x8D: "\u008d",
    0x8F: "\u008f",
    0x90: "\u0090",
    0x98: "\u2248",
    0x9D: "\u009d",
    0xA2: "\u20a1",
    0xA3: "\u20a4",
    0xA4: "\u263c",
    0xA6: (
        "\u2302\u2502\u2524\u2551\u255e\u255f\u2560\u2561\u2562\u2563\u2588\u258c"
        "\u2590\u2591\u2592\u2593\u25a0"
    ),
    0xA8: "\u0308",
    0xAB: "\u226a\u300a",
    0xAC: "\u2310",
    0xAF: "\u02c9\u0304\u0305\u2580",
    0xB0: "\u02da\u030a\u2070\u2218",
    0xB1: "\u2213",
    0xB4: "\u02ca\u0301",
    0xB5: "\u03bc",
    0xB7: "\u2024\u2219\u22c5\u30fb",
    0xB8: "\u0327",
    0xBB: "\u226b\u300b",
    0xC5: "\u212b",
    0xD0: "\u0110\u0189",
    0xD8: "\u2205",
    0xDF: "\u03b2",
}

_POR_CARACTER: dict[str, bytes] = {
    caracter: bytes([byte]) for byte, caracteres in _BEST_FIT.items() for caracter in caracteres
}


def codificar_cp1252(texto: str) -> bytes:
    """El texto en cp1252 como lo codifica .NET (best fit, "?" si no hay)."""
    return b"".join(_caracter_cp1252(c) for c in texto)


def _caracter_cp1252(caracter: str) -> bytes:
    try:
        return caracter.encode("cp1252")
    except UnicodeEncodeError:
        if ord(caracter) > 0xFFFF:
            return b"??"
        return _POR_CARACTER.get(caracter, b"?")
