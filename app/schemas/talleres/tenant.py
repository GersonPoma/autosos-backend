from datetime import datetime

from pydantic import BaseModel


class TenantCrear(BaseModel):
    nombre: str
    activo: bool = True
    username: str
    password: str


class TenantActualizar(BaseModel):
    nombre: str | None = None
    activo: bool | None = None


class TenantSalida(BaseModel):
    id: int
    nombre: str
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True