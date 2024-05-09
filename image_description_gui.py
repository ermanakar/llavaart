from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from airtable import Airtable
import requests, os, base64, json, tempfile, logging, magic, uuid
from datetime import datetime

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
config = {
    "ALLOWED_EXTENSIONS": {'png', 'jpg', 'jpeg'},
    "OLLAMA_API_ENDPOINT": os.getenv("OLLAMA_HOST", "default_ollama_host") + "/api/generate",
    "DALLE_API_ENDPOINT": "https://api.openai.com/v1/images/generations",
    "OLLAMA_MODEL": "llava",
    "DALLE_MODEL": "dall-e-3",
    "IMAGE_FOLDER": "static/images",
    "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID", "default_base_id"),
    "AIRTABLE_API_KEY": os.getenv("AIRTABLE_API_KEY", "default_api_key"),
    "AIRTABLE_TABLE_NAME": "iterations"
}

# Ensure IMAGE_FOLDER exists
os.makedirs(config["IMAGE_FOLDER"], exist_ok=True)

def generate_job_id():
    return str(uuid.uuid4())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config["ALLOWED_EXTENSIONS"]

def is_image_file(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    return mime_type.startswith('image/')

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

def update_airtable(job_id, iteration_number, description, image_url, revised_prompt):
    airtable = Airtable(config["AIRTABLE_BASE_ID"], config["AIRTABLE_TABLE_NAME"], api_key=config["AIRTABLE_API_KEY"])
    record = {
        "Job ID": job_id,
        "Iteration Number": iteration_number, 
        "Timestamp": datetime.utcnow().isoformat(), 
        "Description": description, 
        "Image URL": image_url,
        "Revised Prompt": revised_prompt
    }

    try:
        airtable.insert(record)
        logging.info(f"Airtable update successful for iteration {iteration_number} of job {job_id}")
    except Exception as e:
        logging.error(f"Failed to update Airtable for iteration {iteration_number} of job {job_id}: {e}")

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

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        image_file = request.files.get('image')
        if image_file and allowed_file(image_file.filename):
            iterations = int(request.form.get('iterations', 1))
            job_id = generate_job_id()  # Use generate_job_id instead of uuid.uuid4() directly
            
            try:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    # Save the uploaded image to the temporary directory
                    current_image_path = os.path.join(tmpdirname, secure_filename(image_file.filename))
                    image_file.save(current_image_path)
                    
                    if not is_image_file(current_image_path):
                        raise ValueError("Uploaded file is not a valid image.")

                    # Process iterations, passing the job_id along with other parameters
                    results = process_iterations(current_image_path, iterations, tmpdirname, job_id)
                    
                    # Return results along with the unique job_id
                    return jsonify(job_id=job_id, results=results)
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                return jsonify(error=str(e)), 500
        
        # Return an error if the file is not valid
        return jsonify(error="Invalid file or file type."), 400

    # Render the initial HTML form for GET requests
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
