from pydantic import BaseModel


class TecnicoCrear(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    taller_id: int
    tenant_id: int
    username: str
    password: str


class TecnicoActualizar(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    telefono: str | None = None


class TecnicoSalida(BaseModel):
    id: int
    nombre: str
    apellido: str
    telefono: str
    taller_id: int
    taller_nombre: str | None = None
    usuario_id: int

    class Config:
        from_attributes = True
