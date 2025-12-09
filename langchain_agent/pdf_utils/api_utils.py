import requests
from dotenv import load_dotenv
import asyncio
import threading
import os
import aiohttp
import boto3
import random
from datetime import datetime
from langchain_agent.pdf_utils.generate_pdf import find_current_dasha
from langchain_agent.pdf_utils.generate_pdf import html_to_mobile_friendly_kundli, pg_i_j, merge_pdfs, generate_mobile_friendly_kundli
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import logging
import csv
from rapidfuzz import process, fuzz

load_dotenv()
divine_api_token=os.getenv('DIVINE_API_TOKEN')
divine_api_key=os.getenv('DIVINE_API_KEY')
aws_access_key=os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')

s3 = boto3.client("s3", aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_access_key)

logger = logging.getLogger(__name__)

def handle_generate_kundli(details, user_id):

    try:
        # pdf_s3_url=check_pdf_exists(user_id,'kundli')
        # if pdf_s3_url!=0:
        #     return pdf_s3_url
        if details["chart_type"] not in ["north", "south"]:
            return {"error": "Please provide a valid chart-type either north or south"}
        
        lat,lon = get_lat_lon_photon(details["place"])
        if lat is None or lon is None:
            print(lat,lon)
            return {"error": "Could not determine latitude/longitude for the given place."}
        
        details["lat"] = lat
        details["lon"] = lon

        timezone = get_timezone_offset(float(lat), float(lon))
        details["tzone"] = timezone
        
        urls = [
                "https://astroapi-3.divineapi.com/indian-api/v1/basic-astro-details",
                "https://astroapi-3.divineapi.com/indian-api/v1/planetary-positions",
                "https://astroapi-3.divineapi.com/indian-api/v1/sub-planet-positions",
                "https://astroapi-3.divineapi.com/indian-api/v1/sadhe-sati",
                "https://astroapi-3.divineapi.com/indian-api/v1/kaal-sarpa-yoga",
                "https://astroapi-3.divineapi.com/indian-api/v1/manglik-dosha",
                "https://astroapi-3.divineapi.com/indian-api/v1/composite-friendship",
                "https://astroapi-3.divineapi.com/indian-api/v1/shadbala",
                "https://astroapi-3.divineapi.com/indian-api/v1/ascendant-report",
                "https://astroapi-3.divineapi.com/indian-api/v1/yogas",
                "https://astroapi-3.divineapi.com/indian-api/v1/kaal-chakra-dasha",
                "https://astroapi-3.divineapi.com/indian-api/v1/ghata-chakra",
                "https://astroapi-3.divineapi.com/indian-api/v2/yogini-dasha",
                "https://astroapi-3.divineapi.com/indian-api/v1/sub-planet-chart",
                "https://astroapi-3.divineapi.com/indian-api/v1/sudarshana-chakra",
                "https://astroapi-3.divineapi.com/indian-api/v1/horoscope-chart/D1",
                "https://astroapi-3.divineapi.com/indian-api/v1/bhava-kundli/1",
                "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha",
            ]
        
        extra_urls = {
                "vimshottari-dasha": "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha",
                "maha-dasha-analysis": "https://astroapi-3.divineapi.com/indian-api/v1/maha-dasha-analysis",
                "antar-dasha-analysis": "https://astroapi-3.divineapi.com/indian-api/v1/antar-dasha-analysis",
                "pratyantar-dasha-analysis": "https://astroapi-3.divineapi.com/indian-api/v1/pratyantar-dasha-analysis",
            }
        
        headers = {"Authorization": f"Bearer {divine_api_token}"}

        place_list = load_places_from_csv("worldcities.csv")

        user_place = details["place"].capitalize()

        match, score = get_closest_match(user_place, place_list)

        if match:
            user_place = match

        payload = {
                "api_key": divine_api_key,
                "full_name": details["full_name"],
                "gender": details["gender"],
                "day": details["day"],
                "month": details["month"],
                "year": details["year"],
                "place": user_place,
                "lat": details["lat"],
                "lon": details["lon"],
                "tzone": details["tzone"],
                "hour": details["hour"],
                "min": details["min"],
                "sec": details["sec"],
                "lan": "en",
            }
        payload_dasha = {**payload, "dasha_type": "pratyantar-dasha"}

        
        data = asyncio.run(merge_fetch(urls=urls, headers=headers, payload=payload, payload_dasha=payload_dasha, extra_urls=extra_urls, chart_type=details["chart_type"] ))

        if "error" in data:
            return {"error": data["error"]}

        image_blob_name = f"{user_id}_kundli.pdf"

        # html_to_mobile_friendly_kundli(data, image_blob_name)
        # t1 = threading.Thread(target=pg_i_j, args=(data,1,3, ))
        # t2 = threading.Thread(target=pg_i_j, args=(data,3,5, ))
        # t3 = threading.Thread(target=pg_i_j, args=(data,5,7, ))
        # t4 = threading.Thread(target=pg_i_j, args=(data,7,9, ))
        # t5 = threading.Thread(target=pg_i_j, args=(data,9,11, ))
        # t6 = threading.Thread(target=pg_i_j, args=(data,11,13, ))
        # t7 = threading.Thread(target=pg_i_j, args=(data,13,15, ))
        # t8 = threading.Thread(target=pg_i_j, args=(data,15,17, ))
        # t9 = threading.Thread(target=pg_i_j, args=(data,17,20, ))
        # t1.start()
        # t2.start()
        # t3.start()
        # t4.start()
        # t5.start()
        # t6.start()
        # t7.start()
        # t8.start()
        # t9.start()
        # t1.join()
        # t2.join()
        # t3.join()
        # t4.join()
        # t5.join()
        # t6.join()
        # t7.join()
        # t8.join()
        # t9.join()
        # t1 = threading.Thread(target=pg_i_j, args=(data,1,6, ))
        # t2 = threading.Thread(target=pg_i_j, args=(data,6,11, ))
        # t3 = threading.Thread(target=pg_i_j, args=(data,11,15, ))
        # t4 = threading.Thread(target=pg_i_j, args=(data,15,20, ))
        # # t5 = threading.Thread(target=pg_i_j, args=(result,13,16, ))
        # # t6 = threading.Thread(target=pg_i_j, args=(result,16,20, ))
        # t1.start()
        # t2.start()
        # t3.start()
        # t4.start()
        # # t5.start()
        # # t6.start()
        # t1.join()
        # t2.join()
        # t3.join()
        # t4.join()

        # merge_pdfs(output_path= image_blob_name)
        asyncio.run(generate_mobile_friendly_kundli(data = data, user_id=user_id, output_path= image_blob_name))
        


        print("DONE")
        s3.upload_file(
            image_blob_name,
            "astro-ai",
            image_blob_name,
            ExtraArgs={"ACL": "public-read", "ContentType": "application/pdf"},
        )

        s3_url = f"https://astro-ai.s3.ap-south-1.amazonaws.com/{image_blob_name}"

        os.remove(f"{user_id}_kundli.pdf")
        for i in range(1,20):
            if os.path.exists(f"page{i}_mp_{user_id}.pdf"):
                os.remove(f"page{i}_mp_{user_id}.pdf")
                os.remove(f"page{i}_output_{user_id}.html")
                print(f"Removed: {f"page{i}_mp_{user_id}.pdf"}")
            else:
                print(f"File not found: {f"page{i}_mp_{user_id}.pdf"}")

        return s3_url
    
    except Exception as e:
        print(e)


