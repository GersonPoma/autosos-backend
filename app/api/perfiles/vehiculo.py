from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.perfiles.vehiculo import VehiculoCrear, VehiculoActualizar, VehiculoSalida
from app.services.perfiles import vehiculo_service

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=PaginacionSalida[VehiculoSalida])
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return vehiculo_service.obtener_todos(db, pagina, limite)


@router.get("/cliente/{cliente_id}", response_model=VehiculoSalida)
def obtener_por_cliente(cliente_id: int, db: Session = Depends(get_db)):
    vehiculo = vehiculo_service.obtener_por_cliente(db, cliente_id)
    if not vehiculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    return vehiculo


@router.post("/", response_model=VehiculoSalida, status_code=status.HTTP_201_CREATED)
def crear(data: VehiculoCrear, db: Session = Depends(get_db)):
    return vehiculo_service.crear(db, data)


@router.put("/cliente/{cliente_id}", response_model=VehiculoSalida)
def actualizar(cliente_id: int, data: VehiculoActualizar, db: Session = Depends(get_db)):
    vehiculo = vehiculo_service.actualizar(db, cliente_id, data)
    if not vehiculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    return vehiculo


@router.delete("/cliente/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(cliente_id: int, db: Session = Depends(get_db)):
    vehiculo = vehiculo_service.eliminar(db, cliente_id)
    if not vehiculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
