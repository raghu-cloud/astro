import os
import django
from jinja2 import Environment, FileSystemLoader
import asyncio
import aiohttp
import json
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
# from langchain_core.tools import tool
from django.shortcuts import render
from django.conf import settings
from pathlib import Path
from PyPDF2 import PdfMerger
import multiprocessing
from django.conf import settings
import os
import re
import json
import logging
import requests
import subprocess
import asyncio
import aiohttp
import ast
import io
import time
 # PyMuPDF
import base64
import os
# from langchain_community.document_loaders import UnstructuredMarkdownLoader
from asgiref.sync import sync_to_async
from datetime import datetime
import base64
from io import BytesIO
from django.conf import settings
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
import boto3
import json
import random
from langchain_agent.models import User
from gtts import gTTS
import langchain_agent.utils
import boto3
from openai import OpenAI
from timing_test_csv_utils import log_time_to_csv
from influx import log_point_to_db
import influxdb_client_3
from influxdb_client_3 import InfluxDBClient3, Point, WriteOptions
import threading
from context import get_user_id


load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "My_AI_Guruji.settings")
django.setup()
client = InfluxDBClient3(host=f"https://us-east-1-1.aws.cloud2.influxdata.com",
                        database=f"test",
                        token=f"k6zczicQycuY-bNy2YsSSyV2LtknOWO5ss7XdtHL035Qaf9uit2QacAUq0jDCJdtyxpBqqP3H9xOYuJMflWEWA==")
BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)

# Get database connection details from environment variables
db_host = os.getenv('DB_HOST', 'db')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'astro_ai')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'postgres')

divine_api_token=os.getenv('DIVINE_API_TOKEN')
divine_api_key=os.getenv('DIVINE_API_KEY')
# Construct the connection string
astro_conn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

if settings.LOAD_TEST_MODE:
    test_db_host = os.getenv('TEST_DB_HOST', 'db')
    test_db_port = os.getenv('TEST_DB_PORT', '5432')
    test_db_name = os.getenv('TEST_DB_NAME', 'astro_ai')
    test_db_user = os.getenv('TEST_DB_USER', 'postgres')
    test_db_password = os.getenv('TEST_DB_PASSWORD', 'postgres')
    astro_conn = f"postgresql://{test_db_user}:{test_db_password}@{test_db_host}:{test_db_port}/{test_db_name}"


s3 = boto3.client("s3",aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))


class MobilePDFGenerator:
    def __init__(self, template_dir=".", base_path=os.getcwd()):
        self.template_dir = template_dir
        self.base_path = base_path
        self.browser = None
        self.context = None
        self.iphone = None
        self.env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))

    async def start(self):
        self.playwright = await async_playwright().start()
        self.iphone = self.playwright.devices["iPhone 12"]
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(**self.iphone)

    async def stop(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def _render_single_pdf(self, result: dict, k: int, user_id):

        template = self.env.get_template(f'page{k}.html')
        html_content = template.render(report=result)

        
        with open(f'page{k}_output_{user_id}.html', 'w') as f:
            f.write(html_content)
        output_html_path = f"{self.base_path}/page{k}_output_{user_id}.html"

        page = await self.context.new_page()
        await page.goto(f"file://{output_html_path}")
        await page.wait_for_load_state("networkidle")
        await page.emulate_media(media="screen")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        scroll_height = await page.evaluate("document.body.scrollHeight")
        pdf_height = scroll_height + 20

        await page.pdf(
            path=f"page{k}_mp_{user_id}.pdf",
            width=f"{self.iphone['viewport']['width']}px",
            height=f"{pdf_height}px",
            print_background=True,
            prefer_css_page_size=True
        )
        await page.close()

    async def generate_all_pdfs_concurrently(self, result: dict, i: int, j: int, user_id):
        tasks = [self._render_single_pdf(result, k, user_id) for k in range(i, j)]
        await asyncio.gather(*tasks)

    def merge_pdfs(self, i: int, j: int, user_id, output_path="final_merged_asyncio.pdf"):
        merger = PdfMerger()
        for k in range(i, j):
            pdf_path =  f"page{k}_mp_{user_id}.pdf"
            if os.path.exists(pdf_path):
                merger.append(pdf_path)
            else:
                logger.error(f"Warning: Missing {pdf_path}, skipping.")
        # output_file = os.path.join(self.base_path, output_path)
        merger.write(output_path)
        merger.close()
        logger.info(f"Merged PDF saved to {output_path}")

async def generate_mobile_friendly_kundli(data, user_id, output_path):
    """
    Asynchronously generates a multi-page, mobile-optimized Kundli PDF and merges all pages into one.

    Parameters:
    - data (dict): The data used for rendering Kundli content across pages (passed to templates).
    - user_id (str or int): Unique identifier used to generate user-specific filenames.
    - output_path (str): Full path where the final merged PDF should be saved.

    Workflow:
    - Initializes a `MobilePDFGenerator` instance.
    - Starts the Playwright browser session.
    - Calls `generate_all_pdfs_concurrently()` to render and save multiple PDF pages concurrently.
      - Pages are expected to be rendered using templates like `page1.html` to `page19.html`.
      - PDFs are named `page{i}_mp_{user_id}.pdf`.
    - Stops the browser session.
    - Merges all generated PDFs (from page 1 to 19) into a single file at `output_path`.

    Notes:
    - Requires the `MobilePDFGenerator` class to implement `start()`, `stop()`, `generate_all_pdfs_concurrently()`, and `merge_pdfs()` methods.
    - All operations are performed asynchronously and are suitable for event-loop based environments like FastAPI.
    - Intermediate files are not cleaned up automatically unless handled within the generator class.

    Error Handling:
    - Logs any exception using `logger.error`.

    Returns:
    - None. Output is written to disk at `output_path`.
    """

    try:
    # start = time.time()
        generator = MobilePDFGenerator()
        await generator.start()
        await generator.generate_all_pdfs_concurrently(data, i=1, j=20, user_id=user_id)
        await generator.stop()
        generator.merge_pdfs(i=1, j=20,user_id=user_id, output_path=output_path)
    except Exception as e:
        logger.error(f"Error {e}")


async def html_to_pdf_kundli(html_content, output_path):
    """
    Converts given HTML content into a high-quality PDF file using Playwright's Chromium engine.

    Parameters:
    - html_content (str): The HTML string to render.
    - output_path (str): The file path where the output PDF will be saved.

    Notes:
    - Uses a Chromium browser with specific viewport settings for A4 output.
    - Waits for network to be idle and adds a slight delay before generating PDF.
    """
    try:
  
    
        async with async_playwright() as p:
            # Launch browser with specific arguments for better PDF rendering
            browser = await p.chromium.launch(
                args=["--disable-web-security", "--font-render-hinting=none"]
            )
            
            # Create context with proper viewport
            context = await browser.new_context(
                viewport={"width": 850, "height": 1123},  # A4 size in pixels
                device_scale_factor=1.5  # Higher resolution rendering
            )
            
            page = await context.new_page()
            
            # Set the content with the extra CSS
            await page.set_content(html_content)
            
            # Wait for rendering
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)
            
            # Generate PDF with no margins
            await page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "5mm", "right": "5mm", "bottom": "5mm", "left": "5mm"},
                scale=1.0
            )
            
            await browser.close()
    except Exception as e:
        logger.error(f"Error {e}")

