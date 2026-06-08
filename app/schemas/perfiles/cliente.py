from datetime import date
from pydantic import BaseModel


class ClienteRegistrar(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date | None = None
    email: str | None = None
    telefono: str
    username: str
    password: str


class ClienteActualizar(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    fecha_nacimiento: date | None = None
    email: str | None = None
    telefono: str | None = None


class ClienteSalida(BaseModel):
    id: int
    nombre: str
    apellido: str
    fecha_nacimiento: date | None
    email: str | None
    telefono: str
    usuario_id: int

    class Config:
        from_attributes = True
