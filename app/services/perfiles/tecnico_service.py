import math
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import hash_password
from app.models.cuentas.usuario import Usuario
from app.services.cuentas.usuario_service import verificar_username_disponible
from app.models.perfiles.taller import Taller
from app.models.perfiles.tecnico import Tecnico
from app.schemas.perfiles.tecnico import TecnicoCrear, TecnicoActualizar


def obtener_rol_por_nombre(db: Session, nombre: str):
    from app.models.cuentas.rol import Rol
    return db.query(Rol).filter(Rol.nombre == nombre, Rol.deleted == False).first()


def crear(db: Session, data: TecnicoCrear) -> Tecnico:
    verificar_username_disponible(db, data.username)
    rol = obtener_rol_por_nombre(db, "tecnico")
    usuario = Usuario(
        username=data.username,
        password=hash_password(data.password),
        rol_id=rol.id,
        tenant_id=data.tenant_id,
    )
    db.add(usuario)
    db.flush()

    tecnico = Tecnico(
        nombre=data.nombre,
        apellido=data.apellido,
        telefono=data.telefono,
        taller_id=data.taller_id,
        usuario_id=usuario.id,
    )
    db.add(tecnico)
    db.commit()
    db.refresh(tecnico)
    return tecnico


def obtener_por_taller(db: Session, taller_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = db.query(Tecnico).filter(Tecnico.taller_id == taller_id, Tecnico.deleted == False)
    total = query.count()
    datos = query.offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_tenant(db: Session, tenant_id: int, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    query = (
        db.query(Tecnico)
        .join(Taller, Tecnico.taller_id == Taller.id)
        .filter(Taller.tenant_id == tenant_id, Tecnico.deleted == False)
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


def obtener_por_id(db: Session, tecnico_id: int) -> Tecnico | None:
    return db.query(Tecnico).filter(Tecnico.id == tecnico_id, Tecnico.deleted == False).first()


def actualizar(db: Session, tecnico_id: int, data: TecnicoActualizar) -> Tecnico | None:
    tecnico = obtener_por_id(db, tecnico_id)
    if not tecnico:
        return None
    if data.nombre is not None:
        tecnico.nombre = data.nombre
    if data.apellido is not None:
        tecnico.apellido = data.apellido
    if data.telefono is not None:
        tecnico.telefono = data.telefono
    tecnico.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tecnico)
    return tecnico


def eliminar(db: Session, tecnico_id: int) -> Tecnico | None:
    tecnico = obtener_por_id(db, tecnico_id)
    if not tecnico:
        return None
    tecnico.soft_delete()
    usuario = db.query(Usuario).filter(Usuario.id == tecnico.usuario_id).first()
    if usuario:
        usuario.soft_delete()
    db.commit()
    return tecnico
