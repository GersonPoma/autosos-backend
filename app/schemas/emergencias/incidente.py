from datetime import datetime

from pydantic import BaseModel

from app.models.emergencias.incidente import EstadoIncidente, PrioridadIncidente


class IncidenteCrear(BaseModel):
    latitud: float
    longitud: float


class IncidenteActualizar(BaseModel):
    latitud: float | None = None
    longitud: float | None = None
    estado: EstadoIncidente | None = None
    prioridad: PrioridadIncidente | None = None


class IncidenteSalida(BaseModel):
    id: int
    latitud: float
    longitud: float
    fecha_hora: datetime
    estado: EstadoIncidente
    prioridad: PrioridadIncidente
    usuario_id: int

    class Config:
        from_attributes = True

