import { useCallback, useEffect, useMemo, useState } from 'react';
import { getGenerationStatus, getStyles, startGeneration } from '../services/api';
import { startTextureGANGeneration } from '../services/api.texturegan';
import { USE_TEXTUREGAN } from '../config/apiToggle';
import { socketService } from '../services/socketService';
import type { GenerationRequest, GenerationStatus, StyleOption } from '../types';
import toast from 'react-hot-toast';

interface GeneratorState {
  styles: StyleOption[];
  loading: boolean;
  pendingId: number | null;
  previewUrl: string | null;
  status: GenerationStatus | null;
}

export function useGenerator() {
  const [state, setState] = useState<GeneratorState>({
    styles: [],
    loading: false,
    pendingId: null,
    previewUrl: null,
    status: null,
  });

  useEffect(() => {
    getStyles()
      .then((styles) => setState((prev) => ({ ...prev, styles })))
      .catch(() => toast.error('Unable to load styles'));
    
    // Connect WebSocket for real-time updates (for default SDXL backend)
    if (!USE_TEXTUREGAN) {
      socketService.connect();
      return () => { socketService.disconnect(); };
    }
    return () => {};
  }, []);

  // Listen for WebSocket updates when using default backend
  useEffect(() => {
    if (!state.pendingId || USE_TEXTUREGAN) return;

    const handleUpdate = (data: any) => {
      console.log('[WebSocket] Received generation_update:', data);
      if (data.generation_id === state.pendingId) {
        if (data.status === 'completed' && data.data?.image_url) {
          // Prepend base URL if it's a relative path
          const imageUrl = data.data.image_url.startsWith('http') 
            ? data.data.image_url 
            : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${data.data.image_url}`;
          
          setState((prev) => ({
            ...prev,
            previewUrl: imageUrl,
            loading: false,
            status: { ...prev.status, status: 'completed' } as GenerationStatus
          }));
          toast.success('Pattern ready!');
        } else if (data.status === 'failed') {
          setState((prev) => ({ ...prev, loading: false }));
          toast.error(data.data?.error || 'Generation failed');
        }
      }
    };

    console.log('[WebSocket] Setting up listener for generation:', state.pendingId);
    socketService.on('generation_update', handleUpdate);
    socketService.joinGeneration(state.pendingId);

    return () => {
      if (state.pendingId) {
        socketService.leaveGeneration(state.pendingId);
      }
    };
  }, [state.pendingId]);

  // Use direct HTTP or WebSocket based on backend
  const generate = useCallback(async (payload: GenerationRequest) => {
    setState((prev) => ({ ...prev, loading: true, previewUrl: null }));
    try {
      let result: any;
      if (USE_TEXTUREGAN) {
        result = await startTextureGANGeneration(payload);
        if (result.results && result.results[0]?.image_base64) {
          setState((prev) => ({
            ...prev,
            previewUrl: `data:image/png;base64,${result.results[0].image_base64}`,
            loading: false,
            status: { ...prev.status, status: 'completed' } as GenerationStatus
          }));
          toast.success('Pattern ready');
        } else {
          throw new Error('No image returned');
        }
        return result;
      } else {
        // For SDXL/LoRA, start generation and track via WebSocket
        result = await startGeneration(payload);
        console.log('[API] Generation started:', result);
        setState((prev) => ({ 
          ...prev, 
          pendingId: result.id,
          status: result,
          loading: true  // Keep loading until WebSocket update
        }));
        toast.loading('Generating pattern...', { duration: 2000 });
        
        // Fallback: If no WebSocket update after 5 minutes, reset loading
        setTimeout(() => {
          setState((prev) => {
            if (prev.loading && prev.pendingId === result.id) {
              console.warn('[Timeout] No WebSocket update received, resetting loading state');
              return { ...prev, loading: false };
            }
            return prev;
          });
        }, 300000); // 5 minutes
        
        return result;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Generation failed';
      toast.error(message);
      setState((prev) => ({ ...prev, loading: false }));
      return null;
    }
  }, []);

  const defaultStyle = useMemo(() => state.styles[0]?.id || 'bandhani', [state.styles]);

  return {
    ...state,
    defaultStyle,
    generate,
  };
}
