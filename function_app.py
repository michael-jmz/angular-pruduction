import logging
import json
from azure.cosmos import CosmosClient, exceptions
import azure.functions as func
import os
from datetime import datetime, timedelta
import pytz

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

COSMOS_URL = os.environ.get('COSMOS_URL')
COSMOS_KEY = os.environ.get('COSMOS_KEY')
COSMOS_DB_NAME = os.environ.get('COSMOS_DB_NAME')
COSMOS_CONTAINER_NAME = os.environ.get('COSMOS_CONTAINER_NAME')

client = CosmosClient(COSMOS_URL, COSMOS_KEY)
database = client.get_database_client(COSMOS_DB_NAME)
container = database.get_container_client(COSMOS_CONTAINER_NAME)

@app.function_name(name="func_getCosmosData")
@app.route(route="func_getCosmosData")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    ecuador_tz = pytz.timezone('America/Guayaquil')#Definir la zona horaria de Ecuador
    current_time_utc = datetime.now(pytz.utc)#Obtiene la hora actual en UTC (Tiempo Universal Coordinado).
    current_time_ecuador = current_time_utc.astimezone(ecuador_tz)#convierte la hora UTC a la hora local de Ecuador
    logging.info(f'Current time in Ecuador: {current_time_ecuador}')

    if not all([COSMOS_URL, COSMOS_KEY, COSMOS_DB_NAME, COSMOS_CONTAINER_NAME]):
        return func.HttpResponse("Falta una o más variables de entorno", status_code=500)

    try:
        start_date = req.params.get('startDate')
        end_date = req.params.get('endDate')
        real_time = req.params.get('realTime')

        if real_time:
            current_time_ecuador = datetime.now(ecuador_tz)
            previous_time = current_time_ecuador - timedelta(seconds=10)
            query = "SELECT * FROM c WHERE c.timestamp > @previousTime"
            parameters = [{"name": "@previousTime", "value": previous_time.isoformat()}]
            items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
            items_json = json.dumps(items)

            if not items:
                return func.HttpResponse(json.dumps({"message": "No se encontraron datos recientes"}), mimetype="application/json", status_code=200)

            return func.HttpResponse(items_json, mimetype="application/json")

        elif start_date and end_date:
            query = "SELECT * FROM c WHERE c.timestamp BETWEEN @startDate AND @endDate"
            parameters = [
                {"name": "@startDate", "value": start_date},
                {"name": "@endDate", "value": end_date}
            ]

            items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
            items_json = json.dumps(items)

            return func.HttpResponse(items_json, mimetype="application/json")

        else:
            return func.HttpResponse("Parámetros inválidos", status_code=400)

    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Error en Cosmos DB: {e}")
        return func.HttpResponse("Error al recuperar datos de Cosmos DB", status_code=500)
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        return func.HttpResponse("Se produjo un error inesperado", status_code=500)
