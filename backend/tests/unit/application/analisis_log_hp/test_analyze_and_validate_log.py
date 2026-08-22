"""AnalyzeLog y ValidateLog: parseo + enriquecimiento + detección de códigos
no catalogados, con el catálogo en memoria."""

from src.modules.analisis_log_hp.application.use_cases.analyze_log import AnalyzeLog
from src.modules.analisis_log_hp.application.use_cases.validate_log import ValidateLog
from tests.unit.application.analisis_log_hp.fakes import FakeErrorCodeRepo, make_error_code

# Log pegado del portal: 2+ espacios en vez de tabs (normalize_log_text los convierte).
_LOG = (
    "Error  13.20.01  05-ago-2026 09:05:00  100  FW  ayuda\n"
    "Error  13.20.01  05-ago-2026 10:05:00  120  FW  ayuda\n"
    "Warning  41.03  06-ago-2026 11:00:00  130  FW  ayuda\n"
    "linea rota\n"
)


class TestAnalyzeLog:
    async def test_agrupa_incidentes_y_enriquece_con_catalogo(self) -> None:
        repo = FakeErrorCodeRepo([make_error_code("13.20.01", description="Atasco")])
        result = await AnalyzeLog(repo).execute(_LOG)

        assert len(result.events) == 3
        assert len(result.report.errors) == 1
        codes = {i.code: i for i in result.analysis.incidents}
        assert codes["13.20.01"].occurrences == 2
        assert codes["13.20.01"].classification == "Atasco"
        assert result.analysis.global_severity == "ERROR"

    async def test_codes_new_son_los_no_catalogados_en_orden_de_aparicion(self) -> None:
        repo = FakeErrorCodeRepo([make_error_code("41.03")])
        result = await AnalyzeLog(repo).execute(_LOG)
        assert result.codes_new == ["13.20.01"]

    async def test_log_vacio_da_analisis_vacio(self) -> None:
        result = await AnalyzeLog(FakeErrorCodeRepo()).execute("")
        assert result.analysis.incidents == ()
        assert result.codes_new == []


class TestValidateLog:
    async def test_devuelve_codigos_sin_catalogar_sin_duplicados(self) -> None:
        repo = FakeErrorCodeRepo([make_error_code("41.03")])
        assert await ValidateLog(repo).execute(_LOG) == ["13.20.01"]

    async def test_todo_catalogado_devuelve_lista_vacia(self) -> None:
        repo = FakeErrorCodeRepo([make_error_code("41.03"), make_error_code("13.20.01")])
        assert await ValidateLog(repo).execute(_LOG) == []
