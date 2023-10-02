import functions_framework
import base64
import requests
import time
import json
import os
from concurrent import futures
from google.cloud import bigquery
from google.cloud import pubsub_v1

# Set your own parameter
API_KEY = os.environ.get('YOUTUBE_API_KEY', 'Specified environment variable is not set.')
PROJECT_ID = os.environ.get('PROJECT_ID', 'Specified environment variable is not set.')
BQ_DATASET = 'youtube'
PUBSUB_TOPIC_ID = 'video'
URL = 'https://www.googleapis.com/youtube/v3/'

@functions_framework.cloud_event
def load_data(cloud_event):
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8"))
    query = f"{data['product_group']} {data['product_name']}"
    params = {
        'key': API_KEY,
        'part': 'id',
        'q': query,
        'order': 'relevance',
        'regionCode': data["region_code"],
        'maxResults': 50,
    }
    response = requests.get(URL + 'search', params=params)
    resource = response.json()
    videos = resource['items']
    id_arr = []
    for video in videos:
        if video["id"]["kind"] == "youtube#video":
            id_arr.append(video["id"]["videoId"])
    video_ids = ','.join(id_arr)
    search_video_info(
        product_id=data["product_id"],
        product_name=data["product_name"],
        product_group=data["product_group"],
        video_ids=video_ids,
        region_code=data["region_code"]
    )
    
def search_video_info(product_id, product_name, product_group, video_ids, region_code):
    params = {
        'key': API_KEY,
        'part': 'snippet,statistics',
        'id': video_ids,
        'order': 'relevance',
        'regionCode': region_code,
        'maxResults': 50,
    }
    response = requests.get(URL + 'videos', params=params)
    resource = response.json()
    videos = resource['items']
    messages = []
    for video in videos:
        isVideo = (video["kind"] == "youtube#video")
        if (isVideo):
            stats = video["statistics"]
            stats.setdefault('viewCount', 0)
            stats.setdefault('likeCount', 0)
            stats.setdefault('favoriteCount', 0)
            stats.setdefault('commentCount', 0)
            hasComments = (stats["commentCount"] != 0)
            if (hasComments):
                messages.append({
                    "table_id"              : f"{PROJECT_ID}.{BQ_DATASET}.video",
                    "row"                   : [{
                        "product_id"            : product_id,
                        "product_name"          : product_name,
                        "product_group"         : product_group,
                        "video_id"              : video["id"],
                        "video_url"             : f"https://www.youtube.com/watch?v={video['id']}",
                        "video_published_at"    : video["snippet"]["publishedAt"],
                        "video_title"           : video["snippet"]["title"],
                        "video_description"     : video["snippet"]["description"].replace('\r', '\n').replace('\n', ' '),
                        "video_view_count"      : video["statistics"]["viewCount"],
                        "video_like_count"      : video["statistics"]["likeCount"],
                        "video_favorite_count"  : video["statistics"]["favoriteCount"],
                        "video_comment_count"   : video["statistics"]["commentCount"],
                        "video_thumbnail_url"   : video["snippet"]["thumbnails"]["high"]["url"],
                        "video_channel_id"      : video["snippet"]["channelId"],
                        "video_channel_title"   : video["snippet"]["channelTitle"],
                        "region_code"           : region_code
                    }]
                })
    publish_message_to_pubsub(messages)

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