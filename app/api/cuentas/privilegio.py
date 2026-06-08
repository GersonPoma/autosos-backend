from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.cuentas.privilegio import PrivilegioActualizar, PrivilegioSalida
from app.services.cuentas import privilegio_service

router = APIRouter(prefix="/privilegios", tags=["Privilegios"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=PaginacionSalida[PrivilegioSalida])
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return privilegio_service.obtener_todos(db, pagina, limite)


@router.get("/{privilegio_id}", response_model=PrivilegioSalida)
def obtener(privilegio_id: int, db: Session = Depends(get_db)):
    privilegio = privilegio_service.obtener_por_id(db, privilegio_id)
    if not privilegio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Privilegio no encontrado")
    return privilegio


@router.put("/{privilegio_id}", response_model=PrivilegioSalida)
def actualizar(privilegio_id: int, data: PrivilegioActualizar, db: Session = Depends(get_db)):
    privilegio = privilegio_service.actualizar(db, privilegio_id, data)
    if not privilegio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Privilegio no encontrado")
    return privilegio


@router.post("/roles/{rol_id}/privilegios/{privilegio_id}", status_code=status.HTTP_201_CREATED)
def asignar_a_rol(rol_id: int, privilegio_id: int, db: Session = Depends(get_db)):
    asignado = privilegio_service.asignar_a_rol(db, rol_id, privilegio_id)
    if not asignado:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El privilegio ya está asignado a este rol")
    return {"detail": "Privilegio asignado correctamente"}


@router.delete("/roles/{rol_id}/privilegios/{privilegio_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_de_rol(rol_id: int, privilegio_id: int, db: Session = Depends(get_db)):
    removido = privilegio_service.remover_de_rol(db, rol_id, privilegio_id)
    if not removido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")


@router.get("/roles/{rol_id}/privilegios", response_model=list[PrivilegioSalida])
def listar_por_rol(rol_id: int, db: Session = Depends(get_db)):
    return privilegio_service.obtener_por_rol(db, rol_id)