from airtable import Airtable
from config import config
import logging
from datetime import datetime
from app_setup import db

class YourModel(db.Model):
    __tablename__ = 'iterations'
    __table_args__ = {'extend_existing': True}  # Add this line
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String, nullable=False)
    iteration_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=False)
    revised_prompt = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {
            "Job ID": self.job_id,
            "Iteration Number": self.iteration_number,
            "Timestamp": self.timestamp,
            "Description": self.description,
            "Image URL": self.image_url,
            "Revised Prompt": self.revised_prompt
        }

def update_airtable(job_id, iteration_number, timestamp, description, image_url, revised_prompt):
    airtable = Airtable(config["AIRTABLE_BASE_ID"], config["AIRTABLE_TABLE_NAME"], api_key=config["AIRTABLE_API_KEY"])
    record = {
        "Job ID": job_id,
        "Iteration Number": iteration_number, 
        "Timestamp": timestamp,  # Use the passed timestamp
        "Description": description, 
        "Image URL": image_url,
        "Revised Prompt": revised_prompt
    }

    try:
        airtable.insert(record)
        logging.info(f"Airtable update successful for iteration {iteration_number} of job {job_id}")
    except Exception as e:
        logging.error(f"Failed to update Airtable for iteration {iteration_number} of job {job_id}: {e}")
        raise

def update_sqlite(job_id, iteration_number, timestamp, description, image_url, revised_prompt):
    record = YourModel(
        job_id=job_id,
        iteration_number=iteration_number,
        timestamp=timestamp,  # Use the passed timestamp
        description=description,
        image_url=image_url,
        revised_prompt=revised_prompt
    )

    try:
        db.session.add(record)
        db.session.commit()
        logging.info(f"SQLite update successful for iteration {iteration_number} of job {job_id}")
    except Exception as e:
        logging.error(f"Failed to update SQLite for iteration {iteration_number} of job {job_id}: {e}")
        db.session.rollback()
        raise
