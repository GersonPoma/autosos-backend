from datetime import date

from pydantic import BaseModel

from app.models.emergencias.evidencia import TipoEvidencia


class EvidenciaCrear(BaseModel):
    tipo: TipoEvidencia
    url: str | None
    incidente_id: int


class EvidenciaActualizar(BaseModel):
    tipo: TipoEvidencia | None = None
    url: str | None = None
    fecha: date | None = None
    incidente_id: int | None = None


class EvidenciaSalida(BaseModel):
    id: int
    tipo: TipoEvidencia
    url: str | None
    fecha: date
    incidente_id: int

    class Config:
        from_attributes = True