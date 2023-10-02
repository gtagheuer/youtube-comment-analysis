import functions_framework
import base64
import requests
import time
import json
import os
from google.cloud import bigquery

# Set your own parameter
PROJECT_ID = os.environ.get('PROJECT_ID', 'Specified environment variable is not set.')
BQ_DATASET = 'youtube'

@functions_framework.cloud_event
def load_data(cloud_event):
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8"))
    insert_rows_to_bq(data["table_id"], data["row"])

def insert_rows_to_bq(table_id, rows):
    client = bigquery.Client()
    errors = client.insert_rows_json(table_id, rows)
    if errors == []:
        print(f"Insert the data to BigQuery Table '{table_id}' - data -> {rows[0]}")
        return(True)
    else:
        print("Encountered errors while inserting rows: {}".format(errors))