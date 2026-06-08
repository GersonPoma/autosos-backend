from pydantic import BaseModel

from app.models.talleres.asignacion_candidato import EstadoNotificacion


class AsignacionCandidatoSalida(BaseModel):
    id: int
    distancia_km: float
    estado: EstadoNotificacion
    incidente_id: int
    taller_id: int
    taller_nombre: str | None = None

    class Config:
        from_attributes = True


class RechazarEmergenciaSalida(BaseModel):
    estado: str
    mensaje: str

