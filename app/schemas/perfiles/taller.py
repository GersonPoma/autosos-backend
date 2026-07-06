from pydantic import BaseModel


class TallerRegistrar(BaseModel):
    nombre: str
    telefono: str
    direccion: str
    latitud: float
    longitud: float
    usuario_id: int
    tenant_id: int


class TallerActualizar(BaseModel):
    nombre: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    disponible: bool | None = None


class TallerEstadoActualizar(BaseModel):
    disponible: bool


class TallerSalida(BaseModel):
    id: int
    nombre: str
    telefono: str
    direccion: str
    latitud: float
    longitud: float
    disponible: bool
    usuario_id: int
    score_confianza: int

    class Config:
        from_attributes = True
