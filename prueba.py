import logging
import json
from azure.cosmos import CosmosClient, exceptions
import azure.functions as func
import os

a = 2
b = 2
c = a + b

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
@app.function_name(name="func_getCosmosData")
@app.route(route="func_getCosmosData")

def http_trigger1(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Configuración de Cosmos DB desde variables de entorno
    COSMOS_URL = os.environ.get('COSMOS_URL')
    COSMOS_KEY = os.environ.get('COSMOS_KEY')
    COSMOS_DB_NAME = os.environ.get('COSMOS_DB_NAME')
    COSMOS_CONTAINER_NAME = os.environ.get('COSMOS_CONTAINER_NAME')

    # Verifica que las variables de entorno están configuradas
    if not all([COSMOS_URL, COSMOS_KEY, COSMOS_DB_NAME, COSMOS_CONTAINER_NAME]):
        return func.HttpResponse("Falta una o más variables de entorno", status_code=500)

    try:
        # Crear cliente de Cosmos DB
        client = CosmosClient(COSMOS_URL, COSMOS_KEY)
        database = client.get_database_client(COSMOS_DB_NAME)
        container = database.get_container_client(COSMOS_CONTAINER_NAME)

        # Consultar documentos de Cosmos DB
        items = list(container.read_all_items())

        # Convertir a JSON
        items_json = json.dumps(items)
        
        return func.HttpResponse(items_json, mimetype="application/json")
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Error en Cosmos DB: {e}")
        return func.HttpResponse("Error al recuperar datos de Cosmos DB", status_code=500)
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        return func.HttpResponse("Se produjo un error inesperado", status_code=500)
