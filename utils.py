import os, uuid, magic, base64, json, logging
from config import config  # Make sure config is available in this scope

def generate_job_id():
    return str(uuid.uuid4())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config["ALLOWED_EXTENSIONS"]

def is_image_file(file_path):
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path).startswith('image/')

def log_api_call(url, payload):
    truncated_payload = payload.copy()
    if 'images' in truncated_payload:
        truncated_images = [image[:30] + '...' if len(image) > 30 else image for image in truncated_payload['images']]
        truncated_payload['images'] = truncated_images
    logging.info(f"Making API call to {url} with payload: {json.dumps(truncated_payload)}")

def log_api_response(response):
    if response.ok:
        logging.info(f"API call successful. Response: {response.json()}")
    else:
        logging.error(f"API call failed. Status Code: {response.status_code}, Response: {response.text}")
