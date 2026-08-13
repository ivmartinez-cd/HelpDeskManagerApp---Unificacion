"""PUT /config: merge parcial sobre el singleton + auditoría de claves."""

from src.modules.vacaciones.application.use_cases.actualizar_config import (
    ActualizarConfig,
    ActualizarConfigCommand,
    ActualizarConfigDependencies,
)
from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier
from tests.unit.application.vacaciones.fakes import (
    FakeConfigRepo,
    FakeRegistradorAuditoria,
)
from tests.unit.domain.vacaciones.factories import make_config


class TestActualizarConfig:
    async def test_merge_parcial_no_toca_lo_no_enviado(self) -> None:
        repo = FakeConfigRepo(make_config())
        auditoria = FakeRegistradorAuditoria()
        deps = ActualizarConfigDependencies(config=repo, auditoria=auditoria)
        nueva = await ActualizarConfig(deps).execute(
            ActualizarConfigCommand(min_advance_notice_days=5, max_overlap_percent=35)
        )
        assert nueva.min_advance_notice_days == 5
        assert nueva.max_overlap_percent == 35
        # lo no enviado conserva el valor previo
        assert nueva.next_year_open_month == 10
        assert nueva.allow_carry_over is True
        persistida = await repo.get()
        assert persistida == nueva

    async def test_tiers_se_reemplazan_completos(self) -> None:
        repo = FakeConfigRepo(make_config())
        deps = ActualizarConfigDependencies(config=repo)
        tiers = (SeniorityTier(min_years=0, max_years=99, days=20),)
        nueva = await ActualizarConfig(deps).execute(
            ActualizarConfigCommand(seniority_tiers=tiers)
        )
        assert nueva.seniority_tiers == tiers

    async def test_audita_las_claves_cambiadas(self) -> None:
        auditoria = FakeRegistradorAuditoria()
        deps = ActualizarConfigDependencies(
            config=FakeConfigRepo(make_config()), auditoria=auditoria
        )
        await ActualizarConfig(deps).execute(
            ActualizarConfigCommand(allow_carry_over=False, max_carry_over_days=10)
        )
        accion, entidad, entidad_id, metadata = auditoria.registros[0]
        assert (accion, entidad, entidad_id) == ("UPDATE", "SystemConfig", "singleton")
        assert metadata == {"changes": ["allow_carry_over", "max_carry_over_days"]}
