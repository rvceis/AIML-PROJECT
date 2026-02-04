# WebSocket Configuration - Ports & Files

## Server Ports

### Backend (Flask + SocketIO)
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 5000
- **File**: `textile_generator_backend/app.py` (line 92-93)
- **Protocol**: HTTP + WebSocket (Socket.IO)
- **Started**: `python app.py` or `python .\app.py`

### Frontend (Vite React)
- **Host**: localhost
- **Port**: 5173
- **File**: `textile_generator_frontend/vite.config.ts`
- **Started**: `npm run dev`
- **Accessed via**: `http://localhost:5173`

## WebSocket Connection Configuration

### Backend WebSocket Setup
**File**: `textile_generator_backend/app/websocket.py`
- Line 9: `cors_allowed_origins="*"` - Allows connections from any origin
- Line 10: `async_mode="threading"` - Uses threading for background generation
- Line 11-13: Logging and heartbeat configuration

**File**: `textile_generator_backend/app.py` (line 42)
```python
socketio.init_app(app, cors_allowed_origins="*")
```

### Frontend WebSocket Connection
**File**: `textile_generator_frontend/src/services/socketService.ts`
- Line 3: `const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'`
- Reads from `.env` file: `VITE_API_URL=http://localhost:5000`
- Uses transports: `['websocket', 'polling']`
- Connects to: `http://localhost:5000` with Socket.IO

**File**: `textile_generator_frontend/.env`
```
VITE_API_URL=http://localhost:5000
```

## WebSocket Event Flow

### Connection Sequence
1. Frontend connects to `http://localhost:5000` (Socket.IO)
2. Backend receives connection event in `websocket.py` - `handle_connect()` (line 18)
3. Backend emits `connected` event back to client
4. Frontend registers listener for `generation_update` events

### Generation Sequence
1. Frontend sends `POST /api/generate` request
2. Backend creates generation record, returns generation_id
3. Backend starts background thread for image generation
4. When generation completes, backend calls:
   ```python
   socketio.emit('generation_update', {...}, room=f'generation_{generation_id}')
   ```
   - **File**: `textile_generator_backend/app/routes/generation.py` (line 234-243)
5. Frontend WebSocket listener receives event and updates image

### Room Join Sequence
1. Frontend gets generation_id from API response
2. Frontend calls `socketService.joinGeneration(generationId)`
3. Frontend emits `join_generation` event to backend
4. Backend handler `on_join()` in `websocket.py` (line 26) joins the client to room `generation_{id}`
5. Now backend can emit to this specific room

## Key Files and Their Roles

### Backend
| File | Purpose | Port |
|------|---------|------|
| `app.py` | Flask app initialization, socketio setup | 5000 |
| `app/websocket.py` | WebSocket event handlers, room management | 5000 |
| `app/routes/generation.py` | Generation API endpoint, WebSocket emission | 5000 |
| `config.py` | Configuration (DEFAULT_STEPS=15 here) | - |

### Frontend
| File | Purpose | Port |
|------|---------|------|
| `src/services/socketService.ts` | WebSocket client initialization | 5173 |
| `src/hooks/useGenerationStatus.ts` | Listens for generation updates | 5173 |
| `src/components/Generator.tsx` | UI component, sends generation request | 5173 |
| `.env` | Environment variables (VITE_API_URL) | - |
| `vite.config.ts` | Vite configuration | - |

## Why Steps Are Still 25 (Issue)

The old backend process might still be running with cached config. 

**Solution**:
1. Kill the old Python process: `taskkill /pid <PID> /f` (from `Get-Process python`)
2. Clear Python cache: Delete `__pycache__` folders
3. Restart backend: `cd textile_generator_backend && python app.py`
4. Verify: Backend should show `DEFAULT_STEPS: 15` in logs

**Check Current Config in Running App**:
- Add debug endpoint in `generation.py` to print current config
- Or check backend logs for step count in generation log message

## Testing WebSocket

### Check Connection
1. Open DevTools (F12) → Console
2. Look for: `[SocketService] ✅ Connected to WebSocket - SID: ...`
3. If not connected, check:
   - Backend running on port 5000? `netstat -ano | findstr ":5000"`
   - VITE_API_URL set correctly? Check `.env` file
   - CORS enabled? Check `app.py` line 42

### Check Event Reception
1. Generate pattern
2. Look for: `[useGenerationStatus] 📨 Received WebSocket update`
3. Backend should log: `[WS] 🔌 Client connected`, `[WS] 🚪 joined room`, `[WS] 📤 Emitting to room`

## Summary
- **Backend**: Port 5000 (Flask + Socket.IO)
- **Frontend**: Port 5173 (Vite React)
- **WebSocket**: Connects from 5173 → 5000
- **Config File**: `config.py` (DEFAULT_STEPS=15)
- **WebSocket Handler**: `app/websocket.py`
- **Socket URL**: `http://localhost:5000`
