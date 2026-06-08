import os

import mimetypes

import google.generativeai as genai
import requests
import json

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("¡Error! No se encontró GEMINI_API_KEY en el archivo .env")

genai.configure(api_key=API_KEY)


def _descargar_evidencia(url: str, tipo_esperado: str) -> tuple[str, bytes]:
    try:
        respuesta = requests.get(url, timeout=20)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise ValueError(f"No se pudo descargar la evidencia desde la URL: {exc}")

    mime_header = respuesta.headers.get("Content-Type", "").split(";")[0].strip().lower()
    mime_guess, _ = mimetypes.guess_type(url)
    mime_tipo = mime_header or mime_guess

    if not mime_tipo:
        mime_tipo = "audio/mp4" if tipo_esperado == "audio" else "image/jpeg"

    if not mime_tipo.startswith(f"{tipo_esperado}/"):
        raise ValueError(
            f"La URL no devuelve un {tipo_esperado} valido. MIME recibido: {mime_tipo}"
        )

    return mime_tipo, respuesta.content

def generar_ficha_servicio(url_audio: str, urls_fotos: list[str]) -> dict:
    """
    Servicio principal que orquesta la creación de la ficha estructurada.
    Lanza un ValueError si las evidencias no son válidas.
    """

    # 1. Validar y procesar el Audio
    resultado_audio = analizar_audio_incidente(url_audio)
    if not resultado_audio.get("es_valido"):
        print(f"Audio no válido: {resultado_audio.get('motivo_rechazo')}")
        # Lanzamos un error nativo de Python con el motivo de rechazo de la IA
        raise ValueError(f"AUDIO_INVALIDO|{resultado_audio.get('motivo_rechazo')}")

    # 2. Validar y procesar las Imágenes
    resultado_fotos = analizar_imagenes_incidente(urls_fotos)
    if not resultado_fotos.get("es_valido"):
        raise ValueError(f"IMAGEN_INVALIDA|{resultado_fotos.get('motivo_rechazo')}")

    # 3. Consolidar la Ficha Estructurada (Si todo salió bien)
    ficha_db = {
        "transcripcion_audio": resultado_audio["transcripcion"],
        "categoria_problema": resultado_fotos["categoria"],
        "danios_identificados": resultado_fotos["danos_visibles"],
        "resumen_estructurado": resultado_audio["informacion_relevante"]
    }

    prioridad_incidente = resultado_fotos["prioridad"]

    # ficha_consolidada = {
    #     "transcripcion_audio": resultado_audio["transcripcion"],
    #     "resumen_audio": resultado_audio["informacion_relevante"],
    #     "categoria_problema": resultado_fotos["categoria"],
    #     "danos_identificados": resultado_fotos["danos_visibles"],
    #     "prioridad_sugerida": resultado_fotos["prioridad"]
    # }

    # Nota: Aquí más adelante llamarías a otra función para guardar esto en PostgreSQL
    # ej: guardar_ficha_en_bd(ficha_consolidada)

    # return ficha_consolidada

    return {
        "ficha_para_insertar": ficha_db,
        "prioridad_para_actualizar": prioridad_incidente
    }

def analizar_audio_incidente(url_audio: str):
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt_audio = """
    Eres un asistente mecánico. Escucha el siguiente audio.
    Tu objetivo es determinar si el audio contiene una descripción clara de un problema vehicular.
    Devuelve estrictamente un JSON con esta estructura:
    {
        "es_valido": true/false,
        "transcripcion": "texto exacto de lo que se escucha",
        "informacion_relevante": "resumen ejecutivo del problema para el mecánico (vacío si no es válido)",
        "motivo_rechazo": "Si es_valido es false, explica por qué (ej. 'Solo se escucha ruido del viento', 'No menciona ningún problema del auto'). Si es true, déjalo vacío."
    }
    """
    # --- EL TRUCO MAESTRO DE CLOUDINARY ---
    # Convertimos cualquier formato (m4a, aac, wav, etc.) a un MP3 puro al vuelo

    # 1. Separamos la URL por el último punto para quitar la extensión vieja
    if "." in url_audio.split("/")[-1]:
        url_base = url_audio.rsplit(".", 1)[0]
        url_audio_mp3 = f"{url_base}.mp3"  # Le pegamos la extensión mp3
    else:
        url_audio_mp3 = f"{url_audio}.mp3"  # Por si viene sin extensión

    print(f"Descargando audio convertido de: {url_audio_mp3}")

    # --- BLINDAJE DE DESCARGA ---
    try:
        # Le damos a Cloudinary hasta 10 segundos para convertir el audio
        respuesta_audio = requests.get(url_audio_mp3, timeout=10)

        # Verificamos que Cloudinary nos haya devuelto el archivo y no un error interno
        if respuesta_audio.status_code != 200:
            return {"es_valido": False,
                    "motivo_rechazo": "Los servidores de medios están tardando en procesar el audio. Por favor, intenta enviarlo de nuevo."}

    except requests.exceptions.Timeout:
        return {"es_valido": False,
                "motivo_rechazo": "El audio tardó demasiado en procesarse. Por favor, intenta de nuevo."}
    except Exception as e:
        return {"es_valido": False, "motivo_rechazo": f"Error al intentar descargar el audio: {str(e)}"}
    # ----------------------------

    # Si todo salió bien, le mandamos el archivo a Gemini
    contenido = [prompt_audio, {"mime_type": "audio/mp3", "data": respuesta_audio.content}]

    try:
        respuesta_ia = model.generate_content(
            contenido,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(respuesta_ia.text)
    except Exception as e:
        print(f"Error real audio IA: {e}")
        return {"es_valido": False, "motivo_rechazo": "Error interno al procesar el audio."}


def analizar_imagenes_incidente(urls_fotos: list[str]):
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt_imagen = """
    Eres un perito de seguros vehiculares. Analiza las siguientes fotografías.
    ¿Puedes ver claramente un vehículo y algún daño o situación de emergencia?
    Devuelve estrictamente un JSON con esta estructura:
    {
        "es_valido": true/false,
        "categoria": "Motor, Choque, Llanta, Batería, u Otros (vacío si no es válido)",
        "danos_visibles": "Descripción de lo que ves roto o dañado",
        "prioridad": "Evalúa la prioridad ESTRICTAMENTE bajo estas reglas: 
                      - Alta: Choques graves, humo, fuego, o autos destrozados.
                      - Media: Llantas pinchadas, choques leves (raspones/abolladuras).
                      - Baja: Luces de tablero, problemas de batería, o daños estéticos menores.",
        "motivo_rechazo": "Si es_valido es false, explica por qué. Si es true, déjalo vacío."
    }
    """

    contenido = [prompt_imagen]
    for url in urls_fotos:
        try:
            tipo_mime, data_foto = _descargar_evidencia(url, "image")
        except ValueError as exc:
            return {"es_valido": False, "motivo_rechazo": str(exc)}
        contenido.append({"mime_type": tipo_mime, "data": data_foto})

    try:
        respuesta_ia = model.generate_content(
            contenido,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(respuesta_ia.text)
    except Exception as e:
        return {"es_valido": False, "motivo_rechazo": "Error interno al procesar las imágenes."}