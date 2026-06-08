from datetime import datetime

from pydantic import BaseModel

from app.models.talleres.cotizacion import EstadoCotizacion, TipoAtencion


class DetalleCotizacionCrear(BaseModel):
    servicio_taller_id: int
    cantidad: int
    precio_unitario: float


class CotizacionCrear(BaseModel):
    asignacion_candidato_id: int
    tipo_atencion: TipoAtencion
    fecha_validez: datetime
    detalles: list[DetalleCotizacionCrear]


class DetalleCotizacionSalida(BaseModel):
    id: int
    servicio_taller_id: int
    servicio_nombre: str | None = None
    cantidad: int
    precio_unitario: float
    subtotal: float

    class Config:
        from_attributes = True


class CotizacionSalida(BaseModel):
    id: int
    estado_cotizacion: EstadoCotizacion
    tipo_atencion: TipoAtencion
    distancia_km: float
    tiempo_estimado_llegada: int
    costo_total: float
    fecha_emision: datetime
    fecha_validez: datetime
    asignacion_candidato_id: int
    detalles: list[DetalleCotizacionSalida] = []

    class Config:
        from_attributes = True


class AceptarCotizacionSalida(BaseModel):
    mensaje: str
    orden_servicio_id: int
    tiempo_estimado_llegada: int