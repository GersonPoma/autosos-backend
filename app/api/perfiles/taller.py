from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.perfiles.taller import TallerRegistrar, TallerActualizar, TallerEstadoActualizar, TallerSalida
from app.services.perfiles import taller_service

router = APIRouter(prefix="/talleres", tags=["Talleres"])


@router.post("/registrar", response_model=TallerSalida, status_code=status.HTTP_201_CREATED)
def registrar(data: TallerRegistrar, db: Session = Depends(get_db)):
    return taller_service.registrar(db, data)


@router.get("/", response_model=PaginacionSalida[TallerSalida], dependencies=[Depends(get_current_user)])
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return taller_service.obtener_todos(db, pagina, limite)


@router.get("/tenant/{tenant_id}", response_model=PaginacionSalida[TallerSalida], dependencies=[Depends(get_current_user)])
def listar_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return taller_service.obtener_por_tenant(db, tenant_id, pagina, limite)


@router.get("/{taller_id}", response_model=TallerSalida, dependencies=[Depends(get_current_user)])
def obtener(taller_id: int, db: Session = Depends(get_db)):
    taller = taller_service.obtener_por_id(db, taller_id)
    if not taller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller


@router.put("/{taller_id}", response_model=TallerSalida, dependencies=[Depends(get_current_user)])
def actualizar(taller_id: int, data: TallerActualizar, db: Session = Depends(get_db)):
    taller = taller_service.actualizar(db, taller_id, data)
    if not taller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller


@router.patch("/{taller_id}/estado", response_model=TallerSalida, dependencies=[Depends(get_current_user)])
def actualizar_estado(taller_id: int, data: TallerEstadoActualizar, db: Session = Depends(get_db)):
    taller = taller_service.actualizar_estado(db, taller_id, data)
    if not taller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller


@router.patch("/{taller_id}/activar", response_model=TallerSalida, dependencies=[Depends(get_current_user)])
def activar(taller_id: int, db: Session = Depends(get_db)):
    taller = taller_service.activar(db, taller_id)
    if not taller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller


@router.patch("/{taller_id}/desactivar", response_model=TallerSalida, dependencies=[Depends(get_current_user)])
def desactivar(taller_id: int, db: Session = Depends(get_db)):
    taller = taller_service.desactivar(db, taller_id)
    if not taller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller


@router.delete("/{taller_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
def eliminar(taller_id: int, db: Session = Depends(get_db)):
    taller = taller_service.eliminar(db, taller_id)
    if not taller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
