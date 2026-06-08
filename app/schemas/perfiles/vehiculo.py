from pydantic import BaseModel


class VehiculoCrear(BaseModel):
    placa: str
    modelo: str
    color: str
    cliente_id: int


class VehiculoActualizar(BaseModel):
    placa: str | None = None
    modelo: str | None = None
    color: str | None = None


class VehiculoSalida(BaseModel):
    id: int
    placa: str
    modelo: str
    color: str
    cliente_id: int

    class Config:
        from_attributes = True
