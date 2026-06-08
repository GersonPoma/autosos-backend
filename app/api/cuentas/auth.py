from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.cuentas.usuario import LoginRequest, TokenResponse
from app.services.cuentas.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def obtener_datos_perfil(db: Session, usuario):
    from app.models.perfiles.cliente import Cliente
    from app.models.perfiles.tecnico import Tecnico
    from app.models.perfiles.taller import Taller
    from app.models.cuentas.privilegio import Privilegio
    from app.models.cuentas.rol_privilegio import rol_privilegio

    rol_nombre = usuario.rol.nombre
    id_perfil = None
    id_taller = None

    if rol_nombre == "cliente":
        perfil = db.query(Cliente).filter(Cliente.usuario_id == usuario.id).first()
        if perfil:
            id_perfil = perfil.id
    else:
        tecnico = db.query(Tecnico).filter(Tecnico.usuario_id == usuario.id).first()
        if tecnico:
            id_perfil = tecnico.id
            id_taller = tecnico.taller_id
        else:
            taller = db.query(Taller).filter(Taller.usuario_id == usuario.id, Taller.deleted == False).first()
            if taller:
                id_taller = taller.id

    privilegios = db.query(Privilegio).join(
        rol_privilegio, Privilegio.id == rol_privilegio.c.privilegio_id
    ).filter(
        rol_privilegio.c.rol_id == usuario.rol_id,
        Privilegio.deleted == False,
    ).all()

    tenant_id = None if rol_nombre == "cliente" else usuario.tenant_id

    return id_perfil, id_taller, rol_nombre, [p.nombre for p in privilegios], tenant_id


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    usuario = authenticate_user(db, request.username, request.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    id_perfil, id_taller, rol_nombre, privilegios, tenant_id = obtener_datos_perfil(db, usuario)
    token = create_access_token(data={"sub": str(usuario.id)})

    return TokenResponse(
        access_token=token,
        id_usuario=usuario.id,
        id_perfil=id_perfil,
        id_taller=id_taller,
        tenant_id=tenant_id,
        rol=rol_nombre,
        super_usuario=usuario.super_usuario,
        privilegios=privilegios,
    )