# def html_to_mobile_friendly_kundli(html_content, output_path):
#     with sync_playwright() as p:
#         iphone = p.devices["iPhone 12"]

#         browser = p.chromium.launch()
#         context = browser.new_context(**iphone)

#         page = context.new_page()
#         page.set_content(html_content)
#         page.wait_for_load_state("networkidle")

#         # Emulate screen media (not print)
#         page.emulate_media(media="screen")

#         # Scroll to bottom to trigger any lazy content
#         page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

#         # Get full page height
#         scroll_height = page.evaluate("document.body.scrollHeight")
#         #for emptying space at end
#         # pdf_height = scroll_height + 700 

#         # Generate PDF matching full rendered screen layout
#         page.pdf(
#             path=output_path,
#             width=f"{iphone['viewport']['width']}px",
#             height=f"{scroll_height}px",
#             print_background=True,
#             prefer_css_page_size=True
#         )

#         browser.close()
def html_to_mobile_friendly_kundli(result, output_path):
    """
    Generates a mobile-optimized multi-page Kundli PDF using HTML templates and the Playwright library.

    Parameters:
    - result (dict): Data dictionary used to populate each template page (`report` context variable).
    - output_path (str): Full file path where the final merged PDF will be saved.

    Workflow:
    - Loads HTML templates named `page1.html` to `page19.html` from the `templates` directory.
    - Renders each page using the Jinja2 templating engine with `result` data.
    - Emulates an iPhone 12 browser environment to simulate mobile view.
    - Dynamically scrolls to bottom and adjusts PDF height to match scroll height for better mobile rendering.
    - Saves each rendered page as an individual PDF file (`page{i}.pdf`).
    - Merges all generated PDFs into a single output PDF at `output_path`.

    Notes:
    - Requires the following packages: `playwright`, `jinja2`, `PyPDF2`.
    - Templates must be located in the `templates` directory under `BASE_DIR`.
    - Assumes up to 19 pages (`page1.html` to `page19.html`); skips none silently.

    Error Handling:
    - Logs any exceptions encountered during rendering, PDF generation, or merging using `logger`.

    Returns:
    - None. Output is written to disk at `output_path`.
    """

    try:
    
        with sync_playwright() as p:
            iphone = p.devices["iPhone 12"]
            browser = p.chromium.launch()
            context = browser.new_context(**iphone)

            for i in range(1, 20):
                # env = Environment(loader=FileSystemLoader('.'))
                env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))
                # template = env.get_template('mobile_friendly_kundli_template.html')
                template = env.get_template(f'page{i}.html')

                html_content = template.render(report=result)
            

                page = context.new_page()
                page.set_content(html_content)
                page.wait_for_load_state("networkidle")
                page.emulate_media(media="screen")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                scroll_height = page.evaluate("document.body.scrollHeight")
                pdf_height = scroll_height+20

                page.pdf(
                    path=f"page{i}.pdf",
                    width=f"{iphone['viewport']['width']}px",
                    height=f"{pdf_height}px",
                    print_background=True,
                    prefer_css_page_size=True
                )
                page.close()

            browser.close()


        # Create a merger object
        merger = PdfMerger()

        # Append each PDF to the merger
        for i in range(1,20):
            merger.append(f"page{i}.pdf")

        # Write out the merged PDF
        with open(output_path, "wb") as output_file:
            merger.write(output_file)

        # Close the merger
        merger.close()
    except Exception as e:
        logger.error(f"Error {e}")


