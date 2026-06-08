from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.cuentas.usuario import UsuarioCrear, UsuarioActualizar, UsuarioSalida, FcmTokenRegistrar
from app.services.cuentas import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=PaginacionSalida[UsuarioSalida])
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return usuario_service.obtener_todos(db, pagina, limite)


@router.get("/buscar", response_model=list[UsuarioSalida])
def buscar(tenant_id: int, username: str, db: Session = Depends(get_db)):
    return usuario_service.buscar_por_username(db, tenant_id, username)


@router.get("/tenant/{tenant_id}", response_model=PaginacionSalida[UsuarioSalida])
def listar_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return usuario_service.obtener_por_tenant(db, tenant_id, pagina, limite)


@router.get("/{usuario_id}", response_model=UsuarioSalida)
def obtener(usuario_id: int, db: Session = Depends(get_db)):
    usuario = usuario_service.obtener_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


@router.post("/", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED)
def crear(data: UsuarioCrear, db: Session = Depends(get_db)):
    return usuario_service.crear(db, data)


@router.put("/{usuario_id}", response_model=UsuarioSalida)
def actualizar(usuario_id: int, data: UsuarioActualizar, db: Session = Depends(get_db)):
    usuario = usuario_service.actualizar(db, usuario_id, data)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


@router.patch("/{usuario_id}/fcm-token", status_code=status.HTTP_204_NO_CONTENT)
def registrar_fcm_token(usuario_id: int, data: FcmTokenRegistrar, db: Session = Depends(get_db)):
    usuario = usuario_service.registrar_fcm_token(db, usuario_id, data.fcm_token)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(usuario_id: int, db: Session = Depends(get_db)):
    usuario = usuario_service.eliminar(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")