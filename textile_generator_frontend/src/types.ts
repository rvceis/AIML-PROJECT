export type StyleId = 'bandhani' | 'ikat' | 'block_print' | 'paisley';

export interface StyleOption {
  id: StyleId;
  name: string;
  icon: string;
  description: string;
}

export interface GenerationRequest {
  prompt: string;
  style: StyleId;
  color_1?: string | null;
  color_2?: string | null;
  seed?: number | null;
  num_inference_steps?: number;
  guidance_scale?: number;
  reference_image?: string | null;
}

export interface GenerationStatus {
  id: number;
  status: 'processing' | 'completed' | 'failed';
  prompt: string;
  style: StyleId;
  color_1?: string | null;
  color_2?: string | null;
  seed?: number | null;
  image_url?: string | null;
  error_message?: string | null;
  created_at?: string;
  completed_at?: string | null;
  user_id?: number | null;
}

export interface ApiHealth {
  status: string;
  model_loaded?: boolean;
  database?: string;
}
