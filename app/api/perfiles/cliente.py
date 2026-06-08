from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.perfiles.cliente import ClienteRegistrar, ClienteActualizar, ClienteSalida
from app.services.perfiles import cliente_service

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/registrar", response_model=ClienteSalida, status_code=status.HTTP_201_CREATED)
def registrar(data: ClienteRegistrar, db: Session = Depends(get_db)):
    return cliente_service.registrar(db, data)


@router.get("/", response_model=PaginacionSalida[ClienteSalida], dependencies=[Depends(get_current_user)])
def listar(pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return cliente_service.obtener_todos(db, pagina, limite)


@router.get("/{cliente_id}", response_model=ClienteSalida, dependencies=[Depends(get_current_user)])
def obtener(cliente_id: int, db: Session = Depends(get_db)):
    cliente = cliente_service.obtener_por_id(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteSalida, dependencies=[Depends(get_current_user)])
def actualizar(cliente_id: int, data: ClienteActualizar, db: Session = Depends(get_db)):
    cliente = cliente_service.actualizar(db, cliente_id, data)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
def eliminar(cliente_id: int, db: Session = Depends(get_db)):
    cliente = cliente_service.eliminar(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
