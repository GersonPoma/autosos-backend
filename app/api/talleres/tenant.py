from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.talleres.tenant import TenantCrear, TenantActualizar, TenantSalida
from app.services.talleres import tenant_service

router = APIRouter(prefix="/tenants", tags=["Tenants"])

_auth = [Depends(get_current_user)]


@router.post("/", response_model=TenantSalida, status_code=status.HTTP_201_CREATED)
def crear(data: TenantCrear, db: Session = Depends(get_db)):
    return tenant_service.crear(db, data)


@router.get("/", response_model=PaginacionSalida[TenantSalida], dependencies=_auth)
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return tenant_service.listar(db, pagina, limite)


@router.get("/{tenant_id}", response_model=TenantSalida, dependencies=_auth)
def obtener(tenant_id: int, db: Session = Depends(get_db)):
    tenant = tenant_service.obtener(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


@router.put("/{tenant_id}", response_model=TenantSalida, dependencies=_auth)
def actualizar(tenant_id: int, data: TenantActualizar, db: Session = Depends(get_db)):
    tenant = tenant_service.actualizar(db, tenant_id, data)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_auth)
def eliminar(tenant_id: int, db: Session = Depends(get_db)):
    resultado = tenant_service.eliminar(db, tenant_id)
    if not resultado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")