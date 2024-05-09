import requests, json, logging
from config import config
from utils import log_api_call, log_api_response
from socket_events import emit
import os, uuid, base64, json, logging
from airtable_integration import update_airtable

def get_image_description(image_path):
    with open(image_path, 'rb') as img:
        img_base64 = base64.b64encode(img.read()).decode('utf-8')

    payload = {"model": config["OLLAMA_MODEL"], "prompt": "Describe this image with as much detail as possible, be specific in the style, emotion and activity in the image", "images": [img_base64]}
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
    payload = {"prompt": description, "n": 1, "size": "1024x1024", "model": config["DALLE_MODEL"]}
    headers = {'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'}

    log_api_call(config["DALLE_API_ENDPOINT"], payload)

    try:
        response = requests.post(config["DALLE_API_ENDPOINT"], json=payload, headers=headers)
        log_api_response(response)
        response.raise_for_status()
        image_data = response.json()

        # Extract the revised prompt and image URL from the response
        revised_prompt = image_data['data'][0].get('revised_prompt', '')
        image_url = image_data['data'][0].get('url', '')

        # Return both the revised_prompt and the image_url
        return revised_prompt, image_url
    except requests.RequestException as e:
        logging.error(f"Error generating image: {e}")
        # Return None for both revised_prompt and image_url in case of an error
        return None, None

def save_image_from_url(image_url, tmpdirname):
    logging.info(f"Attempting to download image from URL: {image_url}")
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            tmp_file_path = os.path.join(tmpdirname, uuid.uuid4().hex + ".jpg")
            with open(tmp_file_path, 'wb') as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
            logging.info(f"Image successfully saved to {tmp_file_path}")
            return tmp_file_path
        else:
            logging.error(f"Failed to download image. HTTP status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Error downloading image from {image_url}: {e}")
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

        results.append({"iteration": i + 1, "description": description, "image_url": image_url})
        update_airtable(job_id, i + 1, description, image_url, revised_prompt)

        # Emit update to connected clients
        emit('update_image', {'iteration': i + 1, 'image_url': image_url, 'description': description}, broadcast=True)

        if i < iterations - 1:
            new_image_path = save_image_from_url(image_url, tmpdirname)
            if new_image_path:
                current_image_path = new_image_path
            else:
                logging.error(f"Failed to save new image for next iteration {i+2}")
                break

    return results
