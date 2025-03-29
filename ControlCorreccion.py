import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

Autobus = 5637330198


def actualizar_corregir():
    try:
        client = MongoClient(MONGO_URI)
        db = client["Transporte"]
        collection = db["Autobuses"]
        result = collection.update_one({"IdAutobus": Autobus}, {
            "$set": {"Corregir": 1}})
        if result.modified_count > 0:
            print("El campo 'Corregir' se actualizó correctamente.")
        else:
            print("No se encontró un documento con el IdAutobus especificado.")
    except ConnectionFailure:
        print("Error al conectar con la base de datos.")
    finally:
        client.close()


actualizar_corregir()
