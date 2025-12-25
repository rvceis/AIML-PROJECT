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
      if (data.generation_id === state.pendingId) {
        if (data.status === 'completed' && data.data?.image_url) {
          setState((prev) => ({
            ...prev,
            previewUrl: data.data.image_url,
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
        setState((prev) => ({ 
          ...prev, 
          pendingId: result.id,
          status: result
        }));
        toast.info('Generating pattern...');
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
