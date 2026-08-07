from datetime import date

from fastapi import APIRouter, Depends, Form, UploadFile

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.run_projection_request import RunProjectionRequest
from src.modules.contadores.application.use_cases.run_counter_projection import (
    RunCounterProjectionUseCase,
)
from src.modules.contadores.domain.value_objects.projection_settings import ProjectionSettings
from src.modules.contadores.domain.well_known_permissions import EXPORT
from src.modules.contadores.infrastructure.excel.openpyxl_counter_workbook_reader import (
    OpenpyxlCounterWorkbookReader,
)
from src.modules.contadores.infrastructure.excel.openpyxl_projection_report_writer import (
    OpenpyxlProjectionReportWriter,
)
from src.modules.contadores.presentation.schemas.projection_schemas import RunProjectionResponse
from src.modules.contadores.presentation.upload_storage import output_dir, save_upload

router = APIRouter(prefix="/api/contadores", tags=["contadores"])

_require_export = Depends(require_permission(EXPORT))


@router.post("/proyeccion")
async def run_proyeccion(
    file: UploadFile,
    fecha_toma: date = Form(...),
    tolerancia_dias: int = Form(2),
    min_dias_intervalo: int = Form(1),
    ventana_reciente_dias: int = Form(365),
    umbral_minimo_consumo: float = Form(0.2),
    max_antiguedad_lectura_dias: int = Form(365),
    _: Identity = _require_export,
) -> RunProjectionResponse:
    upload_path = await save_upload(file)
    try:
        request = RunProjectionRequest(
            file_path=str(upload_path),
            source_filename=file.filename or upload_path.name,
            fecha_toma=fecha_toma,
            output_dir=output_dir(),
            settings=ProjectionSettings(
                tolerancia_dias=tolerancia_dias,
                min_dias_intervalo=min_dias_intervalo,
                ventana_reciente_dias=ventana_reciente_dias,
                umbral_minimo_consumo=umbral_minimo_consumo,
                max_antiguedad_lectura_dias=max_antiguedad_lectura_dias,
            ),
        )
        use_case = RunCounterProjectionUseCase(
            OpenpyxlCounterWorkbookReader(), OpenpyxlProjectionReportWriter()
        )
        result = use_case.execute(request)
    finally:
        upload_path.unlink(missing_ok=True)
    return RunProjectionResponse.from_domain(result)