def handle_panchang_details(details):
    try:
        # pdf_s3_url=check_pdf_exists(user_id,'kundli')
        # if pdf_s3_url!=0:
        #     return pdf_s3_url
        lat,lon = get_lat_lon_photon(details["place"])
        if lat is None or lon is None:
            return {"error": "Could not determine latitude/longitude for the given place."}
        
        details["lat"] = lat
        details["lon"] = lon
        # details["tzone"] = 5.5

        timezone = get_timezone_offset(float(lat), float(lon))
        details["tzone"] = timezone

        urls = [
            "https://astroapi-2.divineapi.com/indian-api/v1/find-sun-and-moon",
            "https://astroapi-1.divineapi.com/indian-api/v1/find-panchang",
            "https://astroapi-1.divineapi.com/indian-api/v1/find-nakshatra",
            "https://astroapi-1.divineapi.com/indian-api/v1/find-surya-nakshatra",
            "https://astroapi-1.divineapi.com/indian-api/v1/find-tithi",
            "https://astroapi-1.divineapi.com/indian-api/v1/find-yoga",
            "https://astroapi-1.divineapi.com/indian-api/v1/find-karana",
            "https://astroapi-2.divineapi.com/indian-api/v1/find-ritu-and-anaya",
            "https://astroapi-2.divineapi.com/indian-api/v1/find-samvat",
            "https://astroapi-2.divineapi.com/indian-api/v1/find-nivas-and-shool",
            "https://astroapi-2.divineapi.com/indian-api/v1/find-choghadiya",
            "https://astroapi-2.divineapi.com/indian-api/v1/find-chandrabalam-and-tarabalam",
            "https://astroapi-2.divineapi.com/indian-api/v1/find-other-calendars-and-epoch",
            "https://astroapi-3.divineapi.com/indian-api/v1/auspicious-timings",
            "https://astroapi-3.divineapi.com/indian-api/v1/inauspicious-timings",
            "https://astroapi-3.divineapi.com/indian-api/v1/panchak-rahita",
            "https://astroapi-3.divineapi.com/indian-api/v2/uday-lagna",
            "https://astroapi-3.divineapi.com/indian-api/v1/chandramasa",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/sun",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/moon",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/mercury",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/venus",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/earth",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/jupiter",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/saturn",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/uranus",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/neptune",
            "https://astroapi-3.divineapi.com/indian-api/v1/grah-gochar/pluto"

        ]

        headers = {"Authorization": f"Bearer {divine_api_token}"}

        place_list = load_places_from_csv("worldcities.csv")

        user_place = details["place"].capitalize()

        match, score = get_closest_match(user_place, place_list)

        if match:
            user_place = match

        payload = {
            "api_key": divine_api_key,
            "day": details['day'],
            "month": details['month'], 
            "year": details['year'],
            "place": user_place,
            "lat": details['lat'],
            "lon": details['lon'],
            "tzone": details['tzone'],
            "lan": "en"
        }

        data = asyncio.run(fetch_all_initial(urls=urls, headers=headers, payload=payload))

        check_for_error(data)


        if "error" in data:
            return {"error": data["error"]}
        
        return data
    
    except Exception as e:
        print(e)


