import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.emergencias.incidente import EstadoIncidente, Incidente
from app.models.emergencias.evidencia import Evidencia
from app.models.talleres.asignacion_candidato import AsignacionCandidato, EstadoNotificacion
from app.schemas.emergencias.incidente import IncidenteActualizar, IncidenteCrear


def crear(db: Session, data: IncidenteCrear, usuario_id: int) -> Incidente:
    incidente = Incidente()
    incidente.latitud = data.latitud
    incidente.longitud = data.longitud
    incidente.usuario_id = usuario_id
    db.add(incidente)
    db.commit()
    db.refresh(incidente)
    return incidente


def obtener_por_id(db: Session, incidente_id: int):
    return db.query(Incidente).filter(
        Incidente.id == incidente_id,
        Incidente.deleted == False,
    ).first()


def obtener_por_usuario_id(db: Session, usuario_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(Incidente).filter(
        Incidente.usuario_id == usuario_id,
        Incidente.deleted == False,
    )
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_activo_por_usuario(db: Session, usuario_id: int) -> Incidente | None:
    return (
        db.query(Incidente)
        .filter(
            Incidente.usuario_id == usuario_id,
            Incidente.estado == EstadoIncidente.EN_PROCESO,
            Incidente.deleted == False,
        )
        .order_by(Incidente.fecha_hora.desc())
        .first()
    )


def actualizar(db: Session, incidente_id: int, data: IncidenteActualizar):
    incidente = obtener_por_id(db, incidente_id)
    if not incidente:
        return None

    if data.latitud is not None:
        incidente.latitud = data.latitud
    if data.longitud is not None:
        incidente.longitud = data.longitud
    if data.estado is not None:
        incidente.estado = data.estado
    if data.prioridad is not None:
        incidente.prioridad = data.prioridad

    incidente.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incidente)
    return incidente


def obtener_aceptados_por_tenant(db: Session, tenant_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(Incidente).filter(
        Incidente.tenant_id == tenant_id,
        Incidente.deleted == False,
    )
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def cancelar_incidente(db: Session, incidente_id: int):
    incidente = obtener_por_id(db, incidente_id)
    if not incidente:
        return None

    if incidente.estado != EstadoIncidente.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede cancelar un incidente en estado Pendiente",
        )

    #Cambiar AsignacionCandidato a REZACHADO
    db.query(AsignacionCandidato).filter(
        AsignacionCandidato.incidente_id == incidente_id,
        AsignacionCandidato.estado == EstadoNotificacion.NOTIFICADO,
        AsignacionCandidato.deleted == False,
    ).update({"estado": EstadoNotificacion.RECHAZADO}, synchronize_session=False)

    incidente.estado = EstadoIncidente.CANCELADO
    incidente.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incidente)
    return incidente

def obtener_detalle_incidente(db: Session, incidente_id: int) -> dict:
    incidente = obtener_por_id(db, incidente_id)
    if not incidente:
        return None

    # Recopilar Evidencias
    evidencias = db.query(Evidencia).filter(Evidencia.incidente_id == incidente_id, Evidencia.deleted == False).all()
    evidencias_list = [{"id": e.id, "url": e.url, "tipo": e.tipo, "fecha_subida": e.fecha} for e in evidencias]

    # Recopilar Asignación al taller (Aceptado)
    asignacion = db.query(AsignacionCandidato).filter(
        AsignacionCandidato.incidente_id == incidente_id,
        AsignacionCandidato.estado == EstadoNotificacion.ACEPTADO
    ).first()

    taller_info = None
    orden_info = None
    transaccion_info = None

    if asignacion:
        taller = asignacion.taller
        if taller:
            taller_info = {
                "id": taller.id,
                "nombre": taller.nombre,
                "telefono": taller.telefono,
                "direccion": taller.direccion,
                "latitud": taller.latitud,
                "longitud": taller.longitud
            }

        orden = asignacion.orden_servicio
        if orden:
            orden_info = {
                "id": orden.id,
                "estado": orden.estado,
                "tiempo_estimado_segundos": orden.tiempo_estimado_llegada,
                "fecha_hora": orden.fecha_hora,
                "detalles": [
                    {
                        "id": d.id,
                        "nombre_servicio": d.servicio_taller.nombre if d.servicio_taller else "Desconocido",
                        "categoria": d.servicio_taller.categoria if d.servicio_taller else "Desconocido",
                        "precio_cobrado": d.precio_cobrado,
                        "comentario": d.comentario,
                        "subtotal": d.precio_cobrado
                    } for d in orden.detalles
                ] if orden.detalles else []
            }

            transaccion = orden.transaccion
            if transaccion:
                transaccion_info = {
                    "id": transaccion.id,
                    "monto_cobrado": transaccion.monto_cobrado,
                    "monto_comision": transaccion.monto_comision,
                    "estado": transaccion.estado,
                    "metodo_pago": transaccion.metodo_pago,
                    "fecha_hora": transaccion.fecha_hora
                }

    # Recopilar análisis de IA (si existe)
    analisis = incidente.analisis
    analisis_info = None
    if analisis:
        analisis_info = {
            "id": analisis.id,
            "transcripcion_audio": analisis.transcripcion_audio,
            "categoria_problema": analisis.categoria_problema,
            "danios_identificados": analisis.danios_identificados,
            "resumen_estructurado": analisis.resumen_estructurado,
            "fecha_analisis": analisis.created_at
        }

    return {
        "incidente": {
            "id": incidente.id,
            "latitud": incidente.latitud,
            "longitud": incidente.longitud,
            "estado": incidente.estado,
            "prioridad": incidente.prioridad,
            "fecha_hora": incidente.fecha_hora,
        },
        "evidencias": evidencias_list,
        "analisis": analisis_info,
        "taller_atendio": taller_info,
        "orden_servicio": orden_info,
        "transaccion": transaccion_info
    }
