from pydantic import BaseModel


class ServicioTallerCrear(BaseModel):
    nombre: str
    categoria: str
    precio: float
    taller_id: int


class ServicioTallerActualizar(BaseModel):
    nombre: str | None = None
    categoria: str | None = None
    precio: float | None = None


class ServicioTallerSalida(BaseModel):
    id: int
    nombre: str
    categoria: str
    precio: float
    taller_id: int
    taller_nombre: str | None = None

    class Config:
        from_attributes = True
