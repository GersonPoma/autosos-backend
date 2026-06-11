import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.perfiles.taller import Taller
from app.models.cuentas.usuario import Usuario
from app.models.talleres.asignacion_candidato import AsignacionCandidato, EstadoNotificacion
from app.models.talleres.cotizacion import Cotizacion
from app.models.talleres.orden_servicio import OrdenServicio, EstadoOperacion
from app.services.firebase_service import enviar_notificacion


def formatear_tiempo_hms(segundos: int) -> str:
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{horas}:{minutos}:{segs:02d}"


def _resolver(orden: OrdenServicio):
    asignacion = orden.cotizacion.asignacion_candidato if orden.cotizacion else None
    incidente = asignacion.incidente if asignacion else None
    taller = asignacion.taller if asignacion else None
    return asignacion, incidente, taller


def _mapear_orden_lista(orden: OrdenServicio) -> dict:
    asignacion, incidente, taller = _resolver(orden)
    incidente_id = incidente.id if incidente else 0

    nombre_cliente = "Desconocido"
    if incidente and incidente.usuario and incidente.usuario.cliente:
        cliente_perfil = incidente.usuario.cliente[0]
        nombre_cliente = f"{cliente_perfil.nombre} {cliente_perfil.apellido}"

    return {
        "id": orden.id,
        "incidente_id": incidente_id,
        "nombre_cliente": nombre_cliente,
        "fecha_hora": orden.fecha_hora,
        "estado": orden.estado,
        "taller_nombre": taller.nombre if taller else None,
        "transaccion_id": orden.transaccion.id if orden.transaccion else None,
    }


def _mapear_orden_salida(orden: OrdenServicio) -> dict:
    asignacion, incidente, taller = _resolver(orden)
    incidente_id = incidente.id if incidente else 0

    nombre_cliente = "Desconocido"
    if incidente and incidente.usuario and incidente.usuario.cliente:
        cliente_perfil = incidente.usuario.cliente[0]
        nombre_cliente = f"{cliente_perfil.nombre} {cliente_perfil.apellido}"

    tiene_transaccion = orden.transaccion is not None
    transaccion_id = orden.transaccion.id if tiene_transaccion else None

    return {
        "id": orden.id,
        "fecha_hora": orden.fecha_hora,
        "tiempo_estimado_llegada_segundos": orden.tiempo_estimado_llegada,
        "tiempo_estimado_llegada": formatear_tiempo_hms(orden.tiempo_estimado_llegada),
        "estado": orden.estado,
        "cotizacion_id": orden.cotizacion_id,
        "incidente_id": incidente_id,
        "nombre_cliente": nombre_cliente,
        "taller_id": taller.id if taller else None,
        "taller_nombre": taller.nombre if taller else None,
        "fecha_hora_llegada": orden.fecha_hora_llegada,
        "fecha_hora_fin": orden.fecha_hora_fin,
        "tiene_transaccion": tiene_transaccion,
        "transaccion_id": transaccion_id,
        "estrellas": orden.estrellas,
        "comentario": orden.comentario,
    }


def obtener_todos(db: Session, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(OrdenServicio).filter(OrdenServicio.deleted == False)
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=[_mapear_orden_salida(orden) for orden in datos],
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_id(db: Session, orden_id: int):
    orden = db.query(OrdenServicio).filter(
        OrdenServicio.id == orden_id,
        OrdenServicio.deleted == False,
    ).first()
    if not orden:
        return None
    return _mapear_orden_salida(orden)


def obtener_por_taller_id(db: Session, taller_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = (
        db.query(OrdenServicio)
        .join(Cotizacion, OrdenServicio.cotizacion_id == Cotizacion.id)
        .join(AsignacionCandidato, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .filter(
            AsignacionCandidato.taller_id == taller_id,
            AsignacionCandidato.estado == EstadoNotificacion.ACEPTADO,
            OrdenServicio.deleted == False,
        )
        .order_by(OrdenServicio.fecha_hora.desc())
    )
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=[_mapear_orden_lista(o) for o in datos],
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_tenant_id(db: Session, tenant_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = (
        db.query(OrdenServicio)
        .join(Cotizacion, OrdenServicio.cotizacion_id == Cotizacion.id)
        .join(AsignacionCandidato, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .join(Taller, AsignacionCandidato.taller_id == Taller.id)
        .filter(
            Taller.tenant_id == tenant_id,
            AsignacionCandidato.estado == EstadoNotificacion.ACEPTADO,
            OrdenServicio.deleted == False,
        )
        .order_by(OrdenServicio.fecha_hora.desc())
    )
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=[_mapear_orden_lista(o) for o in datos],
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_incidente_id(db: Session, incidente_id: int):
    orden = (
        db.query(OrdenServicio)
        .join(Cotizacion, OrdenServicio.cotizacion_id == Cotizacion.id)
        .join(AsignacionCandidato, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .filter(
            AsignacionCandidato.incidente_id == incidente_id,
            AsignacionCandidato.estado == EstadoNotificacion.ACEPTADO,
            OrdenServicio.deleted == False,
        )
        .first()
    )
    if not orden:
        return None
    return _mapear_orden_salida(orden)


def cambiar_estado(db: Session, orden_id: int, nuevo_estado: EstadoOperacion):
    from datetime import datetime, timezone
    orden = db.query(OrdenServicio).filter(
        OrdenServicio.id == orden_id,
        OrdenServicio.deleted == False,
    ).first()
    if not orden:
        return None
    orden.estado = nuevo_estado
    now = datetime.now(timezone.utc)
    if nuevo_estado == EstadoOperacion.DIAGNOSTICANDO and not orden.fecha_hora_llegada:
        orden.fecha_hora_llegada = now
    elif nuevo_estado == EstadoOperacion.FINALIZADO and not orden.fecha_hora_fin:
        orden.fecha_hora_fin = now
    db.commit()
    db.refresh(orden)
    return _mapear_orden_salida(orden)


def notificar_en_camino(db: Session, orden_id: int) -> bool:
    orden = db.query(OrdenServicio).filter(
        OrdenServicio.id == orden_id,
        OrdenServicio.deleted == False,
    ).first()
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Orden {orden_id} no encontrada")

    if not orden.cotizacion or not orden.cotizacion.asignacion_candidato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La orden no tiene cotización o asignación")

    incidente = orden.cotizacion.asignacion_candidato.incidente
    if not incidente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró el incidente asociado")

    usuario_cliente = db.query(Usuario).filter(
        Usuario.id == incidente.usuario_id,
        Usuario.deleted == False,
    ).first()
    if not usuario_cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró el usuario cliente")
    if not usuario_cliente.fcm_token:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El cliente no tiene token FCM registrado")

    minutos = orden.tiempo_estimado_llegada // 60
    nombre_taller = orden.cotizacion.asignacion_candidato.taller.nombre
    enviar_notificacion(
        fcm_token=usuario_cliente.fcm_token,
        titulo="¡El taller está en camino!",
        cuerpo=f"{nombre_taller} ya salió hacia tu ubicación. Tiempo estimado de llegada: {minutos} minutos.",
        data={"orden_id": str(orden.id), "incidente_id": str(incidente.id)},
    )
    return True


def calificar(db: Session, orden_id: int, estrellas: float, comentario: str | None = None):
    orden = db.query(OrdenServicio).filter(
        OrdenServicio.id == orden_id,
        OrdenServicio.deleted == False,
    ).first()
    if not orden:
        return None
    orden.estrellas = estrellas
    orden.comentario = comentario
    db.commit()
    db.refresh(orden)
    return _mapear_orden_salida(orden)