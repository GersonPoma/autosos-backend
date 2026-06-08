from datetime import datetime
import math

from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.models.cuentas.rol import Rol
from app.schemas.cuentas.rol import RolCrear, RolActualizar


def obtener_todos(db: Session, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    total = db.query(Rol).filter(Rol.deleted == False).count()
    datos = db.query(Rol).filter(Rol.deleted == False).offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_id(db: Session, rol_id: int) -> Rol | None:
    return db.query(Rol).filter(Rol.id == rol_id, Rol.deleted == False).first()


def crear(db: Session, data: RolCrear) -> Rol:
    rol = Rol(nombre=data.nombre, tenant_id=data.tenant_id)
    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


def actualizar(db: Session, rol_id: int, data: RolActualizar) -> Rol | None:
    rol = obtener_por_id(db, rol_id)
    if not rol:
        return None
    rol.nombre = data.nombre
    rol.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rol)
    return rol


def obtener_por_tenant(db: Session, tenant_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(Rol).filter(Rol.tenant_id == tenant_id, Rol.deleted == False)
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def eliminar(db: Session, rol_id: int) -> Rol | None:
    rol = obtener_por_id(db, rol_id)
    if not rol:
        return None
    rol.soft_delete()
    db.commit()
    return rol