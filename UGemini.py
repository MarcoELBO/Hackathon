import os
import asyncio
import logging
from dotenv import load_dotenv
from google import genai
from telegram import Bot
from telegram.error import BadRequest
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener las variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME", "Transporte")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "Autobuses")

# Configurar parámetros de alerta
TIEMPO = "7 minutos"
VELOCIDAD = "6 km/h"


def get_database_collection(uri: str, db_name: str, coleccion_name: str):
    try:
        client = MongoClient(uri)
        client.admin.command('ping')
        db = client[db_name]
        coleccion = db[coleccion_name]
        return coleccion
    except ConnectionFailure as e:
        logger.error("No se pudo conectar a la base de datos: %s", e)
        raise


def obtener_chat_ids(coleccion):
    chat_ids = []
    try:
        for auto in coleccion.find({"Corregir": 1}):
            chat_id = auto.get('IdAutobus')
            if chat_id:
                chat_ids.append(chat_id)
        logger.info("Chat IDs obtenidos: %s", chat_ids)
    except Exception as e:
        logger.error("Error al obtener chat IDs: %s", e)
    return chat_ids


def generar_mensaje(client_api, tiempo: str, velocidad: str) -> str:
    prompt = (
        f"Considerate un supervisor de rutas de autobuses. Debes dar mensajes claros y cortos, "
        f"enviando alertas solo si el conductor se ha desfasado de su horario y transcurso de ruta. "
        f"Toma en cuenta el tiempo = {tiempo} y la velocidad = {velocidad}. "
        f"El conductor debe mantener esta velocidad durante el tiempo dado. "
        f"Envíame solo un mensaje de alerta indicando la velocidad a la que debe ir."
    )
    try:
        response = client_api.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
        )
        mensaje = response.text.strip() if hasattr(response, "text") else ""
        if not mensaje:
            logger.warning("El mensaje generado está vacío.")
        return mensaje
    except Exception as e:
        logger.error("Error al generar el mensaje: %s", e)
        return ""


async def enviar_mensajes(bot: Bot, chat_ids: list, mensaje: str):
    if not mensaje:
        logger.error("No se envió mensaje: el mensaje está vacío.")
        return
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=mensaje)
            logger.info("Mensaje enviado correctamente a %s", chat_id)
            # Actualizar el campo "Corregir" en la colección para el chat_id correspondiente
            try:
                coleccion = get_database_collection(
                    MONGO_URI, DATABASE_NAME, COLLECTION_NAME)
                coleccion.update_one(
                    {"IdAutobus": chat_id},
                    {"$set": {"Corregir": 0}}
                )
                logger.info(
                    "Campo 'Corregir' actualizado a 1 para el chat_id: %s", chat_id)
            except Exception as e:
                logger.error(
                    "Error al actualizar el campo 'Corregir' para el chat_id %s: %s", chat_id, e)
        except BadRequest as e:
            logger.error("Error al enviar mensaje a %s: %s", chat_id, e)
        except Exception as e:
            logger.error(
                "Error inesperado al enviar mensaje a %s: %s", chat_id, e)


async def main():
    coleccion = get_database_collection(
        MONGO_URI, DATABASE_NAME, COLLECTION_NAME)
    chat_ids = obtener_chat_ids(coleccion)

    if not chat_ids:
        logger.info("No se encontraron chat IDs para enviar mensajes.")
        return

    client_api = genai.Client(api_key=GOOGLE_API_KEY)
    mensaje = generar_mensaje(client_api, TIEMPO, VELOCIDAD)

    bot = Bot(token=TELEGRAM_TOKEN)
    await enviar_mensajes(bot, chat_ids, mensaje)

if __name__ == "__main__":
    while True:
        asyncio.run(main())
        asyncio.sleep(20)
