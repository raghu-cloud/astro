import influxdb_client_3
from influxdb_client_3 import InfluxDBClient3, Point, WriteOptions, WritePrecision
from datetime import datetime
from dotenv import load_dotenv
import os
from context import get_request_id, get_user_id, get_channel, get_request_type


load_dotenv()

INFLUX_HOST = os.getenv("INFLUX_HOST")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")



client = InfluxDBClient3(host=INFLUX_HOST, database=INFLUX_BUCKET, token=INFLUX_TOKEN,timeout=20000)
# client = influxdb_client.InfluxDBClient(
#    url=INFLUX_HOST,
#    token=INFLUX_TOKEN,
#    org='dev'
# # )
# write_api = client.write_api(write_options=SYNCHRONOUS)

def log_point_to_db(
    health_metric: str,
    phase: str = None,
    action_button_category = None,
    detected_language: str = None,
    transcript: str = None,
    translation_from: str = None,
    translation_to: str = None,
    audio_duration: float = None,
    character_count: int = None,
    latency: float = None,
    model: str = None,
    model_version: str = None,
    success: bool = None,
    tokens:int=None,
    cost:float=None,

    
):

    
    point = Point("usage_metric_table")
    point = point.tag("request_id", get_request_id())
    point = point.tag("user_id", get_user_id())
    point = point.tag("channel", get_channel())
    point = point.tag("request_type", get_request_type())


    point = point.tag("health_metric_category", health_metric)

    if phase:
        point = point.tag("phase", phase)
    


    
    if detected_language is not None:
        point = point.tag("detected_language", detected_language)

    if transcript is not None:
        point = point.tag("transcript", transcript)

    if action_button_category is not None:
        point = point.tag("action_button_category", action_button_category)

    if model:
        point = point.tag("model", model)
    
    if model_version:
        point = point.tag("model_version", model_version)

    if translation_from is not None:
        point = point.tag("translation_from", translation_from)

    if translation_to is not None:
        point = point.tag("translation_to", translation_to)

    if audio_duration is not None:
        point = point.field("audio_duration", audio_duration)

    if character_count is not None:
        point = point.field("character_count", character_count)

    if latency is not None:
        point = point.field("latency", round(latency, 4))

    if success is not None:
        point = point.field("success", str(success).lower())
    if tokens:
        point = point.field("total_token", tokens)
    if cost:
        point = point.field("cost", cost)  # Store as 'true' or 'false'

    point = point.time(datetime.now(), WritePrecision.S)

    client.write( record=point, write_precision='s')
    # write_api.write( record=point, bucket=INFLUX_BUCKET,org='dev')
