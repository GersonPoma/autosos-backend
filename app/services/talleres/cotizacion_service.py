from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cuentas.usuario import Usuario
from app.models.emergencias.incidente import EstadoIncidente
from app.models.talleres.asignacion_candidato import AsignacionCandidato, EstadoNotificacion
from app.models.talleres.cotizacion import Cotizacion, DetalleCotizacion, EstadoCotizacion
from app.models.talleres.orden_servicio import OrdenServicio, EstadoOperacion
from app.schemas.talleres.cotizacion import CotizacionCrear
from app.services.firebase_service import enviar_notificacion


def crear(db: Session, data: CotizacionCrear) -> Cotizacion:
    asignacion = db.query(AsignacionCandidato).filter(
        AsignacionCandidato.id == data.asignacion_candidato_id,
        AsignacionCandidato.deleted == False,
    ).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
    if asignacion.estado != EstadoNotificacion.NOTIFICADO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La asignación ya no está en estado notificado")

    costo_total = round(sum(d.precio_unitario * d.cantidad for d in data.detalles), 2)
    distancia_km = asignacion.distancia_km
    tiempo_estimado_llegada = (int(distancia_km * 3) + 5) * 60

    cotizacion = Cotizacion(
        tipo_atencion=data.tipo_atencion,
        distancia_km=distancia_km,
        tiempo_estimado_llegada=tiempo_estimado_llegada,
        costo_total=costo_total,
        fecha_validez=data.fecha_validez,
        asignacion_candidato_id=data.asignacion_candidato_id,
    )
    db.add(cotizacion)
    db.flush()

    for item in data.detalles:
        detalle = DetalleCotizacion(
            cotizacion_id=cotizacion.id,
            servicio_taller_id=item.servicio_taller_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            subtotal=round(item.precio_unitario * item.cantidad, 2),
        )
        db.add(detalle)

    asignacion.estado = EstadoNotificacion.COTIZADO
    db.commit()
    db.refresh(cotizacion)

    usuario_cliente = db.query(Usuario).filter(
        Usuario.id == asignacion.incidente.usuario_id,
        Usuario.deleted == False,
    ).first()
    if usuario_cliente and usuario_cliente.fcm_token:
        taller_nombre = asignacion.taller.nombre if asignacion.taller else "Un taller"
        enviar_notificacion(
            fcm_token=usuario_cliente.fcm_token,
            titulo="Nueva cotización recibida",
            cuerpo=f"{taller_nombre} te envió una cotización por Bs. {costo_total}.",
            data={
                "cotizacion_id": str(cotizacion.id),
                "incidente_id": str(asignacion.incidente_id),
            },
        )

    return cotizacion


def listar_por_incidente(db: Session, incidente_id: int) -> list[Cotizacion]:
    return (
        db.query(Cotizacion)
        .join(AsignacionCandidato, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .filter(
            AsignacionCandidato.incidente_id == incidente_id,
            Cotizacion.deleted == False,
        )
        .all()
    )


def obtener_por_id(db: Session, cotizacion_id: int) -> Cotizacion | None:
    return db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id, Cotizacion.deleted == False).first()


def aceptar(db: Session, cotizacion_id: int) -> dict:
    cotizacion = obtener_por_id(db, cotizacion_id)
    if not cotizacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    if cotizacion.estado_cotizacion != EstadoCotizacion.PENDIENTE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cotización ya no está pendiente")

    asignacion = cotizacion.asignacion_candidato
    incidente = asignacion.incidente

    cotizacion.estado_cotizacion = EstadoCotizacion.ACEPTADA
    asignacion.estado = EstadoNotificacion.ACEPTADO
    incidente.estado = EstadoIncidente.EN_PROCESO
    incidente.tenant_id = asignacion.taller.tenant_id

    otras = db.query(AsignacionCandidato).filter(
        AsignacionCandidato.incidente_id == incidente.id,
        AsignacionCandidato.id != asignacion.id,
        AsignacionCandidato.deleted == False,
    ).all()
    for otra in otras:
        otra.estado = EstadoNotificacion.RECHAZADO
        if otra.cotizacion:
            otra.cotizacion.estado_cotizacion = EstadoCotizacion.RECHAZADA

    tiempo_calculado = (int(cotizacion.distancia_km * 3) + 5) * 60
    orden = OrdenServicio(
        cotizacion_id=cotizacion.id,
        tiempo_estimado_llegada=tiempo_calculado,
        estado=EstadoOperacion.EN_CAMINO,
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)

    usuario_taller = asignacion.taller.usuario if asignacion.taller else None
    if usuario_taller and usuario_taller.fcm_token:
        enviar_notificacion(
            fcm_token=usuario_taller.fcm_token,
            titulo="¡Cotización aceptada!",
            cuerpo="El cliente aceptó tu cotización. Ya puedes dirigirte al lugar.",
            data={"orden_id": str(orden.id), "incidente_id": str(incidente.id)},
        )

    return {
        "mensaje": "Cotización aceptada. Orden de servicio creada.",
        "orden_servicio_id": orden.id,
        "tiempo_estimado_llegada": tiempo_calculado,
    }


def rechazar(db: Session, cotizacion_id: int) -> Cotizacion:
    cotizacion = obtener_por_id(db, cotizacion_id)
    if not cotizacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    cotizacion.estado_cotizacion = EstadoCotizacion.RECHAZADA
    cotizacion.asignacion_candidato.estado = EstadoNotificacion.RECHAZADO
    db.commit()
    db.refresh(cotizacion)
    return cotizacion