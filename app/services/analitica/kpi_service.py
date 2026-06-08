from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric, case, nullslast

from app.models.emergencias.incidente import Incidente, EstadoIncidente
from app.models.talleres.cotizacion import Cotizacion
from app.models.talleres.asignacion_candidato import AsignacionCandidato
from app.models.talleres.orden_servicio import OrdenServicio
from app.models.perfiles.taller import Taller
from app.models.ia.analisis import Analisis
from app.schemas.analitica.kpi_schema import (
    TiempoPromedioAsignacionSalida,
    TiempoPromedioLlegadaSalida,
    IncidentesPorTipoSalida,
    IncidentePorTipoItem,
    TalleresEficientesSalida,
    TallerEficienciaItem,
    ZonasIncidentesSalida,
    ZonaIncidenteItem,
    CasosCanceladosSalida,
    SlaCumplimientoSalida,
)


def tiempo_promedio_asignacion(db: Session, tenant_id: int) -> TiempoPromedioAsignacionSalida:
    """
    Tiempo entre Incidente.fecha_hora y Cotizacion.fecha_emision (en minutos).
    Cadena: Incidente -> AsignacionCandidato -> Cotizacion
    """
    result = (
        db.query(
            func.avg(
                func.extract("epoch", Cotizacion.fecha_emision - Incidente.fecha_hora) / 60
            ).label("promedio_minutos"),
            func.count(Incidente.id).label("total_casos"),
        )
        .join(AsignacionCandidato, AsignacionCandidato.incidente_id == Incidente.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.deleted == False,
            AsignacionCandidato.deleted == False,
            Cotizacion.deleted == False,
        )
        .one()
    )
    return TiempoPromedioAsignacionSalida(
        promedio_minutos=round(float(result.promedio_minutos), 2) if result.promedio_minutos else None,
        total_casos=result.total_casos or 0,
    )


def obtener_tiempo_promedio_llegada(db: Session, tenant_id: int) -> TiempoPromedioLlegadaSalida:
    """
    Promedio entre OrdenServicio.fecha_hora (creacion) y fecha_hora_llegada (en minutos).
    Solo incluye ordenes con llegada registrada.
    """
    result = (
        db.query(
            func.avg(
                func.extract("epoch", OrdenServicio.fecha_hora_llegada - OrdenServicio.fecha_hora) / 60
            ).label("promedio_minutos"),
            func.count(OrdenServicio.id).label("total_ordenes"),
        )
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .join(Incidente, Incidente.id == AsignacionCandidato.incidente_id)
        .filter(
            Incidente.tenant_id == tenant_id,
            OrdenServicio.fecha_hora_llegada.isnot(None),
            Incidente.deleted == False,
            OrdenServicio.deleted == False,
            Cotizacion.deleted == False,
            AsignacionCandidato.deleted == False,
        )
        .one()
    )
    return TiempoPromedioLlegadaSalida(
        promedio_minutos=round(float(result.promedio_minutos), 2) if result.promedio_minutos else None,
        total_ordenes=result.total_ordenes or 0,
    )


def obtener_incidentes_por_tipo(db: Session, tenant_id: int) -> IncidentesPorTipoSalida:
    """
    Agrupa incidentes por Analisis.categoria_problema (clasificacion de la IA).
    Los incidentes sin analisis quedan como 'Sin clasificar'.
    """
    rows = (
        db.query(
            func.coalesce(Analisis.categoria_problema, "Sin clasificar").label("categoria"),
            func.count(Incidente.id).label("cantidad"),
        )
        .outerjoin(Analisis, Analisis.incidente_id == Incidente.id)
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.deleted == False,
        )
        .group_by(func.coalesce(Analisis.categoria_problema, "Sin clasificar"))
        .order_by(func.count(Incidente.id).desc())
        .all()
    )
    datos = [IncidentePorTipoItem(categoria=r.categoria, cantidad=r.cantidad) for r in rows]
    return IncidentesPorTipoSalida(datos=datos, total=sum(d.cantidad for d in datos))


