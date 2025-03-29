import asyncio
import threading
import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from telegram import Bot

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables de entorno y configuración (usando dotenv o similares)
MONGO_URI = "tu_mongo_uri"
DATABASE_NAME = "Transporte"
COLLECTION_NAME = "Autobuses"
TELEGRAM_TOKEN = "tu_telegram_token"

# Conexión a la base de datos
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Inicializa el bot de Telegram
bot = Bot(token=TELEGRAM_TOKEN)


async def enviar_alerta(chat_id: int, mensaje: str):
    try:
        await bot.send_message(chat_id=chat_id, text=mensaje)
        logger.info("Mensaje enviado a %s", chat_id)
    except Exception as e:
        logger.error("Error al enviar mensaje a %s: %s", chat_id, e)


def procesar_evento(change):
    """
    Función para procesar el evento de cambio.
    Aquí puedes agregar la lógica para generar el mensaje o actualizar tu aplicación.
    """
    logger.info("Cambio detectado: %s", change)
    # Por ejemplo, si detectamos un cambio que requiere enviar alerta:
    chat_id = change.get("fullDocument", {}).get("IdAutobus")
    if chat_id:
        # Genera o usa tu lógica para el mensaje
        mensaje = "Alerta: Se ha detectado un cambio en tu ruta."
        # Ejecutamos la función asíncrona en el loop principal:
        asyncio.run(enviar_alerta(chat_id, mensaje))


def monitorear_cambios():
    """
    Esta función se encarga de abrir el Change Stream y estar pendiente de cambios en la colección.
    Se ejecuta en un hilo separado.
    """
    try:
        with collection.watch() as change_stream:
            for change in change_stream:
                procesar_evento(change)
    except PyMongoError as e:
        logger.error("Error en el Change Stream: %s", e)


def iniciar_monitoreo():
    # Ejecutar el monitoreo en un hilo separado para no bloquear el loop principal
    hilo = threading.Thread(target=monitorear_cambios, daemon=True)
    hilo.start()
    logger.info(
        "Monitoreo de cambios iniciado en la colección '%s'", COLLECTION_NAME)


if __name__ == "__main__":
    iniciar_monitoreo()

    # Mantener el proceso corriendo. Por ejemplo, con un loop infinito.
    try:
        while True:
            # Aquí puedes incluir otras tareas o simplemente dormir
            asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Deteniendo el monitoreo.")
