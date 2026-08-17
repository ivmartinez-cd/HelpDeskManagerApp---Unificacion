"""Parseo de respuestas HTML/XML del portal SDS HP.

Port exacto de las funciones del legacy (sds_web_service.py):
- html_to_tsv: extrae la tabla de event logs del wrapper XML/CDATA → TSV 6 cols.
- extract_help_urls: extrae URLs de ayuda por código de la misma tabla.
- _parse_hp_operations: parsea la tabla de operaciones HP Smart.
- _get_html_content: desenvuelve el wrapper XML/CDATA.
- _cell_text: texto de celda sin links incrustados.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from lxml import etree as _etree
from lxml import html

logger = logging.getLogger(__name__)

_HP_OP_FIELDS = (
    "operation", "sent", "sent_by",
    "last_known_state", "last_state_updated", "last_state_requested",
)


def _get_html_content(raw_xml_html: str) -> str:
    try:
        root = _etree.fromstring(raw_xml_html.encode("utf-8"))
        node = root.find("content")
        if node is not None and node.text:
            return str(node.text)
    except Exception as exc:
        logger.debug("XML de event log no parseable, fallback a CDATA", exc_info=exc)
    cdatas = re.findall(r"<!\[CDATA\[(.*?)\]\]>", raw_xml_html, re.DOTALL)
    return max(cdatas, key=len) if cdatas else raw_xml_html


_TSV_HEADER = (
    "Tipo de evento", "Código de evento", "Fecha de evento",
    "N.º total de impresiones", "Versión del firmware", "Ayuda",
)


def _html_content_para_tsv(raw_xml_html: str) -> str:
    try:
        root = _etree.fromstring(raw_xml_html.encode("utf-8"))
        node = root.find("content")
        if node is not None and node.text:
            return str(node.text)
        match = re.search(
            r"<content>\s*<!\[CDATA\[(.*?)\]\]>\s*</content>", raw_xml_html, re.DOTALL
        )
        return match.group(1) if match else raw_xml_html
    except Exception as exc:
        logger.debug("XML de event log no parseable, fallback a CDATA", exc_info=exc)
        cdatas = re.findall(r"<!\[CDATA\[(.*?)\]\]>", raw_xml_html, re.DOTALL)
        return max(cdatas, key=len) if cdatas else raw_xml_html


def _fila_tsv(tr: Any) -> str | None:
    cells = [" ".join(td.text_content().split()) for td in tr.xpath("./td")]
    if not cells:
        return None
    cells += [""] * (6 - len(cells))
    return "\t".join(cells[:6])


def html_to_tsv(raw_xml_html: str) -> str:
    """Convierte el HTML de event logs del portal SDS en un TSV de 6 columnas."""
    try:
        html_content = _html_content_para_tsv(raw_xml_html)
        if not html_content or not html_content.strip():
            return ""
        tree = html.fromstring(html_content)
        table = tree.xpath('//table[@class="data"]') or tree.xpath("//table")
        if not table:
            return ""
        rows = ["\t".join(_TSV_HEADER)]
        for tr in table[0].xpath(".//tbody/tr"):
            fila = _fila_tsv(tr)
            if fila is not None:
                rows.append(fila)
        return "\n".join(rows)
    except Exception as exc:
        logger.error("html_to_tsv: error parseando respuesta SDS: %s", exc, exc_info=exc)
        raise


def _help_link(tds: list[Any]) -> dict[str, Any] | None:
    links = tds[5].xpath(".//a")
    if not links:
        return None
    url = links[0].get("href")
    if not url:
        return None
    desc = " ".join(links[0].text_content().split())
    return {"url": url, "description": desc or None}


def extract_help_urls(raw_xml_html: str) -> dict[str, dict[str, Any]]:
    """{code: {'url': url, 'description': desc}} de la tabla de event logs."""
    result: dict[str, dict[str, Any]] = {}
    try:
        html_content = _get_html_content(raw_xml_html)
        tree = html.fromstring(html_content)
        for tr in tree.xpath("//tbody/tr"):
            tds = tr.xpath("./td")
            if len(tds) < 6:
                continue
            code = " ".join(tds[1].text_content().split())
            if not code or code in result:
                continue
            link = _help_link(tds)
            if link is not None:
                result[code] = link
    except Exception as exc:
        logger.warning("extract_help_urls: falló: %s", exc, exc_info=exc)
    return result


def _cell_text(td: Any) -> str:
    without_links = " ".join("".join(td.xpath(".//text()[not(ancestor::a)]")).split())
    return without_links or " ".join(td.text_content().split())


def parse_hp_operations(page_text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        html_content = _get_html_content(page_text)
        tree = html.fromstring(html_content)
        for tr in tree.xpath("//table//tr"):
            tds = tr.xpath("./td")
            if len(tds) < 4:
                continue
            cells = [_cell_text(td) for td in tds]
            row = dict(zip(_HP_OP_FIELDS, cells, strict=False))
            if row.get("operation"):
                out.append(row)
    except Exception as exc:
        logger.warning("parse_hp_operations: falló: %s", exc, exc_info=exc)
    return out
