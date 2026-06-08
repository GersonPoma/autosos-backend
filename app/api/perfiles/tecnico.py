from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.perfiles.tecnico import TecnicoCrear, TecnicoActualizar, TecnicoSalida
from app.services.perfiles import tecnico_service

router = APIRouter(prefix="/tecnicos", tags=["Técnicos"], dependencies=[Depends(get_current_user)])


@router.get("/taller/{taller_id}", response_model=PaginacionSalida[TecnicoSalida])
def listar_por_taller(taller_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return tecnico_service.obtener_por_taller(db, taller_id, pagina, limite)


@router.get("/tenant/{tenant_id}", response_model=PaginacionSalida[TecnicoSalida])
def listar_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return tecnico_service.obtener_por_tenant(db, tenant_id, pagina, limite)


@router.get("/{tecnico_id}", response_model=TecnicoSalida)
def obtener(tecnico_id: int, db: Session = Depends(get_db)):
    tecnico = tecnico_service.obtener_por_id(db, tecnico_id)
    if not tecnico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnico no encontrado")
    return tecnico


@router.post("/", response_model=TecnicoSalida, status_code=status.HTTP_201_CREATED)
def crear(data: TecnicoCrear, db: Session = Depends(get_db)):
    return tecnico_service.crear(db, data)


@router.put("/{tecnico_id}", response_model=TecnicoSalida)
def actualizar(tecnico_id: int, data: TecnicoActualizar, db: Session = Depends(get_db)):
    tecnico = tecnico_service.actualizar(db, tecnico_id, data)
    if not tecnico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnico no encontrado")
    return tecnico


@router.delete("/{tecnico_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(tecnico_id: int, db: Session = Depends(get_db)):
    tecnico = tecnico_service.eliminar(db, tecnico_id)
    if not tecnico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnico no encontrado")
