import json
import os

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cuentas.usuario import Usuario
from app.models.perfiles.tecnico import Tecnico
from app.models.talleres.asignacion_candidato import AsignacionCandidato, EstadoNotificacion
from app.tracking.manager import manager

router = APIRouter(tags=["Tracking"])


def _usuario_desde_token(token: str, db: Session) -> Usuario | None:
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM", "HS256")])
        user_id = int(payload.get("sub"))
        return db.query(Usuario).filter(Usuario.id == user_id, Usuario.deleted == False).first()
    except (JWTError, TypeError, ValueError):
        return None


def _es_taller_del_incidente(db: Session, usuario_id: int, incidente_id: int) -> bool:
    """
    Verifica que el usuario sea el dueño del taller asignado al incidente
    o un técnico de ese taller. No depende del rol, solo de la relación en BD.
    """
    asignacion = (
        db.query(AsignacionCandidato)
        .filter(
            AsignacionCandidato.incidente_id == incidente_id,
            AsignacionCandidato.estado == EstadoNotificacion.ACEPTADO,
            AsignacionCandidato.deleted == False,
        )
        .first()
    )
    if not asignacion or not asignacion.taller:
        return False

    taller = asignacion.taller
    if taller.usuario_id == usuario_id:
        return True

    return (
        db.query(Tecnico)
        .filter(
            Tecnico.taller_id == taller.id,
            Tecnico.usuario_id == usuario_id,
            Tecnico.deleted == False,
        )
        .first()
        is not None
    )


@router.websocket("/ws/incidente/{incidente_id}")
async def websocket_incidente(
    incidente_id: int,
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    usuario = _usuario_desde_token(token, db)
    if not usuario:
        await websocket.close(code=4001)
        return

    await manager.connect(incidente_id, websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except (json.JSONDecodeError, ValueError):
                continue

            if data.get("tipo") == "ubicacion":
                if not _es_taller_del_incidente(db, usuario.id, incidente_id):
                    continue
                lat = data.get("lat")
                lon = data.get("lon")
                if lat is None or lon is None:
                    continue
                await manager.broadcast(incidente_id, {
                    "evento": "ubicacion_taller",
                    "data": {"lat": lat, "lon": lon},
                })

    except WebSocketDisconnect:
        manager.disconnect(incidente_id, websocket)