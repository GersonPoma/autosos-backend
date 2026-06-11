import math
import stripe
import os
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.emergencias.incidente import EstadoIncidente
from app.models.pagos.transaccion import EstadoTransaccion, Transaccion, MetodoPago
from app.models.talleres.asignacion_candidato import AsignacionCandidato
from app.models.talleres.orden_servicio import EstadoOperacion, OrdenServicio
from fastapi import HTTPException, status
from app.models.pagos.detalle_orden import DetalleOrden
from app.schemas.pagos.transaccion import TransaccionEntrada
from app.services.pagos import service_detalle_orden


def generar_pago(
    db: Session,
    orden_servicio_id: int,
    tenant_id: int | None = None,
) -> dict:
    detalles = db.query(DetalleOrden).filter(
        DetalleOrden.orden_servicio_id == orden_servicio_id,
        DetalleOrden.deleted == False,
    ).all()
    if not detalles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La orden no tiene detalles. Inicialice primero desde la cotización.",
        )

    monto_cobrado = round(sum(d.subtotal for d in detalles), 2)
    monto_comision = round(monto_cobrado * 0.10, 2)
    transaccion = Transaccion(
        monto_cobrado=monto_cobrado,
        monto_comision=monto_comision,
        orden_servicio_id=orden_servicio_id,
        tenant_id=tenant_id,
    )
    db.add(transaccion)
    orden = db.query(OrdenServicio).filter(OrdenServicio.id == orden_servicio_id).first()
    if orden:
        orden.estado = EstadoOperacion.FINALIZADO
    db.commit()
    db.refresh(transaccion)
    return {
        "transaccion": transaccion,
        "detalles": [service_detalle_orden._mapear_salida(d) for d in detalles],
    }


def crear(db: Session, entrada: TransaccionEntrada) -> Transaccion:
    transaccion = Transaccion(
        monto_cobrado=entrada.monto_cobrado,
        monto_comision=entrada.monto_comision,
        metodo_pago=entrada.metodo_pago,
        orden_servicio_id=entrada.orden_servicio_id,
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion


def obtener_por_taller(db: Session, taller_id: int, pagina: int = 1, limite: int = 10):
    skip = (pagina - 1) * limite
    from app.models.talleres.cotizacion import Cotizacion
    query = (
        db.query(Transaccion)
        .join(OrdenServicio, Transaccion.orden_servicio_id == OrdenServicio.id)
        .join(Cotizacion, OrdenServicio.cotizacion_id == Cotizacion.id)
        .join(AsignacionCandidato, Cotizacion.asignacion_candidato_id == AsignacionCandidato.id)
        .filter(AsignacionCandidato.taller_id == taller_id, Transaccion.deleted == False)
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


def obtener_por_tenant(db: Session, tenant_id: int, pagina: int = 1, limite: int = 10):
    skip = (pagina - 1) * limite
    query = db.query(Transaccion).filter(Transaccion.tenant_id == tenant_id, Transaccion.deleted == False)
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_orden(db: Session, orden_id: int) -> Transaccion | None:
    return db.query(Transaccion).filter(
        Transaccion.orden_servicio_id == orden_id,
        Transaccion.deleted == False,
    ).first()


def obtener_por_id(db: Session, transaccion_id: int) -> Transaccion | None:
    return db.query(Transaccion).filter(
        Transaccion.id == transaccion_id,
        Transaccion.deleted == False,
    ).first()


def actualizar_estado(db: Session, transaccion_id: int, nuevo_estado: EstadoTransaccion) -> Transaccion | None:
    t = db.query(Transaccion).filter(
        Transaccion.id == transaccion_id,
        Transaccion.deleted == False,
    ).first()
    if not t:
        return None
    t.estado = nuevo_estado

    if nuevo_estado == EstadoTransaccion.PAGADO and t.orden_servicio and t.orden_servicio.cotizacion and t.orden_servicio.cotizacion.asignacion_candidato and t.orden_servicio.cotizacion.asignacion_candidato.incidente:
        t.orden_servicio.cotizacion.asignacion_candidato.incidente.estado = EstadoIncidente.ATENDIDO

    db.commit()
    db.refresh(t)
    return t


def crear_payment_intent(db: Session, transaccion_id: int) -> dict:
    t = db.query(Transaccion).filter(
        Transaccion.id == transaccion_id,
        Transaccion.deleted == False,
    ).first()
    if not t:
        raise ValueError("Transacción no encontrada")

    if t.estado == EstadoTransaccion.PAGADO:
        raise ValueError("Esta transacción ya fue pagada")

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

    monto_en_centavos = int(t.monto_cobrado * 100)

    try:
        intent = stripe.PaymentIntent.create(
            amount=monto_en_centavos,
            currency="bob",
        )

        t.metodo_pago = MetodoPago.TARJETA
        db.commit()

        return {
            "client_secret": intent.client_secret,
            "publishable_key": publishable_key
        }
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error al generar pago en Stripe: {str(e)}")