def obtener_talleres_mas_eficientes(
    db: Session, tenant_id: int, limite: int = 10
) -> TalleresEficientesSalida:
    """
    Talleres ordenados por promedio de estrellas desc y tiempo de atencion.
    Cadena: Taller -> AsignacionCandidato -> Cotizacion -> OrdenServicio
    """
    rows = (
        db.query(
            Taller.id.label("taller_id"),
            Taller.nombre.label("nombre"),
            func.avg(OrdenServicio.estrellas).label("promedio_estrellas"),
            func.avg(
                func.extract("epoch", OrdenServicio.fecha_hora_fin - OrdenServicio.fecha_hora) / 60
            ).label("promedio_tiempo_atencion_minutos"),
            func.count(OrdenServicio.id).label("total_ordenes"),
        )
        .join(AsignacionCandidato, AsignacionCandidato.taller_id == Taller.id)
        .join(Cotizacion, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(OrdenServicio, OrdenServicio.cotizacion_id == Cotizacion.id)
        .filter(
            Taller.tenant_id == tenant_id,
            Taller.deleted == False,
            OrdenServicio.deleted == False,
            Cotizacion.deleted == False,
            AsignacionCandidato.deleted == False,
        )
        .group_by(Taller.id, Taller.nombre)
        .order_by(nullslast(func.avg(OrdenServicio.estrellas).desc()))
        .limit(limite)
        .all()
    )
    datos = [
        TallerEficienciaItem(
            taller_id=r.taller_id,
            nombre=r.nombre,
            promedio_estrellas=round(float(r.promedio_estrellas), 2) if r.promedio_estrellas else None,
            promedio_tiempo_atencion_minutos=(
                round(float(r.promedio_tiempo_atencion_minutos), 2)
                if r.promedio_tiempo_atencion_minutos
                else None
            ),
            total_ordenes=r.total_ordenes,
        )
        for r in rows
    ]
    return TalleresEficientesSalida(datos=datos)


def obtener_zonas_con_mas_incidentes(
    db: Session, tenant_id: int, limite: int = 10
) -> ZonasIncidentesSalida:
    """
    Agrupa incidentes por cuadricula geografica de ~1km (redondeo lat/lon a 2 decimales).
    El nombre de zona incluye coordenadas; el frontend puede resolver el topónimo
    con cualquier API de geocodificacion inversa (Google Maps, Nominatim, etc.)
    usando latitud_zona y longitud_zona.
    """
    lat_zona = func.round(cast(Incidente.latitud, Numeric(10, 4)), 2)
    lon_zona = func.round(cast(Incidente.longitud, Numeric(10, 4)), 2)

    rows = (
        db.query(
            lat_zona.label("latitud_zona"),
            lon_zona.label("longitud_zona"),
            func.count(Incidente.id).label("cantidad"),
        )
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.deleted == False,
        )
        .group_by(lat_zona, lon_zona)
        .order_by(func.count(Incidente.id).desc())
        .limit(limite)
        .all()
    )
    datos = [
        ZonaIncidenteItem(
            latitud_zona=float(r.latitud_zona),
            longitud_zona=float(r.longitud_zona),
            nombre_zona=f"Zona ({float(r.latitud_zona):.2f}, {float(r.longitud_zona):.2f})",
            cantidad=r.cantidad,
        )
        for r in rows
    ]
    return ZonasIncidentesSalida(datos=datos)


def obtener_casos_cancelados(db: Session, tenant_id: int) -> CasosCanceladosSalida:
    """Incidentes en estado CANCELADO sobre el total del tenant."""
    total = (
        db.query(func.count(Incidente.id))
        .filter(Incidente.tenant_id == tenant_id, Incidente.deleted == False)
        .scalar() or 0
    )
    cancelados = (
        db.query(func.count(Incidente.id))
        .filter(
            Incidente.tenant_id == tenant_id,
            Incidente.estado == EstadoIncidente.CANCELADO,
            Incidente.deleted == False,
        )
        .scalar() or 0
    )
    porcentaje = round(cancelados / total * 100, 2) if total > 0 else 0.0
    return CasosCanceladosSalida(
        total_cancelados=cancelados,
        porcentaje_del_total=porcentaje,
        total_incidentes=total,
    )


def calcular_sla_cumplimiento(db: Session, tenant_id: int) -> SlaCumplimientoSalida:
    """
    Porcentaje de ordenes cuyo tiempo real de llegada (en segundos) es menor o igual
    a OrdenServicio.tiempo_estimado_llegada (entero en segundos).
    Solo evalua ordenes con fecha_hora_llegada registrada.
    """
    cumple_sla = case(
        (
            func.extract("epoch", OrdenServicio.fecha_hora_llegada - OrdenServicio.fecha_hora)
            <= OrdenServicio.tiempo_estimado_llegada,
            1,
        ),
        else_=0,
    )

    result = (
        db.query(
            func.count(OrdenServicio.id).label("total_con_llegada"),
            func.sum(cumple_sla).label("dentro_sla"),
        )
        .join(Cotizacion, Cotizacion.id == OrdenServicio.cotizacion_id)
        .join(AsignacionCandidato, AsignacionCandidato.id == Cotizacion.asignacion_candidato_id)
        .join(Incidente, Incidente.id == AsignacionCandidato.incidente_id)
        .filter(
            Incidente.tenant_id == tenant_id,
            OrdenServicio.fecha_hora_llegada.isnot(None),
            Incidente.deleted == False,
            OrdenServicio.deleted == False,
            Cotizacion.deleted == False,
            AsignacionCandidato.deleted == False,
        )
        .one()
    )

    total = result.total_con_llegada or 0
    dentro = int(result.dentro_sla or 0)
    porcentaje = round(dentro / total * 100, 2) if total > 0 else 0.0

    return SlaCumplimientoSalida(
        total_ordenes_con_llegada=total,
        ordenes_dentro_sla=dentro,
        porcentaje_cumplimiento=porcentaje,
    )
