from typing import List, Optional

from pydantic import BaseModel


class DetalleOrdenEntrada(BaseModel):
    cantidad: int
    precio_unitario: float
    subtotal: float
    orden_servicio_id: int
    servicio_taller_id: int


class DetalleOrdenItemEntrada(BaseModel):
    servicio_taller_id: int
    cantidad: int = 1


class GenerarPagoEntrada(BaseModel):
    orden_servicio_id: int
    servicios: List[DetalleOrdenItemEntrada]


class DetalleOrdenSalida(BaseModel):
    id: int
    servicio_taller_id: int
    servicio_nombre: Optional[str] = None
    cantidad: int
    precio_unitario: float
    subtotal: float
    orden_servicio_id: int

    class Config:
        from_attributes = True