from pydantic import BaseModel
from typing import Optional


class TiempoPromedioAsignacionSalida(BaseModel):
    promedio_minutos: Optional[float] = None
    total_casos: int


class TiempoPromedioLlegadaSalida(BaseModel):
    promedio_minutos: Optional[float] = None
    total_ordenes: int


class IncidentePorTipoItem(BaseModel):
    categoria: str
    cantidad: int


class IncidentesPorTipoSalida(BaseModel):
    datos: list[IncidentePorTipoItem]
    total: int


class TallerEficienciaItem(BaseModel):
    taller_id: int
    nombre: str
    promedio_estrellas: Optional[float] = None
    promedio_tiempo_atencion_minutos: Optional[float] = None
    total_ordenes: int


class TalleresEficientesSalida(BaseModel):
    datos: list[TallerEficienciaItem]


class ZonaIncidenteItem(BaseModel):
    latitud_zona: float
    longitud_zona: float
    nombre_zona: str
    cantidad: int


class ZonasIncidentesSalida(BaseModel):
    datos: list[ZonaIncidenteItem]


class CasosCanceladosSalida(BaseModel):
    total_cancelados: int
    porcentaje_del_total: float
    total_incidentes: int


class SlaCumplimientoSalida(BaseModel):
    total_ordenes_con_llegada: int
    ordenes_dentro_sla: int
    porcentaje_cumplimiento: float
