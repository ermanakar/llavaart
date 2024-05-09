from airtable import Airtable
from config import config
import logging
from datetime import datetime

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
        raise
