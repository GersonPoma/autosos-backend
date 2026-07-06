import math
from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.pagos.detalle_orden import DetalleOrden
from app.models.perfiles.servicio_taller import ServicioTaller
from app.models.talleres.orden_servicio import OrdenServicio
from app.schemas.pagos.detalle_orden import DetalleOrdenActualizar, DetalleOrdenEntrada, DetalleOrdenItemEntrada


def _mapear_salida(detalle: DetalleOrden) -> dict:
    return {
        "id": detalle.id,
        "servicio_taller_id": detalle.servicio_taller_id,
        "servicio_nombre": detalle.servicio_nombre,
        "cantidad": detalle.cantidad,
        "precio_unitario": detalle.precio_unitario,
        "subtotal": detalle.subtotal,
        "orden_servicio_id": detalle.orden_servicio_id,
    }


def inicializar_desde_cotizacion(db: Session, orden_servicio_id: int) -> List[dict]:
    orden = db.query(OrdenServicio).filter(
        OrdenServicio.id == orden_servicio_id,
    ).first()
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de servicio no encontrada")

    cotizacion = orden.cotizacion
    if not cotizacion or not cotizacion.detalles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La orden no tiene cotización con detalles")

    existentes = db.query(DetalleOrden).filter(
        DetalleOrden.orden_servicio_id == orden_servicio_id,
        DetalleOrden.deleted == False,
    ).all()
    if existentes:
        return [_mapear_salida(d) for d in existentes]

    detalles = []
    for dc in cotizacion.detalles:
        if dc.deleted:
            continue
        subtotal = round(dc.precio_unitario * dc.cantidad, 2)
        detalle = DetalleOrden(
            cantidad=dc.cantidad,
            precio_unitario=dc.precio_unitario,
            subtotal=subtotal,
            orden_servicio_id=orden_servicio_id,
            servicio_taller_id=dc.servicio_taller_id,
        )
        db.add(detalle)
        detalles.append(detalle)

    db.flush()
    for d in detalles:
        db.refresh(d)
    db.commit()
    return [_mapear_salida(d) for d in detalles]


def crear_lote(
    db: Session,
    orden_servicio_id: int,
    items: List[DetalleOrdenItemEntrada],
) -> Tuple[List[DetalleOrden], float]:
    if not items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe incluir al menos un servicio",
        )
    detalles = []
    total = 0.0
    for item in items:
        servicio = db.query(ServicioTaller).filter(
            ServicioTaller.id == item.servicio_taller_id,
            ServicioTaller.deleted == False,
        ).first()
        if not servicio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ServicioTaller {item.servicio_taller_id} no encontrado",
            )
        subtotal = round(servicio.precio * item.cantidad, 2)
        detalle = DetalleOrden(
            cantidad=item.cantidad,
            precio_unitario=servicio.precio,
            subtotal=subtotal,
            orden_servicio_id=orden_servicio_id,
            servicio_taller_id=item.servicio_taller_id,
        )
        db.add(detalle)
        total += subtotal
        detalles.append(detalle)
    db.flush()
    for d in detalles:
        db.refresh(d)
    return detalles, total


def crear(db: Session, entrada: DetalleOrdenEntrada) -> dict:
    detalle = DetalleOrden(
        cantidad=entrada.cantidad,
        precio_unitario=entrada.precio_unitario,
        subtotal=entrada.subtotal,
        orden_servicio_id=entrada.orden_servicio_id,
        servicio_taller_id=entrada.servicio_taller_id,
    )
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    return _mapear_salida(detalle)


def actualizar(db: Session, detalle_id: int, datos: DetalleOrdenActualizar) -> dict:
    detalle = db.query(DetalleOrden).filter(
        DetalleOrden.id == detalle_id,
        DetalleOrden.deleted == False,
    ).first()
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de orden no encontrado")

    if datos.cantidad is not None:
        detalle.cantidad = datos.cantidad
    if datos.precio_unitario is not None:
        detalle.precio_unitario = datos.precio_unitario
    detalle.subtotal = round(detalle.precio_unitario * detalle.cantidad, 2)

    db.commit()
    db.refresh(detalle)
    return _mapear_salida(detalle)


def obtener_por_orden(db: Session, orden_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(DetalleOrden).filter(
        DetalleOrden.orden_servicio_id == orden_id,
        DetalleOrden.deleted == False,
    )
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=[_mapear_salida(d) for d in datos],
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_id(db: Session, detalle_id: int):
    detalle = db.query(DetalleOrden).filter(
        DetalleOrden.id == detalle_id,
        DetalleOrden.deleted == False,
    ).first()
    if not detalle:
        return None
    return _mapear_salida(detalle)


def eliminar(db: Session, detalle_id: int) -> bool:
    detalle = db.query(DetalleOrden).filter(
        DetalleOrden.id == detalle_id,
        DetalleOrden.deleted == False,
    ).first()
    if not detalle:
        return False
    detalle.soft_delete()
    db.commit()
    return True