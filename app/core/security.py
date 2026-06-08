import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.session import get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer()


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no puede superar los 72 caracteres",
        )
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer), db: Session = Depends(get_db)):
    token = credentials.credentials
    from app.models.cuentas.usuario import Usuario

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == user_id, Usuario.deleted == False).first()
    if usuario is None:
        raise credentials_exception
    return usuario


def requiere_privilegio(nombre: str):
    def verificar(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
        from app.models.cuentas.privilegio import Privilegio
        from app.models.cuentas.rol_privilegio import rol_privilegio

        tiene = db.query(Privilegio).join(
            rol_privilegio, Privilegio.id == rol_privilegio.c.privilegio_id
        ).filter(
            rol_privilegio.c.rol_id == current_user.rol_id,
            Privilegio.nombre == nombre,
            Privilegio.deleted == False,
        ).first()

        if not tiene:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes el privilegio requerido: {nombre}",
            )
        return current_user
    return verificar