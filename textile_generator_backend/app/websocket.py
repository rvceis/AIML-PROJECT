from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from app.models import Generation
import logging

logger = logging.getLogger(__name__)

# WebSocket with threading mode - supports both polling and websocket
socketio = SocketIO(
    cors_allowed_origins="*", 
    async_mode="threading",
    logger=True,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"[WS] 🔌 Client connected: {request.sid}")
    emit('connected', {'data': 'Connected to server', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"[WS] ❌ Client disconnected: {request.sid}")

@socketio.on('join_generation')
def on_join(data):
    """Join a room for generation updates"""
    generation_id = data.get('generation_id')
    room_name = f'generation_{generation_id}'
    join_room(room_name)
    emit('joined', {'generation_id': generation_id, 'room': room_name})
    logger.info(f"[WS] 🚪 Client {request.sid} joined room: {room_name}")

    try:
        if generation_id is not None:
            generation = Generation.query.get(int(generation_id))
            if generation and generation.status in ('completed', 'failed'):
                payload = {
                    'generation_id': generation.id,
                    'status': generation.status,
                    'data': {}
                }
                if generation.status == 'completed' and generation.image_path:
                    payload['data'] = {
                        'image_url': f'/api/images/{generation.image_path}',
                        'image_path': generation.image_path,
                        'prompt': generation.prompt,
                        'seed': generation.seed
                    }
                if generation.status == 'failed' and generation.error_message:
                    payload['data'] = {
                        'error': generation.error_message
                    }
                logger.info(f"[WS] 📤 Emitting cached status for generation {generation.id} to room {room_name}")
                socketio.emit('generation_update', payload, room=room_name)
    except Exception as e:
        logger.exception(f"[WS] Failed to emit cached generation status for {generation_id}: {e}")

@socketio.on('leave_generation')
def on_leave(data):
    """Leave a generation room"""
    generation_id = data.get('generation_id')
    room_name = f'generation_{generation_id}'
    leave_room(room_name)
    emit('left', {'generation_id': generation_id})
    logger.info(f"[WS] 🚪 Client {request.sid} left room: {room_name}")

def emit_generation_update(generation_id, status, data=None):
    """Emit real-time generation status update"""
    room_name = f'generation_{generation_id}'
    payload = {
        'generation_id': generation_id,
        'status': status,
        'data': data or {}
    }
    logger.info(f"[WS] 📤 Emitting to room {room_name}: status={status}, has_image={bool(data and data.get('image_url'))}")
    socketio.emit('generation_update', payload, room=room_name)
    logger.info(f"[WS] ✅ Event emitted successfully to {room_name}")