def pg_i_j(result, i, j, user_id):
    """
    Renders Jinja2 HTML templates into mobile-friendly PDFs using Playwright.

    Parameters:
    - result (dict): Context data passed to Jinja2 templates.
    - i (int): Start index (inclusive) for page templates.
    - j (int): End index (exclusive) for page templates.
    - user_id (str): A unique identifier used in output file names.

    Workflow:
    - Loads templates named `page{i}.html` from the `templates` directory.
    - Renders each template with `result`, writes the intermediate HTML to disk.
    - Opens the rendered HTML in a mobile-emulated Chromium browser (iPhone 12).
    - Scrolls to bottom to get dynamic height and exports to PDF.
    - Saves output PDF as `page{k}_mp_{user_id}.pdf`.
    """
    try:
        with sync_playwright() as p:
            iphone = p.devices["iPhone 12"]
            browser = p.chromium.launch()
            context = browser.new_context(**iphone)
            base_dir = os.getcwd()


            for k in range(i, j):

                env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))
                template = env.get_template(f'page{k}.html')
                html_content = template.render(report=result)
                with open(f'page{k}_output_{user_id}.html', 'w') as file:
                    file.write(html_content)


                html_file_path = base_dir+f"/page{k}_output_{user_id}.html"
                url = f"file://{html_file_path}"
        
                page = context.new_page()
                # page.set_content(html_content)
                page.goto(url)
                page.wait_for_load_state("networkidle")
                page.emulate_media(media="screen")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                scroll_height = page.evaluate("document.body.scrollHeight")
                pdf_height = scroll_height+20
                # user_id = get_user_id()

                page.pdf(
                    path=f"page{k}_mp_{user_id}.pdf",
                    width=f"{iphone['viewport']['width']}px",
                    height=f"{pdf_height}px",
                    print_background=True,
                    prefer_css_page_size=True
                )
                page.close()

            browser.close()
    except Exception as e:
        logger.error(f"Error {e}")


def merge_pdfs(output_path, user_id):
    """
    Merges multiple single-page PDFs into a single output PDF for a specific user.

    Parameters:
    - output_path (str): Full path (including filename) where the final merged PDF will be saved.
    - user_id (str or int): Unique identifier used to locate individual page PDFs belonging to the user.

    Workflow:
    - Looks for files named in the format: "page1_mp_<user_id>.pdf" through "page19_mp_<user_id>.pdf".
    - Appends each existing file (in order) to a PDF merger.
    - Logs missing files and skips them gracefully.
    - Writes the merged result to `output_path` if any valid pages were found.
    - Closes the merger object after processing.

    Returns:
    - None. The output is saved as a file to `output_path`.

    Logs:
    - Logs each missing page as an error.
    - Logs success message on successful write.
    - Logs a general error message if an exception is raised during the merging process.

    Notes:
    - Assumes that the page PDFs are named sequentially and exist in the current working directory.
    - Uses `PdfMerger` from `PyPDF2`. Ensure PyPDF2 is installed (`pip install PyPDF2`).
    """
    try:
        merger = PdfMerger()

        for i in range(1, 20):
            filename = f"page{i}_mp_{user_id}.pdf"
            if os.path.exists(filename):
    
                merger.append(filename)
            else:
                logger.error(f"Skipping missing file: {filename}")

        if merger.pages:
            merger.write(output_path)
            logger.info(f"Saved merged PDF to: {output_path}")
        else:
            logger.error("No PDFs found to merge.")
            
        merger.close()
    except Exception as e:
        logger.error(f"Error {e}")


