import sys
import os

import app.models.cuentas.rol
from app.models.cuentas import privilegio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.services.cuentas.usuario_service import crear_super_usuario


def main():
    print("=== Crear Superusuario ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    db = SessionLocal()
    try:
        usuario = crear_super_usuario(db, username, password)
        print(f"Superusuario creado exitosamente: id={usuario.id}, username={usuario.username}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()