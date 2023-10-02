import functions_framework
import base64
import requests
import time
import json
import os
from concurrent import futures
from google.api_core import retry
from google.cloud import pubsub_v1
from google.cloud import language_v1

# Set your own parameter
PROJECT_ID = os.environ.get('PROJECT_ID', 'Specified environment variable is not set.')
PUBSUB_TOPIC_ID = 'sentiment'
SUBSCRIPTION_ID = 'comment-sub'
NUM_MESSAGES = 300
URL = 'https://www.googleapis.com/youtube/v3/'

@functions_framework.cloud_event
def load_data(cloud_event):
    language = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8"))["language"]
    
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    # Wrap the subscriber in a 'with' block to automatically call close() to
    # close the underlying gRPC channel when done.
    with subscriber:
        # The subscriber pulls a specific number of messages. The actual
        # number of messages pulled may be smaller than max_messages.
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": NUM_MESSAGES},
            retry=retry.Retry(timeout=30),
        )

        if len(response.received_messages) == 0:
            return(True)

        ack_ids = []
        messages = []
        for received_message in response.received_messages:
            ack_ids.append(received_message.ack_id)
            data = json.loads(received_message.message.data)

            client = language_v1.LanguageServiceClient()
            document = language_v1.Document(
                content=data["row"][0]["comment_text"],
                type_=language_v1.Document.Type.PLAIN_TEXT,
                language=language
            )
            sentiment = client.analyze_sentiment(
                request={"document": document}
            ).document_sentiment

            messages.append({
                "table_id": data["table_id"],
                "row": [{
                    "product_id"                    : data["row"][0]["product_id"],
                    "product_name"                  : data["row"][0]["product_name"],
                    "product_group"                 : data["row"][0]["product_group"],
                    "video_id"                      : data["row"][0]["video_id"],
                    "comment_id"                    : data["row"][0]["comment_id"],
                    "comment_published_at"          : data["row"][0]["comment_published_at"],
                    "comment_author_name"           : data["row"][0]["comment_author_name"],
                    "comment_author_image_url"      : data["row"][0]["comment_author_image_url"],
                    "comment_like_count"            : data["row"][0]["comment_like_count"],
                    "comment_text"                  : data["row"][0]["comment_text"],
                    "comment_sentiment"             : sentiment_classification(sentiment),
                    "comment_sentiment_score"       : sentiment.score,
                    "comment_sentiment_magnitude"   : sentiment.magnitude,
                    "region_code"                   : data["row"][0]["region_code"],
                }]
            })

        publish_message_to_pubsub(messages)        

        # Acknowledges the received messages so they will not be sent again.
        subscriber.acknowledge(
            request={"subscription": subscription_path, "ack_ids": ack_ids}
        )

        print(
            f"Received and acknowledged {len(response.received_messages)} messages from {subscription_path}."
        )
        return(True)

def sentiment_classification(sentiment):
    # sentiment magnitude won't be considered for now
    if 0.25 <= sentiment.score <= 1:
        return "Positive"
    elif -0.25 < sentiment.score < 0.25:
        return "Neutral"
    elif -1 <= sentiment.score <= 0.25:
        return "Negative"
    else:
        return "Unknown"

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
