import os
import uuid
import magic
import base64
import json
import logging
from datetime import datetime
from config import config

def generate_job_id():
    """Generate a unique job ID using UUID."""
    return str(uuid.uuid4())

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config["ALLOWED_EXTENSIONS"]

def is_image_file(file_path):
    """Check if the file at the given path is an image."""
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path).startswith('image/')

def log_api_call(url, payload):
    """Log the API call details, truncating the image data for readability."""
    truncated_payload = payload.copy()
    if 'images' in truncated_payload:
        truncated_images = [image[:30] + '...' if len(image) > 30 else image for image in truncated_payload['images']]
        truncated_payload['images'] = truncated_images
    logging.info(f"Making API call to {url} with payload: {json.dumps(truncated_payload)}")

def log_api_response(response):
    """Log the API response details."""
    if response.ok:
        logging.info(f"API call successful. Response: {response.json()}")
    else:
        logging.error(f"API call failed. Status Code: {response.status_code}, Response: {response.text}")

def get_current_timestamp():
    """Generate the current timestamp."""
    return datetime.utcnow().isoformat()
