import math
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import hash_password
from app.models.cuentas.rol import Rol
from app.models.cuentas.usuario import Usuario
from app.models.talleres.tenant import Tenant
from app.schemas.talleres.tenant import TenantCrear, TenantActualizar


def listar(db: Session, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    total = db.query(Tenant).filter(Tenant.deleted == False).count()
    datos = db.query(Tenant).filter(Tenant.deleted == False).offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener(db: Session, tenant_id: int) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.deleted == False).first()


def crear(db: Session, data: TenantCrear) -> Tenant:
    if db.query(Usuario).filter(Usuario.username == data.username, Usuario.deleted == False).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El username '{data.username}' ya está en uso",
        )

    rol = db.query(Rol).filter(Rol.nombre == "admin_tenant", Rol.deleted == False).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el rol 'admin_tenant'",
        )

    tenant = Tenant(nombre=data.nombre, activo=data.activo)
    db.add(tenant)
    db.flush()

    usuario = Usuario(
        username=data.username,
        password=hash_password(data.password),
        rol_id=rol.id,
        tenant_id=tenant.id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(tenant)
    return tenant


def actualizar(db: Session, tenant_id: int, data: TenantActualizar) -> Tenant | None:
    tenant = obtener(db, tenant_id)
    if not tenant:
        return None
    if data.nombre is not None:
        tenant.nombre = data.nombre
    if data.activo is not None:
        tenant.activo = data.activo
    tenant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tenant)
    return tenant


def eliminar(db: Session, tenant_id: int) -> Tenant | None:
    tenant = obtener(db, tenant_id)
    if not tenant:
        return None
    tenant.soft_delete()
    db.commit()
    return tenant