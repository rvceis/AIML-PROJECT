import { useEffect, useState } from 'react';
import type { RefObject } from 'react';
import { StyleSelector } from './StyleSelector';
import { PatternSelector } from './PatternSelector';
import { ColorPicker } from './ColorPicker';
import { PromptInput } from './PromptInput';
import { AdvancedOptions } from './AdvancedOptions';
import { motion } from 'framer-motion';
import type { PatternId, PatternOption, StyleId } from '../../types';

interface Props {
  prompt: string;
  style: StyleId;
  pattern: PatternId;
  patterns: PatternOption[];
  primaryColor: string;
  secondaryColor: string;
  steps: number;
  guidance: number;
  seed: number | null;
  loading: boolean;
  promptRef: RefObject<HTMLTextAreaElement>;
  onPrompt: (v: string) => void;
  onStyle: (v: StyleId) => void;
  onPattern: (v: PatternId) => void;
  onPrimary: (v: string) => void;
  onSecondary: (v: string) => void;
  onSteps: (v: number) => void;
  onGuidance: (v: number) => void;
  onSeed: (v: number | null) => void;
  onGenerate: () => void;
  disableGenerate?: boolean;
  stylesLoaded: boolean;
  referenceImage?: string | null;
  imgStrength?: number;
  onReferenceImage?: (image: string | null) => void;
  onImgStrength?: (strength: number) => void;
}

export function ControlPanel(props: Props) {
  const {
    prompt,
    style,
    pattern,
    patterns,
    primaryColor,
    secondaryColor,
    steps,
    guidance,
    seed,
    loading,
    onPrompt,
    onStyle,
    onPattern,
    onPrimary,
    onSecondary,
    onSteps,
    onGuidance,
    onSeed,
    onGenerate,
    disableGenerate,
    stylesLoaded,
    promptRef,
    referenceImage = null,
    imgStrength = 0.7,
    onReferenceImage = () => {},
    onImgStrength = () => {},
  } = props;

  const handleReferenceImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result as string;
          onReferenceImage(base64);
        };
        reader.readAsDataURL(file);
      } catch (err) {
        console.error('Failed to load reference image', err);
      }
    }
  };

  return (
    <div className="card-surface rounded-3xl p-6 space-y-6" id="generator">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-primary-600">Generator</p>
          <h2 className="text-xl font-bold text-slate-900">Craft your textile</h2>
        </div>
        <span className="px-3 py-1 rounded-full bg-primary-50 text-primary-700 text-xs font-semibold">1024×1024 seamless</span>
      </div>

      <StyleSelector value={style} onChange={onStyle} />
      <PatternSelector value={pattern} onChange={onPattern} patterns={patterns} />
      
      {!referenceImage ? (
        <PromptInput ref={promptRef} value={prompt} onChange={onPrompt} />
      ) : (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-3">
          <p className="text-sm font-semibold text-primary-700 dark:text-primary-300">Reference Mode Active</p>
          <p className="text-xs text-primary-600 dark:text-primary-400 mt-1">Using reference image as the primary guide. Style and colors will be applied. Custom prompt is ignored in this mode.</p>
        </div>
      )}
      
      <ColorPicker primary={primaryColor} secondary={secondaryColor} onPrimaryChange={onPrimary} onSecondaryChange={onSecondary} />
      
      <div>
        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Reference Image (Optional - Enables Image-to-Image Mode)</label>
        <div className="space-y-3">
          <input
            type="file"
            accept="image/*"
            onChange={handleReferenceImageChange}
            disabled={loading}
            className="w-full p-3 border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 rounded-lg file:mr-3 file:py-1 file:px-2 file:bg-primary-500 file:text-white file:border-0 file:rounded disabled:opacity-50"
          />
          {referenceImage && (
            <div className="space-y-3 border-t border-slate-200 dark:border-slate-700 pt-3">
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 mb-1">💡 Image-to-Image Mode</p>
                <p className="text-xs text-blue-600 dark:text-blue-400">Your reference image will be transformed with selected style and colors. Adjust strength to control how much the original image influences the output.</p>
              </div>
              
              <div>
                <img src={referenceImage} alt="Reference" className="w-full h-32 object-cover rounded-lg border border-slate-200 dark:border-slate-700" />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">Strength</p>
                  <p className="text-xs font-semibold text-primary-600 dark:text-primary-400">{(imgStrength * 100).toFixed(0)}%</p>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={imgStrength}
                  onChange={(e) => onImgStrength(parseFloat(e.target.value))}
                  disabled={loading}
                  className="w-full"
                />
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  <span className="font-semibold">30-50%:</span> Keep reference structure 
                  <span className="font-semibold block mt-1">50-70%:</span> Balanced transformation
                  <span className="font-semibold block mt-1">70-100%:</span> Creative variation
                </p>
              </div>
              
              <button
                onClick={() => onReferenceImage(null)}
                disabled={loading}
                className="w-full px-3 py-2 text-sm bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg font-medium disabled:opacity-50 transition-colors"
              >
                Clear Reference Image
              </button>
            </div>
          )}
        </div>
      </div>
      
      <AdvancedOptions steps={steps} guidance={guidance} seed={seed} onStepsChange={onSteps} onGuidanceChange={onGuidance} onSeedChange={onSeed} />

      <div className="flex flex-col gap-3">
        <motion.button
          type="button"
          whileTap={{ scale: 0.98 }}
          disabled={loading || disableGenerate || !stylesLoaded}
          onClick={onGenerate}
          className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary-500 to-secondary-500 text-white font-semibold py-3 shadow-lg shadow-primary-500/30 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? 'Generating...' : 'Generate pattern'}
        </motion.button>
        <p className="text-xs text-slate-500">Generation takes ~30-60s on first run as the model warms up.</p>
      </div>
    </div>
  );
}
