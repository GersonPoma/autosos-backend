from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.paginacion import PaginacionSalida
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.pagos.detalle_orden import GenerarPagoEntrada
from app.schemas.pagos.transaccion import ActualizarEstadoEntrada, GenerarPagoSalida, StripeIntentSalida, TransaccionEntrada, TransaccionSalida
from app.models.talleres.orden_servicio import OrdenServicio as OrdenModel, EstadoOperacion
from app.services.pagos import service_transaccion
from app.services.talleres import service_orden_servicio
from app.tracking.manager import manager

router = APIRouter(
    prefix="/transacciones",
    tags=["Transacciones"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/generar-pago", response_model=GenerarPagoSalida, status_code=status.HTTP_201_CREATED)
async def generar_pago(entrada: GenerarPagoEntrada, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    resultado = service_transaccion.generar_pago(db, entrada.orden_servicio_id, entrada.servicios, current_user.tenant_id)
    orden = db.query(OrdenModel).filter(OrdenModel.id == entrada.orden_servicio_id).first()
    if orden:
        incidente_id = orden.cotizacion.asignacion_candidato.incidente_id
        service_orden_servicio.cambiar_estado(db, entrada.orden_servicio_id, EstadoOperacion.FINALIZADO)
        await manager.broadcast(incidente_id, {
            "evento": "estado_orden_cambiado",
            "data": {"orden_id": entrada.orden_servicio_id, "estado": "FINALIZADO"},
        })
        await manager.broadcast(incidente_id, {
            "evento": "transaccion_creada",
            "data": {"orden_servicio_id": entrada.orden_servicio_id},
        })
    return resultado


@router.post("/", response_model=TransaccionSalida, status_code=status.HTTP_201_CREATED)
def crear(entrada: TransaccionEntrada, db: Session = Depends(get_db)):
    return service_transaccion.crear(db, entrada)


@router.get("/taller/{taller_id}", response_model=PaginacionSalida[TransaccionSalida])
def obtener_por_taller(taller_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_transaccion.obtener_por_taller(db, taller_id, pagina, limite)


@router.get("/tenant/{tenant_id}", response_model=PaginacionSalida[TransaccionSalida])
def obtener_por_tenant(tenant_id: int, pagina: int = 1, limite: int = 10, db: Session = Depends(get_db)):
    return service_transaccion.obtener_por_tenant(db, tenant_id, pagina, limite)


@router.get("/orden/{orden_id}", response_model=TransaccionSalida)
def obtener_por_orden(orden_id: int, db: Session = Depends(get_db)):
    t = service_transaccion.obtener_por_orden(db, orden_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    return t


@router.get("/{transaccion_id}", response_model=TransaccionSalida)
def obtener(transaccion_id: int, db: Session = Depends(get_db)):
    t = service_transaccion.obtener_por_id(db, transaccion_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    return t


@router.patch("/{transaccion_id}/estado", response_model=TransaccionSalida)
def actualizar_estado(transaccion_id: int, entrada: ActualizarEstadoEntrada, db: Session = Depends(get_db)):
    t = service_transaccion.actualizar_estado(db, transaccion_id, entrada.estado)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    return t


@router.post("/{transaccion_id}/stripe-intent", response_model=StripeIntentSalida)
def crear_intent_stripe(transaccion_id: int, db: Session = Depends(get_db)):
    """
    Inicia una sesión de pago en Stripe (PaymentIntent) para la transacción.
    Retorna el `client_secret` que el frontend (Flutter) requiere para completar el pago.
    """
    try:
        resultado = service_transaccion.crear_payment_intent(db, transaccion_id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
