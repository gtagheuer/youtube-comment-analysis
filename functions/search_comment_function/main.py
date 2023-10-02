import functions_framework
import base64
import requests
import time
import json
import os
from concurrent import futures
from google.cloud import pubsub_v1

# Set your own parameter
API_KEY = os.environ.get('YOUTUBE_API_KEY', 'Specified environment variable is not set.')
PROJECT_ID = os.environ.get('PROJECT_ID', 'Specified environment variable is not set.')
BQ_DATASET = 'youtube'
PUBSUB_TOPIC_ID = 'comment'
URL = 'https://www.googleapis.com/youtube/v3/'

@functions_framework.cloud_event
def load_data(cloud_event):
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8"))
    search_comments(
        product_id=data["row"][0]["product_id"],
        product_name=data["row"][0]["product_name"],
        product_group=data["row"][0]["product_group"],
        video_id=data["row"][0]["video_id"],
        next_page_token=None,
        region_code=data["row"][0]["region_code"]
    )

def search_comments(product_id, product_name, product_group, video_id, next_page_token, region_code):
    params = {
        'key': API_KEY,
        'part': 'snippet',
        'videoId': video_id,
        'order': 'relevance',
        'textFormat': 'plaintext',
        'maxResults': 100,
    }
    if next_page_token is not None:
        params['pageToken'] = next_page_token
    response = requests.get(URL + 'commentThreads', params=params)
    resource = response.json()
    if 'error' not in resource:
        comments = resource["items"]
        messages = []
        for comment in comments:
            message = {
                "table_id"                  : f"{PROJECT_ID}.{BQ_DATASET}.comment",
                "row"                       : [{
                    "product_id"                    : product_id,
                    "product_name"                  : product_name,
                    "product_group"                 : product_group,
                    "video_id"                      : video_id,
                    "comment_id"                    : comment['snippet']['topLevelComment']['id'],
                    "comment_published_at"          : comment['snippet']['topLevelComment']['snippet']['publishedAt'],
                    "comment_author_name"           : comment['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    "comment_author_image_url"      : comment['snippet']['topLevelComment']['snippet']['authorProfileImageUrl'],
                    "comment_like_count"            : comment['snippet']['topLevelComment']['snippet']['likeCount'],
                    "comment_text"                  : comment['snippet']['topLevelComment']['snippet']['textDisplay'].replace('\r', '\n').replace('\n', ' '),
                    "comment_sentiment"             : "",
                    "comment_sentiment_score"       : 0,
                    "comment_sentiment_magnitude"   : 0,
                    "region_code"                   : region_code,
                }]
            }
            messages.append(message)
        publish_message_to_pubsub(messages)
    
    if 'nextPageToken' in resource:
        search_comments(
            product_id=product_id,
            product_name=product_name,
            product_group=product_group,
            video_id=video_id,
            next_page_token=resource["nextPageToken"],
            region_code=region_code
        )

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
            time.sleep(1)
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