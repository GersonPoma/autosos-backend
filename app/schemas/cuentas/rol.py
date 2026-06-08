from pydantic import BaseModel

from app.schemas.cuentas.privilegio import PrivilegioSalida


class RolCrear(BaseModel):
    nombre: str
    tenant_id: int | None = None


class RolActualizar(BaseModel):
    nombre: str


class RolSalida(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


class RolDetalle(RolSalida):
    privilegios: list[PrivilegioSalida] = []