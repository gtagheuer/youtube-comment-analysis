import functions_framework
import base64
import requests
import time
import datetime
import json
import os
from concurrent import futures
from google.cloud import bigquery
from google.cloud import pubsub_v1

# Set your own parameter
PROJECT_ID = os.environ.get('PROJECT_ID', 'Specified environment variable is not set.')
BQ_DATASET = 'youtube'
BQ_PRODUCT_TABLE = 'product'
BQ_VIDEO_TABLE = 'video'
PUBSUB_TOPIC_ID = 'product'
URL = 'https://www.googleapis.com/youtube/v3/'

@functions_framework.cloud_event
def load_data(cloud_event):
    print("YouTube comment analysis pipeline is triggered!!")
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8"))
    region_code = data["region_code"]
    client = bigquery.Client()
    query = f"""
        SELECT product_group
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_PRODUCT_TABLE}`
        WHERE region_code = '{region_code}'
        GROUP BY product_group
    """
    query_job = client.query(query)
    pick_product_group(query_job, region_code)

def pick_product_group(rows, region_code):
    date_ = datetime.datetime.now().date().replace(day=1)
    client = bigquery.Client()
    for row in rows:
        product_group = row[0]
        query = f"""
            SELECT *
            FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_VIDEO_TABLE}`
            WHERE product_group = '{product_group}'
            AND region_code = '{region_code}'
            AND TIMESTAMP_TRUNC(_PARTITIONTIME, MONTH) = TIMESTAMP("{date_}")
        """
        query_job = client.query(query)
        not_analyzed = (query_job.result().total_rows == 0)
        if not_analyzed:
            get_product(product_group, region_code)
            break
        else:
            print(f"Product group: {product_group} is already analyzed for this month.")
    return(True)

def get_product(product_group, region_code):
    client = bigquery.Client()
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_PRODUCT_TABLE}`
        WHERE product_group = '{product_group}'
        AND region_code = '{region_code}'
    """
    query_job = client.query(query)
    for row in query_job:
        message = [{
           "product_id": row[0],
           "product_name": row[1],
           "product_group": row[2],
           "region_code": row[3]
        }]
        # Decrease the time for sleep if you have more than 100 products
        # The function triggered by Eventarc timeouts after 540 seconds
        time.sleep(5)
        print(f"YouTube comment analysis pipeline for {message[0]['product_name']} [{message[0]['product_group']}]started!!")
        publish_message_to_pubsub(message)
    return(True)

class pubsub_publisher():
    def __init__(self):
        self.project_id = PROJECT_ID
        self.topic_id = PUBSUB_TOPIC_ID
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
        self.futures = dict()
        return
       
    def send(self,messages):
        for message_id,message in enumerate(json.loads(messages)):
            data = json.dumps(message)
            self.futures.update({message_id:None})
            future = self.publisher.publish(
                self.topic_path, data=data.encode("utf-8")
            )
            self.futures[message_id] = future
            future.add_done_callback(self.get_callback(future,message_id))
        while self.futures:
            time.sleep(2)
        return(True)

    def get_callback(self,f,id):
        def callback(f):
            try:
                self.futures.pop(id)
            except:
                print(f"Please handle {f.exception()} for {id}.")
        return callback

def publish_message_to_pubsub(message):
    pub = pubsub_publisher()
    data = json.dumps(message)
    pub.send(data)