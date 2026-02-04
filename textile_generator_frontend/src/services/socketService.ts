import io, { Socket } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

console.log('[SocketService] 📍 Initializing with URL:', SOCKET_URL);

class SocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Function[]> = new Map();
  private isConnecting: boolean = false;

  connect() {
    if (this.socket?.connected) {
      console.log('[SocketService] ✅ Already connected');
      return;
    }

    if (this.isConnecting) {
      console.log('[SocketService] ⏳ Connection already in progress');
      return;
    }
    
    this.isConnecting = true;
    console.log('[SocketService] 🔌 Attempting connection to:', SOCKET_URL);
    console.log('[SocketService] 🌐 Using transports: websocket, polling');
    
    try {
      this.socket = io(SOCKET_URL, {
        transports: ['websocket', 'polling'],
        reconnectionDelay: 1000,
        reconnection: true,
        reconnectionAttempts: 10,
        timeout: 20000,
        reconnectionDelayMax: 5000,
      });

      this.socket.on('connect', () => {
        console.log('[SocketService] ✅ Connected to WebSocket - SID:', this.socket?.id);
        console.log('[SocketService] 📡 Transport:', this.socket?.io.engine.transport.name);
        this.isConnecting = false;
      });

      this.socket.on('connected', (data: any) => {
        console.log('[SocketService] 📬 Received connected event:', data);
      });

      this.socket.on('joined', (data: any) => {
        console.log('[SocketService] 🚪 Received joined event:', data);
      });

      this.socket.on('generation_update', (data: any) => {
        console.log('[SocketService] 🔔 Received generation_update event:', JSON.stringify(data, null, 2));
        this.emit('generation_update', data);
      });

      this.socket.on('disconnect', () => {
        console.log('[SocketService] ❌ Disconnected from WebSocket');
        this.isConnecting = false;
      });

      this.socket.on('connect_error', (error: any) => {
        console.error('[SocketService] ⚠️ Connection error:', error);
        this.isConnecting = false;
      });

      this.socket.on('error', (error: any) => {
        console.error('[SocketService] ❌ Socket error:', error);
      });

      console.log('[SocketService] ✅ Socket.IO client initialized');
    } catch (err) {
      console.error('[SocketService] ❌ Failed to initialize Socket.IO:', err);
      this.isConnecting = false;
    }
  }

  disconnect() {
    if (this.socket) {
      console.log('[SocketService] 🔌 Disconnecting socket');
      this.socket.disconnect();
      this.socket = null;
    }
  }

  joinGeneration(generationId: number) {
    if (!this.socket) {
      console.warn('[SocketService] ⚠️ Socket not initialized, initializing now');
      this.connect();
    }

    if (!this.socket?.connected) {
      console.warn('[SocketService] ⏳ Socket not connected yet (state:', this.socket?.disconnected ? 'disconnected' : 'connecting', '), retrying...');
      // Retry after a short delay
      setTimeout(() => {
        if (this.socket?.connected) {
          console.log('[SocketService] ✅ Socket now connected, joining room:', generationId);
          this.socket?.emit('join_generation', { generation_id: generationId });
        } else {
          console.warn('[SocketService] ⚠️ Socket still not connected after waiting. Current state:', {
            connected: this.socket?.connected,
            disconnected: this.socket?.disconnected,
            id: this.socket?.id
          });
        }
      }, 500);
      return;
    }
    
    console.log('[SocketService] 🚪 Joining generation room:', generationId, '(Socket ID:', this.socket.id, ')');
    this.socket.emit('join_generation', { generation_id: generationId });
  }

  leaveGeneration(generationId: number) {
    if (this.socket?.connected) {
      console.log('[SocketService] 🚪 Leaving generation room:', generationId);
      this.socket.emit('leave_generation', { generation_id: generationId });
    }
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
    console.log(`[SocketService] 👂 Registered listener for "${event}". Total listeners: ${this.listeners.get(event)?.length}`);
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event) || [];
    console.log(`[SocketService] 📢 Emitting "${event}" to ${callbacks.length} listener(s)`);
    callbacks.forEach((cb, index) => {
      try {
        console.log(`[SocketService] ↪️  Calling listener ${index + 1}/${callbacks.length}`);
        cb(data);
      } catch (err) {
        console.error(`[SocketService] ❌ Error in listener ${index + 1}:`, err);
      }
    });
  }
}

export const socketService = new SocketService();
