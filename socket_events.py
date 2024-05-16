from flask_socketio import emit
from app_setup import socketio

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

def emit_image_update(iteration, image_url, description):
    emit('update_image', {'iteration': iteration, 'image_url': image_url, 'description': description}, broadcast=True)

def broadcast_image_update(iteration, image_url, description):
    # Emit to all connected clients without specifying a room
    socketio.emit('update_image', {'iteration': iteration, 'image_url': image_url, 'description': description})