def get_lat_lon_photon(place):
    """
    Retrieves the latitude and longitude for a given place name using the Photon geocoding API.

    This function sends a GET request to the Photon API with the place query and parses
    the response to extract geographic coordinates.

    Parameters:
    - place (str): The name of the location to geocode (e.g., city, address, landmark).

    Returns:
    - (lat, lon) (tuple of str or None): 
        - A tuple containing the latitude and longitude as strings if found.
        - Returns (None, None) if no coordinates are found or an error occurs.

    Notes:
    - Uses the first match returned by the Photon API.
    - Logs any exceptions and returns (None, None) in case of failure.
    """
    try:
        url = "https://photon.komoot.io/api/"
        params = {
            "q": place
        }
        response = requests.get(url, params=params)
        data = response.json()

        if data['features']:
            lon, lat = data['features'][0]['geometry']['coordinates']
            return str(lat), str(lon)
        else:
            return None, None
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return None, None
    finally:
        logger.info("completed")
    
def check_for_error(result):
    error = []
    for key, val in result.items():
        if "success" in val and val["success"] == 2:
            if val["msg"] not in error:
                error.append(val["msg"])
    print(error)
    if len(error)>0:
        result["error"] = error
        print(result)


# def get_lat_lon_photon(place):
#     url = "https://photon.komoot.io/api/"
#     params = {
#         "q": place
#     }
#     response = requests.get(url, params=params)
#     data = response.json()

#     if data['features']:
#         lon, lat = data['features'][0]['geometry']['coordinates']
#         return str(lat), str(lon)
#     else:
#         return None, None


def check_pdf_exists(user_id, category):
    """
    Downloads a PDF file from an S3 bucket based on user ID and category.

    Parameters:
    - user_id (str or int): The unique identifier for the user.
    - category (str): The category of the PDF (e.g., 'kundli', 'report').

    Returns:
    - int: 
        - 1 if the file was successfully downloaded.
        - 0 if the file does not exist or an error occurred.

    Notes:
    - The function checks if the file exists using a HEAD request before downloading.
    - The file is saved locally using the format "{user_id}_{category}.pdf".
    """
    try:
        image_blob_name = f"{user_id}_{category}.pdf"
        s3_url = f"https://astro-ai.s3.ap-south-1.amazonaws.com/{image_blob_name}"
        print("got file")

        # Check if file exists on S3
        head_response = requests.head(s3_url)
        if head_response.status_code == 200:
            # File exists, proceed with download
            response = requests.get(s3_url, stream=True)
            return s3_url
            
        else:
            print(f"File not found at {s3_url}. HTTP Status Code: {head_response.status_code}")
            return 0

    except Exception as e:
        print(f"An error occurred while downloading the PDF: {e}")
        return 0
    
