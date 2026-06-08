from pathlib import Path
import os
import base64
import json

import firebase_admin
from firebase_admin import credentials, messaging

_app = None
_CRED_PATH = Path(__file__).resolve().parent.parent / "core" / "firebase_credentials.json"


def _get_app():
    global _app
    if _app is None:
        firebase_b64 = os.getenv("FIREBASE_CREDENTIALS_B64")
        if firebase_b64:
            # Producción (Render): Cargar credenciales desde Variable de Entorno en Base64
            cred_json = base64.b64decode(firebase_b64).decode('utf-8')
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # Desarrollo Local: Usar el archivo físico
            cred = credentials.Certificate(str(_CRED_PATH))

        _app = firebase_admin.initialize_app(cred)
    return _app


def enviar_notificacion(fcm_token: str, titulo: str, cuerpo: str, data: dict = None) -> bool:
    try:
        _get_app()
        payload = {"titulo": titulo, "cuerpo": cuerpo}
        payload.update({k: str(v) for k, v in (data or {}).items()})
        message = messaging.Message(
            data=payload,
            token=fcm_token,
        )
        messaging.send(message)
        return True
    except Exception as e:
        print(f"Error FCM: {e}")
        return False