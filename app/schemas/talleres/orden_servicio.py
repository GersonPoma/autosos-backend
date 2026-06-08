from datetime import datetime

from pydantic import BaseModel

from app.models.talleres.orden_servicio import EstadoOperacion


class OrdenServicioLista(BaseModel):
    id: int
    incidente_id: int
    nombre_cliente: str
    fecha_hora: datetime
    estado: EstadoOperacion
    taller_nombre: str | None = None
    transaccion_id: int | None = None


class OrdenServicioSalida(BaseModel):
    id: int
    fecha_hora: datetime
    tiempo_estimado_llegada_segundos: int
    tiempo_estimado_llegada: str
    estado: EstadoOperacion
    cotizacion_id: int

    incidente_id: int
    nombre_cliente: str
    taller_id: int | None = None
    taller_nombre: str | None = None
    fecha_hora_llegada: datetime | None = None
    fecha_hora_fin: datetime | None = None
    tiene_transaccion: bool = False
    transaccion_id: int | None = None
    estrellas: float | None = None
    comentario: str | None = None


class OrdenServicioCalificar(BaseModel):
    estrellas: float | None = None
    comentario: str | None = None
