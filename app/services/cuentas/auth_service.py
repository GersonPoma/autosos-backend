from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.cuentas.usuario import Usuario


def authenticate_user(db: Session, username: str, password: str) -> Usuario | None:
    usuario = db.query(Usuario).filter(
        Usuario.username == username,
        Usuario.deleted == False
    ).first()

    if not usuario:
        return None
    if not verify_password(password, usuario.password):
        return None
    return usuario