import os

config = {
    "ALLOWED_EXTENSIONS": {'png', 'jpg', 'jpeg'},
    "OLLAMA_API_ENDPOINT": os.getenv("OLLAMA_HOST", "default_ollama_host") + "/api/generate",
    "DALLE_API_ENDPOINT": "https://api.openai.com/v1/images/generations",
    "OLLAMA_MODEL": "llava",
    "DALLE_MODEL": "dall-e-3",
    "IMAGE_FOLDER": "static/images",
    "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID", "default_base_id"),
    "AIRTABLE_API_KEY": os.getenv("AIRTABLE_API_KEY", "default_api_key"),
    "AIRTABLE_TABLE_NAME": "iterations",
    "SQLALCHEMY_DATABASE_URI": f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")}',
    "SQLALCHEMY_TRACK_MODIFICATIONS": False
}
