from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.run_db3_export_request import RunDb3ExportRequest
from src.modules.contadores.application.dtos.run_estimation_zero_request import (
    RunEstimationZeroRequest,
)
from src.modules.contadores.application.dtos.run_fixed_sum_request import RunFixedSumRequest
from src.modules.contadores.application.use_cases.run_db3_export import RunDb3ExportUseCase
from src.modules.contadores.application.use_cases.run_estimation_zero import (
    RunEstimationZeroUseCase,
)
from src.modules.contadores.application.use_cases.run_fixed_sum import RunFixedSumUseCase
from src.modules.contadores.domain.well_known_permissions import EXPORT
from src.modules.contadores.infrastructure.csv.csv_db3_writer import CsvDb3Writer
from src.modules.contadores.infrastructure.csv.csv_estimation_zero_writer import (
    CsvEstimationZeroWriter,
)
from src.modules.contadores.infrastructure.csv.csv_falta_contador_reader import (
    CsvFaltaContadorReader,
)
from src.modules.contadores.infrastructure.csv.csv_fixed_sum_writer import CsvFixedSumWriter
from src.modules.contadores.infrastructure.excel.openpyxl_fixed_sum_reader import (
    OpenpyxlFixedSumReader,
)
from src.modules.contadores.infrastructure.sqlite.sqlite3_db3_file_reader import (
    Sqlite3Db3FileReader,
)
from src.modules.contadores.presentation.schemas.db3_schemas import RunDb3ExportResponse
from src.modules.contadores.presentation.schemas.tools_schemas import (
    RunEstimationZeroResponse,
    RunFixedSumResponse,
)
from src.modules.contadores.presentation.upload_storage import output_dir, save_upload

router = APIRouter(prefix="/api/contadores", tags=["contadores"])

_require_export = Depends(require_permission(EXPORT))


@router.post("/db3")
async def run_db3_export(
    files: list[UploadFile],
    fecha_maxima: date | None = Form(None),
    _: Identity = _require_export,
) -> RunDb3ExportResponse:
    upload_paths = [await save_upload(f) for f in files]
    try:
        request = RunDb3ExportRequest(
            file_paths=[str(p) for p in upload_paths],
            base_name=_db3_base_name(files),
            output_dir=output_dir(),
            fecha_maxima=fecha_maxima,
        )
        use_case = RunDb3ExportUseCase(Sqlite3Db3FileReader(), CsvDb3Writer())
        result = use_case.execute(request)
    finally:
        for p in upload_paths:
            p.unlink(missing_ok=True)
    return RunDb3ExportResponse.from_domain(result)


def _db3_base_name(files: list[UploadFile]) -> str:
    if len(files) > 1:
        return f"Consolidado_{len(files)}_archivos"
    name = files[0].filename or "db3"
    return name.replace(".db3", "")


@router.post("/en0")
async def run_estimation_zero(
    file: UploadFile,
    fecha: date = Form(...),
    cliente: str = Form(...),
    _: Identity = _require_export,
) -> RunEstimationZeroResponse:
    upload_path = await save_upload(file)
    try:
        request = RunEstimationZeroRequest(
            file_path=str(upload_path),
            cliente=cliente,
            fecha_nueva=fecha.strftime("%d/%m/%Y"),
            output_dir=output_dir(),
        )
        use_case = RunEstimationZeroUseCase(CsvFaltaContadorReader(), CsvEstimationZeroWriter())
        csv_path = use_case.execute(request)
    finally:
        upload_path.unlink(missing_ok=True)
    return RunEstimationZeroResponse.from_path(csv_path)


@router.post("/suma-fija")
async def run_fixed_sum(
    files: list[UploadFile],
    fecha: date = Form(...),
    hojas: int = Form(...),
    _: Identity = _require_export,
) -> RunFixedSumResponse:
    upload_paths = [await save_upload(f) for f in files]
    try:
        request = RunFixedSumRequest(
            file_paths=[str(p) for p in upload_paths],
            fecha=fecha.strftime("%d/%m/%Y"),
            hojas_a_sumar=hojas,
            output_dir=output_dir(),
        )
        use_case = RunFixedSumUseCase(OpenpyxlFixedSumReader(), CsvFixedSumWriter())
        csv_paths = use_case.execute(request)
    finally:
        for p in upload_paths:
            p.unlink(missing_ok=True)
    return RunFixedSumResponse.from_paths(csv_paths)


@router.get("/outputs/{filename}")
async def download_output(filename: str, _: Identity = _require_export) -> FileResponse:
    """Descarga un archivo de salida generado por las herramientas de Contadores."""
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")
    file_path = Path(output_dir()) / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(file_path, filename=filename)

