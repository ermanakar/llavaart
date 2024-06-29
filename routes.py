from flask import request, jsonify, render_template
from app_setup import app, socketio, db
from image_processing import process_iterations
from utils import allowed_file, generate_job_id, is_image_file
import tempfile
import logging
from werkzeug.utils import secure_filename
import os
from models import Iteration
from socket_events import broadcast_image_update

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        image_file = request.files.get('image')
        if image_file and allowed_file(image_file.filename):
            iterations = int(request.form.get('iterations', 1))
            job_id = generate_job_id()

            try:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    current_image_path = os.path.join(tmpdirname, secure_filename(image_file.filename))
                    image_file.save(current_image_path)

                    if not is_image_file(current_image_path):
                        raise ValueError("Uploaded file is not a valid image.")

                    results = process_iterations(current_image_path, iterations, tmpdirname, job_id)

                    logging.info(f"Results: {results}")

                    for result in results:
                        logging.info(f"Processing result: {result}")
                        existing_iteration = Iteration.query.filter_by(
                            job_id=job_id,
                            iteration_number=result['iteration_number'],
                            image_url=result['image_url']
                        ).first()
                        if existing_iteration is None:
                            new_iteration = Iteration(
                                job_id=job_id,
                                iteration_number=result['iteration_number'],
                                description=result['description'],
                                image_url=result['image_url'],
                                revised_prompt=result['revised_prompt'],
                                timestamp=result['timestamp']
                            )
                            db.session.add(new_iteration)
                            db.session.commit()

                            # Broadcast the update
                            broadcast_image_update(
                                result['iteration_number'],
                                result['image_url'],
                                result['description']
                            )

                    return jsonify(job_id=job_id, results=results)
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                return jsonify(error=str(e)), 500

        return jsonify(error="Invalid file or file type."), 400

    return render_template('index.html')

@app.route('/api/images', methods=['GET'])
def get_images():
    try:
        logging.info("Fetching images from database")
        images = Iteration.query.order_by(Iteration.timestamp).all()
        image_list = [
            {
                "iteration_number": image.iteration_number,
                "image_url": image.image_url,
                "description": image.description,
                "revised_prompt": image.revised_prompt,
                "timestamp": image.timestamp
            }
            for image in images
        ]
        logging.info(f"Fetched {len(image_list)} images")
        return jsonify(image_list)
    except Exception as e:
        logging.error(f"Error fetching images: {e}")
        return jsonify({"error": str(e)}), 500