async def html_to_pdf_horoscope(html_content, output_path):
    """
    Asynchronously renders HTML content to a PDF file using Playwright with a headless Chromium browser.

    Parameters:
    - html_content (str): The raw HTML string to be converted into a PDF.
    - output_path (str): The full file path (including filename) where the generated PDF will be saved.

    Workflow:
    - Launches a Chromium browser with appropriate arguments to ensure compatibility in restricted environments (e.g., Docker, Linux server).
    - Creates a new browser context with custom viewport and device scale factor to improve rendering.
    - Loads the HTML content into a new page and waits for the network to be idle and rendering to stabilize.
    - Generates a PDF with A4 format, background graphics, and minimal margins.
    - Enforces a timeout of 30 seconds for PDF generation to prevent hanging.

    Returns:
    - None. Writes the PDF directly to `output_path`.

    Logs:
    - Logs success or timeout messages, and any exceptions encountered during rendering or PDF generation.

    Notes:
    - Requires `async_playwright` and a working Playwright installation (`playwright install` should be run beforehand).
    - This function is designed for generating horoscope PDFs but can be reused for any HTML-to-PDF conversion with minor tweaks.
    """
    try:
        async with async_playwright() as p:
        
            browser = await p.chromium.launch(
                args=["--disable-web-security", "--font-render-hinting=none", "--disable-dev-shm-usage", "--no-sandbox"]
            )
            

            context = await browser.new_context(
                viewport={"width": 850, "height": 1123},
                device_scale_factor=1.5
            )
            
        
            page = await context.new_page()
            
        
            await page.set_content(html_content)
            
        
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)
            
            
            try:
                # Add timeout to the PDF generation
                await asyncio.wait_for(
                    page.pdf(
                        path=output_path,
                        format="A4",
                        print_background=True,
                        margin={"top": "5mm", "right": "5mm", "bottom": "5mm", "left": "5mm"},
                        scale=1.0
                    ),
                    timeout=30.0  # 30 second timeout
                )
                logger.info("PDF generated successfully")
            except asyncio.TimeoutError:
                logger.error("PDF generation timed out!")
            finally:
                logger.info("Closing browser...")
                await browser.close()
    except Exception as e:
        logger.error(f"Error {e}")




def parse_date(date_str):
    """Parse date string into datetime object"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d') if date_str != '--' else None
    except Exception as e:
        logger.error(f"Error {e}")

def find_current_dasha(data, today):
    # Find current Maha Dasha
    try:
        current_maha = None
        for maha_name, maha_data in data['maha_dasha'].items():
            start = parse_date(maha_data['start_date'])
            end = parse_date(maha_data['end_date'])
            if start <= today <= end:
                current_maha = (maha_name, maha_data)
                break
        
        if not current_maha:
            return "No current Maha Dasha found"
        
        # Find current Antar Dasha
        maha_name, maha_data = current_maha
        current_antar = None
        for antar_name, antar_data in maha_data['antar_dasha'].items():
            start = parse_date(antar_data['start_time'])
            end = parse_date(antar_data['end_time'])
            if start and end and start <= today <= end:
                current_antar = (antar_name, antar_data)
                break
        
        if not current_antar:
            return f"Current Maha Dasha: {maha_name} (No Antar Dasha found)"
        
        # Find current Pratyantar Dasha
        antar_name, antar_data = current_antar
        current_pratyantar = None
        for pratyantar_name, pratyantar_data in antar_data['pratyantar_dasha'].items():
            start = parse_date(pratyantar_data['start_time'])
            end = parse_date(pratyantar_data['end_time'])
            if start and end and start <= today <= end:
                current_pratyantar = pratyantar_name
                break
        
        if not current_pratyantar:
            return f"Current: {maha_name} - {antar_name} (No Pratyantar Dasha found)"
        
        return {
            'Maha Dasha': maha_name,
            'Antar Dasha': antar_name,
            'Pratyantar Dasha': current_pratyantar
        }
    except Exception as e:
        logger.error(f"Error {e}")



def download_pdf(user_id, category):

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
        destination_file = image_blob_name


        # Check if file exists on S3
        head_response = requests.head(s3_url)
        if head_response.status_code == 200:
            # File exists, proceed with download
            response = requests.get(s3_url, stream=True)
            with open(destination_file, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return 1
        else:
            logger.error(f"File not found at {s3_url}. HTTP Status Code: {head_response.status_code}")
            return 0

    except Exception as e:
        logger.error(f"An error occurred while downloading the PDF: {e}")
        return 0
    
async def fetch(session, headers, url, payload=None, payload_dasha=None,custom_payload=None, retries=5, delay=1):
    """
    Makes a POST request with retry logic and exponential backoff.

    Parameters:
    - session (aiohttp.ClientSession): The active HTTP session.
    - headers (dict): Headers to be used in the request.
    - url (str): Target URL.
    - payload (dict): Default payload.
    - payload_dasha (dict): Optional alternate payload for 'vimshottari-dasha' endpoints.
    - custom_payload (dict): Specific override payload.
    - retries (int): Number of retry attempts.
    - delay (int): Initial delay (in seconds) for retries.

    Returns:
    - dict or None: JSON-decoded response data or None if all retries fail.
    """
    try:
            
        for attempt in range(retries):
            try:
                payload_to_send = custom_payload or payload.copy()

                if "horoscope-chart" in url:
                    payload_to_send["chart_type"] = "south"
                if "vimshottari-dasha" in url:
                    payload_to_send = payload_dasha.copy()

                async with session.post(url, data=payload_to_send, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status == 503:
                        logger.info(f"Attempt {attempt+1}: 503 Service Unavailable. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    elif response.status == 429:
                        wait_time = random.uniform(2, 6)  # Random wait between 2 to 6 seconds
                        logger.info(f"Attempt {attempt+1}: 429 Too Many Requests. Waiting {wait_time:.2f}s before retrying...")
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status >= 400:
                        logger.info(f"Attempt {attempt+1}: HTTP {response.status}. Retrying...")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

                    # Try to parse JSON safely
                    try:
                        return await response.json()
                    except aiohttp.ContentTypeError:
                        logger.error(f"Attempt {attempt+1}: Unexpected Content Type, could not decode JSON. Retrying...")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

            except aiohttp.ClientError as e:
                logger.error(f"Attempt {attempt+1}: Client error {e}. Retrying...")
                await asyncio.sleep(delay)
                delay *= 2
        return None  # After all retries fail
    except Exception as e:
        logger.error(f"Error {e}")


async def fetch_all_initial(urls, headers, payload, payload_dasha):
    """
    Asynchronously fetches initial data from multiple URLs and merges the results into a dictionary.

    This function:
    - Iterates over a list of URLs.
    - For each URL, extracts a unique key from the URL's last path segment.
    - Uses the provided `fetch` function to make asynchronous HTTP requests with the given headers and payloads.
    - Gathers responses concurrently using `asyncio.gather`.
    - Merges the responses into a dictionary with keys corresponding to the URL's last segment.

    Parameters:
    - urls (list): A list of URLs (str) from which to fetch data.
    - headers (dict): A dictionary of HTTP headers to include in each request.
    - payload (dict): A dictionary containing the general payload parameters for the requests.
    - payload_dasha (dict): A dictionary containing additional dasha-specific payload parameters.

    Returns:
    - dict: A dictionary where each key is derived from the URL (last segment) and the value is the response
            obtained from the corresponding fetch call.

    Raises:
    - Logs and propagates any exceptions encountered during the fetching or merging process.
