import requests
import json
import logging
from config import config
from utils import log_api_call, log_api_response, get_current_timestamp
from socket_events import broadcast_image_update
import os
import uuid
import base64
from google.cloud import storage
from airtable_integration import update_airtable, update_sqlite
from datetime import datetime

def get_image_description(image_path):
    with open(image_path, 'rb') as img:
        img_base64 = base64.b64encode(img.read()).decode('utf-8')

    payload = {
        "model": config["OLLAMA_MODEL"],
        "prompt": "Describe this image with as much detail as possible, be specific in the style, emotion and activity in the image",
        "images": [img_base64]
    }
    log_api_call(config["OLLAMA_API_ENDPOINT"], payload)

    try:
        response = requests.post(config["OLLAMA_API_ENDPOINT"], json=payload, headers={'Content-Type': 'application/json'}, stream=True)
        response.raise_for_status()

        description = ""
        for line in response.iter_lines():
            if line:
                json_response = json.loads(line.decode('utf-8'))
                description += json_response.get('response', '')
                if json_response.get('done', False):
                    break
        return description.strip()
    except (requests.RequestException, json.JSONDecodeError) as e:
        logging.error(f"Error getting image description: {e}")
        return None

def generate_image(description):
    # Statement for Ukiyo-e styleisation
    ukiyoe_prompt = f"Create the following description of the image in Ukiyo-e style: {description}"
    payload = {"prompt": ukiyoe_prompt, "n": 1, "size": "1024x1024", "model": config["DALLE_MODEL"]}
    headers = {'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'}

    log_api_call(config["DALLE_API_ENDPOINT"], payload)

    try:
        response = requests.post(config["DALLE_API_ENDPOINT"], json=payload, headers=headers)
        log_api_response(response)
        response.raise_for_status()
        image_data = response.json()

        revised_prompt = image_data['data'][0].get('revised_prompt', '')
        image_url = image_data['data'][0].get('url', '')

        return revised_prompt, image_url
    except requests.RequestException as e:
        logging.error(f"Error generating image: {e}")
        return None, None

def save_image_from_url(image_url, local_path):
    logging.info(f"Attempting to download image from URL: {image_url}")
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as img_file:
                for chunk in response.iter_content(chunk_size=8192):
                    img_file.write(chunk)
            logging.info(f"Image successfully saved to {local_path}")
            return local_path
        else:
            logging.error(f"Failed to download image. HTTP status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Error downloading image from {image_url}: {e}")
        return None

def upload_to_gcs(local_path, bucket_name, destination_blob_name):
    try:
        storage_client = storage.Client.from_service_account_json('/Users/ermanakar/Desktop/llava/gpu-ollama-f3403e182055.json')
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_path)
        gcs_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        logging.info(f"Image successfully uploaded to {gcs_url}")
        return gcs_url
    except Exception as e:
        logging.error(f"Error uploading image to GCS: {e}")
        return None

def process_iterations(current_image_path, iterations, tmpdirname, job_id):
    results = []
    for i in range(iterations):
        description = get_image_description(current_image_path)
        if not description:
            logging.error(f"No description generated for iteration {i+1}")
            continue

        revised_prompt, image_url = generate_image(description)
        if not revised_prompt or not image_url:
            logging.error(f"Image generation failed for iteration {i+1}")
            continue

        local_image_path = os.path.join(tmpdirname, f"{uuid.uuid4().hex}.jpg")
        if not save_image_from_url(image_url, local_image_path):
            logging.error(f"Failed to save image for iteration {i+1}")
            continue

        gcs_url = upload_to_gcs(local_image_path, 'llavaimages', f"images/{uuid.uuid4().hex}.jpg")
        if not gcs_url:
            logging.error(f"Failed to upload image to GCS for iteration {i+1}")
            continue

        timestamp = get_current_timestamp()  # Generate the timestamp once

        result = {
            "iteration_number": i + 1,
            "description": description,
            "image_url": gcs_url,
            "revised_prompt": revised_prompt,
            "timestamp": timestamp  # Add the timestamp to the result
        }
        
        results.append(result)
        
        update_sqlite(
            job_id=job_id,
            iteration_number=result['iteration_number'],
            timestamp=timestamp,  # Pass the timestamp here
            description=result['description'],
            image_url=result['image_url'],
            revised_prompt=result['revised_prompt']
        )

        update_airtable(
            job_id=job_id,
            iteration_number=result['iteration_number'],
            timestamp=timestamp,  # Pass the same timestamp here
            description=result['description'],
            image_url=result['image_url'],
            revised_prompt=result['revised_prompt']
        )

        broadcast_image_update(i + 1, gcs_url, description)

        if i < iterations - 1:
            current_image_path = local_image_path

    return results