async def fetch(session, headers, url, payload=None, payload_dasha=None, chart_type="south", custom_payload=None, retries=5, delay=1):
    for attempt in range(retries):
        try:
            payload_to_send = custom_payload or payload.copy()

            if "horoscope-chart" in url:
                payload_to_send["chart_type"] = chart_type
            if "vimshottari-dasha" in url:
                payload_to_send = payload_dasha.copy()

            async with session.post(url, data=payload_to_send, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status == 503:
                    print(f"Attempt {attempt+1}: 503 Service Unavailable. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                elif response.status == 429:
                    wait_time = random.uniform(2, 6)  # Random wait between 2 to 6 seconds
                    print(f"Attempt {attempt+1}: 429 Too Many Requests. Waiting {wait_time:.2f}s before retrying...")
                    await asyncio.sleep(wait_time)
                    continue
                elif response.status >= 400:
                    print(f"Attempt {attempt+1}: HTTP {response.status}. Retrying...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue

                # Try to parse JSON safely
                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    print(f"Attempt {attempt+1}: Unexpected Content Type, could not decode JSON. Retrying...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue

        except aiohttp.ClientError as e:
            print(f"Attempt {attempt+1}: Client error {e}. Retrying...")
            await asyncio.sleep(delay)
            delay *= 2
    return None  # After all retries fail

async def fetch_all_initial(urls, headers, payload, payload_dasha=None, chart_type="south"):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            key = url.rstrip("/").split("/")[-1]
            tasks.append((key, fetch(session, headers, url, payload, payload_dasha, chart_type=chart_type)))
        
        results = await asyncio.gather(*[task[1] for task in tasks])
        
        merged_data = {}
        grah_gochar = {}
        for (key, _), result in zip(tasks, results):
            if key in ["sun", "moon", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus","neptune", "pluto"]:
                grah_gochar[key] = result
                continue
            merged_data[key] = result
        merged_data["grah_gochar"] = grah_gochar

        return merged_data
    
async def fetch_dasha_related(lower_case_dashas, extra_urls, headers):   
    async with aiohttp.ClientSession() as session:
        tasks = []

        
        payload_maha = {
            "api_key": divine_api_key,
            "maha_dasha": lower_case_dashas["Maha Dasha"],
            "lan": "en"
        }
        tasks.append(("mahadasha-analysis", fetch(session, headers, extra_urls["maha-dasha-analysis"], custom_payload=payload_maha)))

        payload_antar = {
            "api_key": divine_api_key,
            "maha_dasha": lower_case_dashas["Maha Dasha"],
            "antar_dasha": lower_case_dashas["Antar Dasha"],
            "lan": "en"
        }
        tasks.append(("antardasha-analysis", fetch(session, headers, extra_urls["antar-dasha-analysis"], custom_payload=payload_antar)))

        payload_pratyantar = {
            "api_key": divine_api_key,
            "maha_dasha": lower_case_dashas["Maha Dasha"],
            "antar_dasha": lower_case_dashas["Antar Dasha"],
            "pratyantar_dasha": lower_case_dashas["Pratyantar Dasha"],
            "lan": "en"
        }
        tasks.append(("pratyantardasha-analysis", fetch(session, headers, extra_urls["pratyantar-dasha-analysis"], custom_payload=payload_pratyantar)))

        results = await asyncio.gather(*[task[1] for task in tasks])

        merged_data = {}
        for (key, _), result in zip(tasks, results):
            merged_data[key] = result
        return merged_data
    

async def merge_fetch(urls, extra_urls, headers, payload, payload_dasha, chart_type = "south"):
    data = await fetch_all_initial(urls, headers, payload, payload_dasha, chart_type=chart_type)
    # print(data)

    for section_name, section_data in data.items():
        if isinstance(section_data, dict) and section_data.get("success") == 2:
            error_msgs = section_data.get("msg", [])
            return {"error": error_msgs[0] if error_msgs else f"Error in section: {section_name}"}

    today = datetime.today()

    current_user_dashas = find_current_dasha(data['vimshottari-dasha']['data'], today)
    lower_case_current_user_dashas = {x: current_user_dashas[x].lower() for x in current_user_dashas.keys()}

    dasha_data = await fetch_dasha_related(lower_case_current_user_dashas,extra_urls, headers)

    # Merge dasha analysis into the main data
    data.update(dasha_data)
    print("DATA",data)

    return data


def get_timezone_offset(lat,lon):
    tf = TimezoneFinder()
    
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if not timezone_str:
        return "Timezone not found"
    
    timezone = pytz.timezone(timezone_str)
    offset = timezone.utcoffset(datetime.now())
    return offset.total_seconds() / 3600 # Return as float hours


def load_places_from_csv(filepath):
    places = []
    with open(filepath, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['country'].capitalize() == 'India':
                places.append(row['city'].capitalize())
        places.append("Bengaluru")
    return places

def get_closest_match(user_input, places):
    # Always return best match even if score is low
    match_result = process.extractOne(user_input, places, scorer=fuzz.ratio)
    
    if match_result:
        match, score, _ = match_result
        return match, score
    return None, None