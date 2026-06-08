from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.pagos.transaccion import EstadoTransaccion, MetodoPago
from app.schemas.pagos.detalle_orden import DetalleOrdenSalida


class TransaccionEntrada(BaseModel):
    monto_cobrado: float
    monto_comision: float
    metodo_pago: MetodoPago
    orden_servicio_id: int


class ActualizarEstadoEntrada(BaseModel):
    estado: EstadoTransaccion


class StripeIntentSalida(BaseModel):
    client_secret: str
    publishable_key: str


class ActualizarMetodoPagoEntrada(BaseModel):
    metodo_pago: MetodoPago


class TransaccionSalida(BaseModel):
    id: int
    monto_cobrado: float
    monto_comision: float
    estado: EstadoTransaccion
    metodo_pago: Optional[MetodoPago]
    fecha_hora: datetime
    orden_servicio_id: int
    taller_nombre: str | None = None

    class Config:
        from_attributes = True


class GenerarPagoSalida(BaseModel):
    transaccion: TransaccionSalida
    detalles: List[DetalleOrdenSalida]
