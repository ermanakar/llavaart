from routes import app, socketio
from logger import configure_logging

if __name__ == '__main__':
    configure_logging()
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
