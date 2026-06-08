from pydantic import BaseModel


class PrivilegioCrear(BaseModel):
    nombre: str
    descripcion: str | None = None


class PrivilegioActualizar(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None


class PrivilegioSalida(BaseModel):
    id: int
    nombre: str
    descripcion: str | None

    class Config:
        from_attributes = True