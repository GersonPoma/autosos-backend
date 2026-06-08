import math
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.perfiles.vehiculo import Vehiculo
from app.schemas.perfiles.vehiculo import VehiculoCrear, VehiculoActualizar


def obtener_todos(db: Session, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    total = db.query(Vehiculo).filter(Vehiculo.deleted == False).count()
    datos = db.query(Vehiculo).filter(Vehiculo.deleted == False).offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_cliente(db: Session, cliente_id: int) -> Vehiculo | None:
    return db.query(Vehiculo).filter(Vehiculo.cliente_id == cliente_id, Vehiculo.deleted == False).first()


def crear(db: Session, data: VehiculoCrear) -> Vehiculo:
    vehiculo = Vehiculo(
        placa=data.placa,
        modelo=data.modelo,
        color=data.color,
        cliente_id=data.cliente_id,
    )
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def actualizar(db: Session, cliente_id: int, data: VehiculoActualizar) -> Vehiculo | None:
    vehiculo = obtener_por_cliente(db, cliente_id)
    if not vehiculo:
        return None
    if data.placa is not None:
        vehiculo.placa = data.placa
    if data.modelo is not None:
        vehiculo.modelo = data.modelo
    if data.color is not None:
        vehiculo.color = data.color
    vehiculo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


def eliminar(db: Session, cliente_id: int) -> Vehiculo | None:
    vehiculo = obtener_por_cliente(db, cliente_id)
    if not vehiculo:
        return None
    vehiculo.soft_delete()
    db.commit()
    return vehiculo