"""
    try:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                key = url.rstrip("/").split("/")[-1]
                tasks.append((key, fetch(session, headers, url, payload, payload_dasha)))
            
            results = await asyncio.gather(*[task[1] for task in tasks])
            
            merged_data = {}
            for (key, _), result in zip(tasks, results):
                merged_data[key] = result
            return merged_data
    except Exception as e:
        logger.error(f"Error {e}")


async def fetch_dasha_related(lower_case_dashas, extra_urls, headers):  
    """
    Asynchronously fetches Dasha-related astrology data (Maha, Antar, and Pratyantar dashas)
    by making concurrent API calls to external services.

    Parameters:
    - lower_case_dashas (dict): A dictionary containing the following keys in lowercase:
        - "Maha Dasha"
        - "Antar Dasha"
        - "Pratyantar Dasha"
    - extra_urls (dict): A dictionary mapping dasha types to their corresponding API URLs. Expected keys:
        - "maha-dasha-analysis"
        - "antar-dasha-analysis"
        - "pratyantar-dasha-analysis"
    - headers (dict): A dictionary of HTTP headers to include with each request (e.g., for authentication).

    Returns:
    - dict: A dictionary with keys:
        - "mahadasha-analysis"
        - "antardasha-analysis"
        - "pratyantardasha-analysis"
      Each key maps to the parsed response returned from the respective API call.

    Notes:
    - Makes use of aiohttp for asynchronous HTTP requests and asyncio.gather to perform all requests concurrently.
    - Each API call includes an API key (`divine_api_key`) and appropriate dasha parameters.
    - Assumes that `fetch` is an awaitable function that performs the POST request and returns the JSON-decoded response.

    Error Handling:
    - Logs any exceptions encountered and returns `None`.

    Dependencies:
    - `divine_api_key` must be defined globally or imported.
    - `fetch(session, url, custom_payload, headers)` must be defined elsewhere in your codebase.
    """
 
    try:

        async with aiohttp.ClientSession() as session:
            tasks = []

            
            payload_maha = {
                "api_key": divine_api_key,
                "maha_dasha": lower_case_dashas["Maha Dasha"],
                "lan": "en"
            }
            tasks.append(("mahadasha-analysis", fetch(session, url=extra_urls["maha-dasha-analysis"], custom_payload=payload_maha,headers=headers)))

            payload_antar = {
                "api_key": divine_api_key,
                "maha_dasha": lower_case_dashas["Maha Dasha"],
                "antar_dasha": lower_case_dashas["Antar Dasha"],
                "lan": "en"
            }
            tasks.append(("antardasha-analysis", fetch(session, url=extra_urls["antar-dasha-analysis"], custom_payload=payload_antar,headers=headers)))

            payload_pratyantar = {
                "api_key": divine_api_key, 
                "maha_dasha": lower_case_dashas["Maha Dasha"],
                "antar_dasha": lower_case_dashas["Antar Dasha"],
                "pratyantar_dasha": lower_case_dashas["Pratyantar Dasha"],
                "lan": "en"
            }
            tasks.append(("pratyantardasha-analysis", fetch(session, url=extra_urls["pratyantar-dasha-analysis"], custom_payload=payload_pratyantar,headers=headers)))

            results = await asyncio.gather(*[task[1] for task in tasks])

            merged_data = {}
            for (key, _), result in zip(tasks, results):
                merged_data[key] = result
            return merged_data
    except Exception as e:
        logger.error(f"Error {e}")

async def main(urls, extra_urls, headers, payload, payload_dasha):
    """
    Main coroutine to orchestrate fetching of initial and dasha-related astrology data.

    Parameters:
    - urls (list): List of endpoint URLs for initial data fetch.
    - extra_urls (dict): Dictionary containing URLs for dasha-related endpoints.
    - headers (dict): Headers to be used in all API requests.
    - payload (dict): Common payload for general requests.
    - payload_dasha (dict): Payload specifically for the vimshottari-dasha endpoint.

    Returns:
    - dict: Merged data including initial astrology data and dasha analysis.
    """

    try:
        data = await fetch_all_initial(urls, headers, payload, payload_dasha)


        today = datetime.today()

        current_user_dashas = find_current_dasha(data['vimshottari-dasha']['data'], today)
        lower_case_current_user_dashas = {x: current_user_dashas[x].lower() for x in current_user_dashas.keys()}

        dasha_data = await fetch_dasha_related(lower_case_current_user_dashas,extra_urls, headers)

        # Merge dasha analysis into the main data
        data.update(dasha_data)

        return data
    except Exception as e:
        logger.error(f"Error {e}")




def call_divine(details, user_id, msg_id, msg_type):
    """
    Sends a request or processes auspicious-related logic using the provided details.

    Parameters:
    - details (dict): Input data containing relevant user or astrological information.
    - user_id (str or int): The ID of the user initiating the request.
    - pdf_name (str): The name of the PDF file to be used or generated in the process.

    Returns:
    - bool: True if the operation was successful, False otherwise.

    Notes:
    - Exceptions are caught and logged internally. Function returns False on failure.
    """

    start_total = time.time()

    chat_id = user_id

    try:
        
      

        kundli_api_requests_start = time.time()
       
        urls = [
            "https://astroapi-3.divineapi.com/indian-api/v1/basic-astro-details",
            "https://astroapi-3.divineapi.com/indian-api/v1/planetary-positions",
            "https://astroapi-3.divineapi.com/indian-api/v1/sub-planet-positions",
            # "https://astroapi-3.divineapi.com/indian-api/v1/kp/planetary-positions",
            "https://astroapi-3.divineapi.com/indian-api/v1/sadhe-sati",
            "https://astroapi-3.divineapi.com/indian-api/v1/kaal-sarpa-yoga",
            "https://astroapi-3.divineapi.com/indian-api/v1/manglik-dosha",
            " https://astroapi-3.divineapi.com/indian-api/v1/composite-friendship",
            # #    "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha",
            "https://astroapi-3.divineapi.com/indian-api/v1/shadbala",
            #    "https://astroapi-3.divineapi.com/indian-api/v2/gemstone-suggestion",
            "https://astroapi-3.divineapi.com/indian-api/v1/ascendant-report",
            "https://astroapi-3.divineapi.com/indian-api/v1/yogas",
            "https://astroapi-3.divineapi.com/indian-api/v1/kaal-chakra-dasha",
            "https://astroapi-3.divineapi.com/indian-api/v1/ghata-chakra",
            # "https://astroapi-3.divineapi.com/indian-api/v1/planet-analysis",
            "https://astroapi-3.divineapi.com/indian-api/v2/yogini-dasha",
            "https://astroapi-3.divineapi.com/indian-api/v1/sub-planet-chart",
            "https://astroapi-3.divineapi.com/indian-api/v1/sudarshana-chakra",
            "https://astroapi-3.divineapi.com/indian-api/v1/horoscope-chart/D1",
            "https://astroapi-3.divineapi.com/indian-api/v1/bhava-kundli/1",
          "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha",
        ]
      

        filtered_endpoints = [url.rstrip("/").split("/")[-1] for url in urls]
        divine_api_token=os.getenv('DIVINE_API_TOKEN')
        divine_api_key=os.getenv('DIVINE_API_KEY')
        # Replace with your actual token
        token = divine_api_token
        key = divine_api_key

        headers = {"Authorization": f"Bearer {token}"}  # Bearer Token Authentication
        url_dasha = "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha"
        url_maha_dasha = (
            "https://astroapi-3.divineapi.com/indian-api/v1/maha-dasha-analysis"
        )
        url_antar_dasha = (
            "https://astroapi-3.divineapi.com/indian-api/v1/antar-dasha-analysis"
        )
        url_prayantar_dasha = (
            "https://astroapi-3.divineapi.com/indian-api/v1/pratyantar-dasha-analysis"
        )
        filtered_endpoints.append('vimshottari-dasha')
        filtered_endpoints.append('mahadasha-analysis')
        filtered_endpoints.append('antar-dasha-analysis')
        filtered_endpoints.append('pratyantardasha-analysis')
        # Sending API Key and other details as form-data
        payload = {
            "api_key": key,
            "full_name": details["full_name"],
            "gender": details["gender"],
            "day": details["day"],
            "month": details["month"],
            "year": details["year"],
            "place": details["place"],
            "lat": details["lat"],
            "lon": details["lon"],
            "tzone": details["tzone"],
            "hour": details["hour"],
            "min": details["min"],
            "sec": details["sec"],
            "lan": "en",
        }
        payload_dasha = {**payload, "dasha_type": "pratyantar-dasha"}
        payload_maha_dasha_analysis = {"api_key": key, "maha_dasha": "rahu"}
        payload_prayantar_dasha_analysis = {
            "api_key": key,
            "maha_dasha": "rahu",
            "antar_dasha": "moon",
            "pratyantar_dasha": "mars",
        }


        extra_urls = {
        "vimshottari-dasha": "https://astroapi-3.divineapi.com/indian-api/v1/vimshottari-dasha",
        "maha-dasha-analysis": "https://astroapi-3.divineapi.com/indian-api/v1/maha-dasha-analysis",
        "antar-dasha-analysis": "https://astroapi-3.divineapi.com/indian-api/v1/antar-dasha-analysis",
        "pratyantar-dasha-analysis": "https://astroapi-3.divineapi.com/indian-api/v1/pratyantar-dasha-analysis",
    }

        

    # Run everything
        data = asyncio.run(main(urls=urls, headers=headers, payload=payload, payload_dasha=payload_dasha, extra_urls=extra_urls ))

        kundli_api_requests_end = time.time()
        
        # if settings.LOAD_TEST_MODE:
        #     log_time_to_csv(chat_id, msg_type , msg_id, "kundli_api_requests_time", kundli_api_requests_end - kundli_api_requests_start)
        log_point_to_db(health_metric="kundli_tool_node", phase="divine_api_time", latency= kundli_api_requests_end - kundli_api_requests_start,  success= True)

        # jinja_render_start = time.time()

        # jinja_render_end = time.time()

        # log_point_to_db(health_metric="kundli_tool_node", phase="jinja_render_time", latency= jinja_render_end - jinja_render_start,  success= True)

        

        # Save the rendered HTML to a file
        # with open('output.html', 'w') as file:
        #     file.write(html_content)
       
        image_blob_name = (
            f"{user_id}_kundli.pdf"
        )
        pdf_start = time.time()

        asyncio.run(generate_mobile_friendly_kundli(data, user_id, output_path=image_blob_name))

        pdf_end = time.time()
    
        # if settings.LOAD_TEST_MODE:
        #     log_time_to_csv(chat_id, msg_type , msg_id, "kundli_pdf_generation", pdf_end - pdf_start)
        
        log_point_to_db(health_metric="kundli_tool_node", phase="html_to_pdf_time", latency= pdf_end - pdf_start,  success= True)
        db_store_start = time.time()
        asyncio.run(store_kundli_in_db(data, user_id))
        asyncio.run(store_key_value_pair_kundli_in_db(data,user_id))
        db_store_end = time.time()
    
        log_point_to_db(health_metric="kundli_tool_node", phase="store_in_db_time", latency= db_store_end - db_store_start,  success= True)
     
        file_path = f"https://astro-ai.s3.ap-south-1.amazonaws.com/{image_blob_name}"

        s3_upload_start = time.time()
        s3.upload_file(
        image_blob_name,
        "astro-ai",
        image_blob_name,
        ExtraArgs={"ACL": "public-read", "ContentType": "application/pdf"},
    )

        s3_upload_end = time.time()
       
        log_point_to_db(health_metric="kundli_tool_node", phase="store_in_db_time", latency= s3_upload_end - s3_upload_start,  success= True)
        

        # parse_and_extract_data(file_path,user_id)
        end_total = time.time()
      
        log_point_to_db(health_metric="kundli_tool_node", phase="total_time", latency=  end_total - start_total,  success= True)
        

   
       

        return langchain_agent.utils.after_kundli_node(chat_id,msg_id,msg_type)
    except Exception as e:
        logger.error(e)
        log_point_to_db(health_metric="kundli_tool_node", phase="error", latency=  0,  success= False)










async def store_kundli_in_db(data, user_id):
    """
    Stores Kundli details in the database for a given user.

    Parameters:
    - data (dict): The Kundli details to be stored.
    - user_id (int): The ID of the user whose Kundli details are to be updated.

    Returns:
    - bool: True if the operation was successful, False otherwise.

    Raises:
    - None: Exceptions are caught and handled internally.
    """
    try:
        get_user = sync_to_async(User.objects.get)
        save_user = sync_to_async(lambda user: user.save())
        
        user = await get_user(id=user_id)
        user.kundli_details = data
        await save_user(user)
        
        return True
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist.")

    except Exception as e:
        logger.error(f"An error occurred while storing Kundli details: {e}")





async def store_key_value_pair_kundli_in_db(data, user_id):
    """
    Stores individual key-value pairs from Kundli data into the corresponding
    fields of the user model.

    Parameters:
    - data (dict): A dictionary containing Kundli data where keys represent
                   user model fields and values represent their corresponding data.
                   Special handling is applied for keys 'D1' and '1' which are
                   mapped to 'horoscope_chart' and 'bhava_kundli' respectively.
                   Keys with dashes are converted to underscores.
    - user_id (int): The ID of the user whose data is to be updated.

    Returns:
    - None: The function prints success or error messages to the console.

    Notes:
    - If a key does not match any field in the user model, it will be ignored.
    - All exceptions are handled internally.
    """
    try:
        # Fetch the user from the database using user_id
        get_user = sync_to_async(User.objects.get)
        save_user = sync_to_async(lambda user: user.save())
        user = await get_user(id=user_id)

        
        # Loop through each key-value pair in the kundli data
        for key, value in data.items():
            if key=='D1':
                key='horoscope_chart'
            if key=='1':
                key='bhava_kundli'
            key = key.replace('-', '_')
            # value= json.dumps(value)
            # Dynamically set the value for the corresponding column
            if hasattr(user, key):
                setattr(user, key, value)
        
        # Save the updated user object back to the database
        await save_user(user)
        logger.info(f"Successfully stored kundli data for user {user_id}")
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")




#horoscope pdf generation






ROXY_API_KEY = os.getenv("ROXY_API")
DIVINE_API_KEY = os.getenv("DIVINE_API_KEY")
DIVINE_API_TOKEN = os.getenv("DIVINE_API_TOKEN")
    


def call_horoscope(details, user_id,category, msg_id, msg_type):
    

    """
    Calls the horoscope API with the provided details and handles the response.

    Parameters:
    - details (dict): The payload or input data required by the API.
    - user_id (str or int): The ID of the user for whom the request is being made.
    - category (str): The category or type of API being called (e.g., 'kundli', 'horoscope').

    Returns:
    - dict or None: Returns the API response as a dictionary if successful, None otherwise.

    Notes:
    - You can customize the actual API endpoint and headers inside the try block.
    """
    start_total = time.time()
    chat_id = user_id
    
 
    # today_date = datetime.today().strftime("%Y-%m-%d")
    # pdf_path=download_pdf(user_id,f'horoscope_{today_date}')
    # if pdf_path:
    #     return

  

    
    url = f"https://roxyapi.com/api/v1/data/astro/astrology/personality?token={ROXY_API_KEY}"
    payload = {
        "name": details["name"],
        "birthdate": details["dob"],
        "time_of_birth": details["time"],
    }
    print("1")
    try:
        print("zxdf")

        response = requests.post(url, json=payload)
        result={}

        if response.status_code == 200:
            print("sdf")
     
            data = response.json()
            print(data)
           
  
    
    # Assuming the response contains these fields
            name = data.get('name', 'Name not found')  # Replace 'name' with the actual key from the response
            zodiac = data.get('zodiac_sign', 'Zodiac not found') 
   
            result["data"] = {
        "name": details['name'],
        "zodiac_sign": zodiac
    }       
            print(data)
            try:
                today = datetime.today()

                if 'daily horoscope' in category:
                    url_dasha = "https://astroapi-5.divineapi.com/api/v2/daily-horoscope"
                
                
                # User birth details
                    details =   {
                                'sign': result['data']['zodiac_sign'],
                                'day': today.day,
                                'month': today.month,
                                'year': today.year,
                                'tzone': 5.5
                            }
                elif 'weekly horoscope' in category:
                    url_dasha = "https://astroapi-5.divineapi.com/api/v2/weekly-horoscope"
                
                
                # User birth details
                    details =   {
                                'sign': result['data']['zodiac_sign'],
                                'week':'current',
                                'tzone': 5.5
                            }
                
                headers = {"Authorization": f"Bearer {DIVINE_API_TOKEN}"}
                payload = {
                                "api_key": DIVINE_API_KEY,
                                **details,
                                "lan": "en",
                            }
                horoscope_divine_api_start_time=time.time()
                response = requests.post(url_dasha, headers=headers, data=payload)
                horoscope_divine_api_end_time=time.time()

                log_point_to_db(health_metric="horoscope_tool_node", phase="divine_api_time", latency=  horoscope_divine_api_end_time - horoscope_divine_api_start_time,  success= True)
                
              
                if response.status_code == 200:
                    api_response=response.json()
               
                
 
                else:
                    logger.error(f"Error: {response.status_code}, {response.text}")  # Handle error
                print(api_response)
       
        
                if 'daily horoscope' in category:
    
                    result['data']['predictions'] = api_response["data"]["prediction"]
                if 'weekly horoscope' in category:
                    result['data']['week']=api_response['data']['week']
                    result['data']['predictions'] = api_response["data"]["weekly_horoscope"]
                print(result)
              

                end_total = time.time()

                log_point_to_db(health_metric="horoscope_tool_node", phase="total_time", latency= end_total - start_total,  success= True)

                        
            except Exception as e:
                logger.error("Exception",e)
        print("sdf")
        print(result)
      
        return langchain_agent.utils.after_horoscope_node(chat_id,msg_id,msg_type,category,result)
        
    except Exception as e:
        logger.error(e)
    

    
def generate_pdf(result,image_blob_name):
    env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))
    template = env.get_template('horoscope_jinja_template.html')
    
    today = datetime.today()
    # Render the template with data
    html_content = template.render(report = result, today = today)

    # Save the rendered HTML to a file
    with open('output_horoscope.html', 'w') as file:
        file.write(html_content)
    
    asyncio.run(html_to_pdf_horoscope(html_content, image_blob_name))
