"""DTOs de la configuración del módulo (GET/PUT /api/insumos/config)."""

from dataclasses import dataclass

from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings


@dataclass(frozen=True)
class ConfigView:
    """`logistics_mail_to`/`ops_alert_mail_to` viajan como lista aunque se
    persistan como CSV en una key cada uno."""

    settings: InsumosSettings
    logistics_mail_to: list[str]
    ops_alert_mail_to: list[str]


@dataclass(frozen=True)
class SaveConfigCommand:
    """El `logistics_mail_to`/`ops_alert_mail_to` de `settings` se ignoran: la
    lista manda."""

    settings: InsumosSettings
    logistics_mail_to: list[str]
    ops_alert_mail_to: list[str]


@dataclass(frozen=True)
class SaveConfigResult:
    """Mismo contrato que el legacy: 200 con ok=false + mensaje si algo no valida —
    los errores de configuración son para mostrar en el formulario, no un 4xx."""

    ok: bool
    error: str | None = None
