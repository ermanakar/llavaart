from flask import request, jsonify, render_template
from app_setup import app, socketio
from image_processing import process_iterations
from utils import allowed_file, generate_job_id, is_image_file
import tempfile
import logging
from werkzeug.utils import secure_filename
import os

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
