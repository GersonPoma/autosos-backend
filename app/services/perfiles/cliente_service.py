import math
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import hash_password
from app.models.cuentas.usuario import Usuario
from app.services.cuentas.usuario_service import verificar_username_disponible
from app.models.perfiles.cliente import Cliente
from app.schemas.perfiles.cliente import ClienteRegistrar, ClienteActualizar


def obtener_rol_por_nombre(db: Session, nombre: str):
    from app.models.cuentas.rol import Rol
    return db.query(Rol).filter(Rol.nombre == nombre, Rol.deleted == False).first()


def registrar(db: Session, data: ClienteRegistrar) -> Cliente:
    verificar_username_disponible(db, data.username)
    rol = obtener_rol_por_nombre(db, "cliente")
    usuario = Usuario(
        username=data.username,
        password=hash_password(data.password),
        rol_id=rol.id,
    )
    db.add(usuario)
    db.flush()

    cliente = Cliente(
        nombre=data.nombre,
        apellido=data.apellido,
        fecha_nacimiento=data.fecha_nacimiento,
        email=data.email,
        telefono=data.telefono,
        usuario_id=usuario.id,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def obtener_todos(db: Session, pagina: int = 1, limite: int = 10) -> PaginacionSalida:
    skip = (pagina - 1) * limite
    total = db.query(Cliente).filter(Cliente.deleted == False).count()
    datos = db.query(Cliente).filter(Cliente.deleted == False).offset(skip).limit(limite).all()
    return PaginacionSalida(
        datos=datos,
        total=total,
        pagina=pagina,
        limite=limite,
        total_paginas=math.ceil(total / limite) if limite else 1,
    )


def obtener_por_id(db: Session, cliente_id: int) -> Cliente | None:
    return db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.deleted == False).first()


def actualizar(db: Session, cliente_id: int, data: ClienteActualizar) -> Cliente | None:
    cliente = obtener_por_id(db, cliente_id)
    if not cliente:
        return None
    if data.nombre is not None:
        cliente.nombre = data.nombre
    if data.apellido is not None:
        cliente.apellido = data.apellido
    if data.fecha_nacimiento is not None:
        cliente.fecha_nacimiento = data.fecha_nacimiento
    if data.email is not None:
        cliente.email = data.email
    if data.telefono is not None:
        cliente.telefono = data.telefono
    cliente.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cliente)
    return cliente


def eliminar(db: Session, cliente_id: int) -> Cliente | None:
    cliente = obtener_por_id(db, cliente_id)
    if not cliente:
        return None
    cliente.soft_delete()
    usuario = db.query(Usuario).filter(Usuario.id == cliente.usuario_id).first()
    if usuario:
        usuario.soft_delete()
    db.commit()
    return cliente
