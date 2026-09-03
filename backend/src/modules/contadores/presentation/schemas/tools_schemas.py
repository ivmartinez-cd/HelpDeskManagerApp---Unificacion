from datetime import date

from pydantic import BaseModel


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]


class RunEstimationZeroResponse(BaseModel):
    file: str

    @classmethod
    def from_path(cls, path: str) -> "RunEstimationZeroResponse":
        return cls(file=_basename(path))


class RunEstimationZeroFromProcesoBody(BaseModel):
    nro_proceso: int
    fecha: date


class RunFixedSumResponse(BaseModel):
    files: list[str]

    @classmethod
    def from_paths(cls, paths: list[str]) -> "RunFixedSumResponse":
        return cls(files=[_basename(p) for p in paths])
