from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.cuentas.rol import RolCrear, RolActualizar, RolSalida, RolDetalle
from app.services.cuentas import rol_service

router = APIRouter(prefix="/roles", tags=["Roles"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=PaginacionSalida[RolSalida])
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return rol_service.obtener_todos(db, pagina, limite)


@router.get("/tenant/{tenant_id}", response_model=PaginacionSalida[RolSalida])
def listar_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return rol_service.obtener_por_tenant(db, tenant_id, pagina, limite)


@router.get("/{rol_id}", response_model=RolDetalle)
def obtener(rol_id: int, db: Session = Depends(get_db)):
    rol = rol_service.obtener_por_id(db, rol_id)
    if not rol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    return rol


@router.post("/", response_model=RolSalida, status_code=status.HTTP_201_CREATED)
def crear(data: RolCrear, db: Session = Depends(get_db)):
    return rol_service.crear(db, data)


@router.put("/{rol_id}", response_model=RolSalida)
def actualizar(rol_id: int, data: RolActualizar, db: Session = Depends(get_db)):
    rol = rol_service.actualizar(db, rol_id, data)
    if not rol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    return rol


@router.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(rol_id: int, db: Session = Depends(get_db)):
    rol = rol_service.eliminar(db, rol_id)
    if not rol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")