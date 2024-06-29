from app_setup import db

class Iteration(db.Model):
    
    __tablename__ = 'iterations'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(80), nullable=False)
    iteration_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    revised_prompt = db.Column(db.String(500), nullable=False)

