from typing import List, Optional

from pydantic import BaseModel


class DetalleOrdenEntrada(BaseModel):
    precio_cobrado: float
    comentario: Optional[str] = None
    orden_servicio_id: int
    servicio_taller_id: int


class DetalleOrdenItemEntrada(BaseModel):
    servicio_taller_id: int
    comentario: Optional[str] = None


class GenerarPagoEntrada(BaseModel):
    orden_servicio_id: int
    servicios: List[DetalleOrdenItemEntrada]


class DetalleOrdenSalida(BaseModel):
    id: int
    precio_cobrado: float
    comentario: Optional[str]
    orden_servicio_id: int
    servicio_taller_id: int
    nombre_servicio: str
    categoria: str
