import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.perfiles.taller import Taller
from app.schemas.perfiles.taller import TallerRegistrar, TallerActualizar, TallerEstadoActualizar



def registrar(db: Session, data: TallerRegistrar) -> Taller:
    taller = Taller(
        nombre=data.nombre,
        telefono=data.telefono,
        direccion=data.direccion,
        latitud=data.latitud,
        longitud=data.longitud,
        usuario_id=data.usuario_id,
        tenant_id=data.tenant_id,
    )
    db.add(taller)
    db.commit()
    db.refresh(taller)
    return taller


def obtener_todos(db: Session, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    total = db.query(Taller).filter(Taller.deleted == False).count()
    datos = db.query(Taller).filter(Taller.deleted == False).offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_tenant(db: Session, tenant_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(Taller).filter(Taller.tenant_id == tenant_id, Taller.deleted == False)
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_id(db: Session, taller_id: int) -> Taller | None:
    return db.query(Taller).filter(Taller.id == taller_id, Taller.deleted == False).first()


def actualizar(db: Session, taller_id: int, data: TallerActualizar) -> Taller | None:
    taller = obtener_por_id(db, taller_id)
    if not taller:
        return None
    if data.nombre is not None:
        taller.nombre = data.nombre
    if data.telefono is not None:
        taller.telefono = data.telefono
    if data.direccion is not None:
        taller.direccion = data.direccion
    if data.latitud is not None:
        taller.latitud = data.latitud
    if data.longitud is not None:
        taller.longitud = data.longitud
    if data.disponible is not None:
        taller.disponible = data.disponible
    taller.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(taller)
    return taller


def actualizar_estado(db: Session, taller_id: int, data: TallerEstadoActualizar) -> Taller | None:
    return cambiar_disponibilidad(db, taller_id, data.disponible)


def cambiar_disponibilidad(db: Session, taller_id: int, disponible: bool) -> Taller | None:
    taller = obtener_por_id(db, taller_id)
    if not taller:
        return None

    taller.disponible = disponible
    taller.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(taller)
    return taller


def activar(db: Session, taller_id: int) -> Taller | None:
    return cambiar_disponibilidad(db, taller_id, True)


def desactivar(db: Session, taller_id: int) -> Taller | None:
    return cambiar_disponibilidad(db, taller_id, False)


def eliminar(db: Session, taller_id: int) -> Taller | None:
    taller = obtener_por_id(db, taller_id)
    if not taller:
        return None
    taller.soft_delete()
    usuario = db.query(Usuario).filter(Usuario.id == taller.usuario_id).first()
    if usuario:
        usuario.soft_delete()
    db.commit()
    return taller
