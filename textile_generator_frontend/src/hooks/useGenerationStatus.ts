import { useEffect, useState } from 'react';
import { socketService } from '../services/socketService';

export function useGenerationStatus(generationId: number | null) {
  const [status, setStatus] = useState<'pending' | 'processing' | 'completed' | 'failed'>('pending');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[useGenerationStatus] 🔍 Hook triggered with generationId:', generationId);
    
    if (!generationId) {
      console.warn('[useGenerationStatus] ⚠️ generationId is null/undefined, skipping');
      return;
    }

    console.log('[useGenerationStatus] 🎬 Initializing for generation:', generationId);
    setStatus('processing');
    setImageUrl(null);
    setError(null);

    // Connect to WebSocket
    console.log('[useGenerationStatus] 🔌 Connecting to WebSocket...');
    socketService.connect();

    // Wait a bit for connection, then join the room
    const joinTimer = setTimeout(() => {
      console.log('[useGenerationStatus] ⏱️ Joining generation room (after 200ms delay):', generationId);
      socketService.joinGeneration(generationId);
    }, 200);

    // Listen for WebSocket updates
    const handleUpdate = (data: any) => {
      console.log('[useGenerationStatus] 📨 Received event from socketService:', JSON.stringify(data, null, 2));
      
      if (!data || typeof data !== 'object') {
        console.warn('[useGenerationStatus] ⚠️ Invalid data received:', data);
        return;
      }

      console.log('[useGenerationStatus] 🔎 Checking: event.generation_id (', data.generation_id, ') vs our generationId (', generationId, ')');
      
      if (data.generation_id === generationId) {
        console.log(`[useGenerationStatus] ✅ ID MATCH! Status: ${data.status}`);
        setStatus(data.status || 'pending');
        
        if (data.data?.image_url) {
          console.log('[useGenerationStatus] 🖼️ Image URL found:', data.data.image_url);
          setImageUrl(data.data.image_url);
        } else {
          console.warn('[useGenerationStatus] ⚠️ No image_url in data');
        }
        
        if (data.data?.error) {
          console.error('[useGenerationStatus] ❌ Error from server:', data.data.error);
          setError(data.data.error);
        }
      } else {
        console.warn(`[useGenerationStatus] ❌ ID MISMATCH: ${data.generation_id} !== ${generationId}`);
      }
    };

    console.log('[useGenerationStatus] 👂 Registering listener for "generation_update"');
    socketService.on('generation_update', handleUpdate);

    return () => {
      console.log('[useGenerationStatus] 🧹 Cleanup for generation:', generationId);
      clearTimeout(joinTimer);
      socketService.leaveGeneration(generationId);
    };
  }, [generationId]);

  return { status, imageUrl, error };
}
