"""Tests de GetInsumosConfig / SaveInsumosConfig — GET y PUT /api/insumos/config."""

from dataclasses import replace

from src.modules.insumos.application.dtos.insumos_config import SaveConfigCommand
from src.modules.insumos.application.use_cases.get_insumos_config import (
    GetInsumosConfig,
    GetInsumosConfigPorts,
)
from src.modules.insumos.application.use_cases.save_insumos_config import (
    SaveInsumosConfig,
    SaveInsumosConfigPorts,
)
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from tests.unit.domain.insumos.fakes import FakeInsumosSettingsRepository


class World:
    def __init__(self) -> None:
        self.settings = FakeInsumosSettingsRepository()
        self.get = GetInsumosConfig(GetInsumosConfigPorts(settings=self.settings))  # type: ignore[arg-type]
        self.save = SaveInsumosConfig(SaveInsumosConfigPorts(settings=self.settings))  # type: ignore[arg-type]

    async def save_valid(
        self,
        emails: list[str] | None = None,
        ops_emails: list[str] | None = None,
        **overrides: object,
    ) -> object:
        command = SaveConfigCommand(
            settings=replace(InsumosSettings(), **overrides),  # type: ignore[arg-type]
            logistics_mail_to=emails or [],
            # ops_alert_mail_to es obligatorio (validate_settings lo exige no
            # vacío) — default a un valor válido para no confundir los tests
            # que ejercitan otra cosa con este error nuevo. `is None` y no
            # `or`: `ops_emails=[]` tiene que viajar vacío de verdad (lo
            # ejercita test_sin_destinatario_de_alertas_tecnicas_no_graba_nada).
            ops_alert_mail_to=["ops@example.com"] if ops_emails is None else ops_emails,
        )
        return await self.save.execute(command)


async def test_sin_nada_grabado_se_devuelven_los_defaults_de_negocio() -> None:
    world = World()

    view = await world.get.execute()

    assert view.settings == InsumosSettings()
    assert view.logistics_mail_to == []
    assert view.ops_alert_mail_to == ["imartinez@canaldirecto.com.ar"]


async def test_un_valor_corrupto_no_rompe_la_pantalla_de_configuracion() -> None:
    """settings_from_raw loguea y cae al default: la config tiene que poder abrirse
    igual para poder corregir el valor."""
    world = World()
    world.settings.raw = {"threshold_critical": "no-es-un-numero"}

    view = await world.get.execute()

    assert view.settings.threshold_critical == InsumosSettings().threshold_critical


async def test_guardar_persiste_todas_las_keys_como_strings() -> None:
    world = World()

    result = await world.save_valid(threshold_critical=2, autoload_enabled=True)

    assert result.ok is True  # type: ignore[attr-defined]
    assert world.settings.raw["threshold_critical"] == "2"
    assert world.settings.raw["autoload_enabled"] == "1"


async def test_lo_guardado_es_lo_que_devuelve_el_get() -> None:
    world = World()
    await world.save_valid(emails=["logistica@example.com"], autoload_max_days=10)

    view = await world.get.execute()

    assert view.settings.autoload_max_days == 10
    assert view.logistics_mail_to == ["logistica@example.com"]


async def test_una_config_invalida_no_graba_nada() -> None:
    """Todo o nada: media configuración aplicada dejaría umbrales incoherentes."""
    world = World()

    result = await world.save_valid(threshold_critical=99)

    assert result.ok is False  # type: ignore[attr-defined]
    assert result.error is not None  # type: ignore[attr-defined]
    assert world.settings.raw == {}


async def test_los_mails_se_normalizan_antes_de_guardar() -> None:
    world = World()

    await world.save_valid(emails=["  a@example.com  ", "", "   "])

    assert world.settings.raw["logistics_mail_to"] == "a@example.com"


async def test_un_mail_invalido_frena_el_guardado_entero() -> None:
    world = World()

    result = await world.save_valid(emails=["a@example.com", "roto"])

    assert result.ok is False  # type: ignore[attr-defined]
    assert world.settings.raw == {}


async def test_ops_alert_mail_to_se_persiste_separado_de_logistica() -> None:
    world = World()
    await world.save_valid(emails=["logistica@example.com"], ops_emails=["ops@example.com"])

    view = await world.get.execute()

    assert view.logistics_mail_to == ["logistica@example.com"]
    assert view.ops_alert_mail_to == ["ops@example.com"]


async def test_sin_destinatario_de_alertas_tecnicas_no_graba_nada() -> None:
    """Resguardo directo del incidente real del 2026-08-12 (ver CLAUDE.md): no
    se puede dejar la config sin nadie que reciba una falla del poller."""
    world = World()

    result = await world.save_valid(ops_emails=[])

    assert result.ok is False  # type: ignore[attr-defined]
    assert world.settings.raw == {}


async def test_no_se_pisan_keys_ajenas_de_app_settings() -> None:
    """app_settings es un key-value compartido: un PUT de configuración no puede
    llevarse puesto lo que escriban otros."""
    world = World()
    world.settings.raw = {"clave_de_otro_modulo": "valor"}

    await world.save_valid()

    assert world.settings.raw["clave_de_otro_modulo"] == "valor"
