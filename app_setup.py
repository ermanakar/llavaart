from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Enable CORS for the Flask app
CORS(app, origins=["http://localhost:3000"])

# Initialize SocketIO with CORS allowed origins
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = config["SQLALCHEMY_DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config["SQLALCHEMY_TRACK_MODIFICATIONS"]

db = SQLAlchemy(app)

# Import models here to register them
from models import Iteration

# Ensure tables are created within an application context
with app.app_context():
    db.create_all()

# Import your routes after creating the app and initializing extensions
import routes
