import { useEffect, useMemo, useRef, useState } from 'react';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { ControlPanel } from './components/generator/ControlPanel';
import { Preview } from './components/generator/Preview';
import { HealthCard } from './components/HealthCard';
import { Footer } from './components/Footer';
import { HistoryPanel } from './components/HistoryPanel';
import { AuthModal } from './components/AuthModal';
import { useGenerator } from './hooks/useGenerator';
import { useTextureGANGenerator } from './hooks/useTextureGANGenerator';
import { USE_TEXTUREGAN } from './config/apiToggle';
import { useAuth } from './hooks/useAuth';
import { useGenerationStatus } from './hooks/useGenerationStatus';
import { ThemeProvider } from './context/ThemeContext';
import type { GenerationStatus, PatternId, PatternOption, StyleId } from './types';

const PATTERN_OPTIONS: Record<StyleId, PatternOption[]> = {
  bandhani: [
    { id: 'leheriya' as PatternId, name: 'Leheriya', description: 'Diagonal wave resist' },
    { id: 'mothra' as PatternId, name: 'Mothra', description: 'Small dot grid' },
    { id: 'ekdali' as PatternId, name: 'Ekdali', description: 'Single dot clusters' },
    { id: 'shikari' as PatternId, name: 'Shikari', description: 'Dense dotted fields' },
    { id: 'gharchola' as PatternId, name: 'Gharchola', description: 'Checkered bandhani grid' },
  ],
  batik: [
    { id: 'parang' as PatternId, name: 'Parang', description: 'Diagonal knife motifs' },
    { id: 'kawung' as PatternId, name: 'Kawung', description: 'Oval palm-fruit shapes' },
    { id: 'mega_mendung' as PatternId, name: 'Mega Mendung', description: 'Layered cloud forms' },
    { id: 'truntum' as PatternId, name: 'Truntum', description: 'Star-flower repeats' },
    { id: 'ceplok' as PatternId, name: 'Ceplok', description: 'Geometric medallions' },
  ],
  ikat: [
    { id: 'patola' as PatternId, name: 'Patola', description: 'Double-ikat geometrics' },
    { id: 'pochampally' as PatternId, name: 'Pochampally', description: 'Rhombus checks' },
    { id: 'telia_rumal' as PatternId, name: 'Telia Rumal', description: 'Oil-resist stripes' },
    { id: 'sambalpuri' as PatternId, name: 'Sambalpuri', description: 'Traditional ikat motifs' },
    { id: 'geringsing' as PatternId, name: 'Geringsing', description: 'Balinese double-ikat' },
  ],
};

function AppContent() {
  const generator = USE_TEXTUREGAN ? useTextureGANGenerator() : useGenerator();
  const { styles, loading, previewUrl, status, defaultStyle, generate } = generator;
  const { token, logout } = useAuth();

  const [prompt, setPrompt] = useState('intricate geometric floral pattern');
  const [style, setStyle] = useState<StyleId>('bandhani');
  const [pattern, setPattern] = useState<PatternId>('leheriya');
  const [primaryColor, setPrimaryColor] = useState('#6366F1');
  const [secondaryColor, setSecondaryColor] = useState('#EC4899');
  const [steps, setSteps] = useState(15);
  const [guidance, setGuidance] = useState(7.5);
  const [seed, setSeed] = useState<number | null>(null);
  const [generationId, setGenerationId] = useState<number | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [referenceImage, setReferenceImage] = useState<string | null>(null);
  const [imgStrength, setImgStrength] = useState(0.7);
  const promptRef = useRef<HTMLTextAreaElement | null>(null);

  const { status: wsStatus, imageUrl: wsImageUrl, error: wsError } = useGenerationStatus(
    !USE_TEXTUREGAN ? generationId : null
  );

  const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
  const wsFullImageUrl = wsImageUrl && wsImageUrl.startsWith('/api/') ? backendUrl + wsImageUrl : wsImageUrl;
  const previewImageUrl = USE_TEXTUREGAN ? previewUrl : wsFullImageUrl;

  const previewStatus: GenerationStatus | null = USE_TEXTUREGAN
    ? status
    : generationId
      ? {
          id: generationId,
          status: wsStatus as GenerationStatus['status'],
          prompt,
          style,
          color_1: primaryColor,
          color_2: secondaryColor,
          seed,
        }
      : null;

  useEffect(() => {
    if (wsError) {
      console.warn('[App] WebSocket error:', wsError);
    }
  }, [wsError]);

  useEffect(() => {
    if (defaultStyle) setStyle(defaultStyle);
  }, [defaultStyle]);

  useEffect(() => {
    const patterns = PATTERN_OPTIONS[style];
    if (patterns && patterns.length > 0) {
      setPattern(patterns[0].id);
    }
  }, [style]);

  const availablePatterns = useMemo(() => PATTERN_OPTIONS[style] || [], [style]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const activeEl = document.activeElement as HTMLElement | null;
      const isTypingTarget =
        activeEl?.tagName === 'INPUT' ||
        activeEl?.tagName === 'TEXTAREA' ||
        activeEl?.isContentEditable;

      if (e.key === 'g' && !isTypingTarget) {
        e.preventDefault();
        onGenerate();
      }
      if (e.key === '/' && !isTypingTarget) {
        e.preventDefault();
        promptRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });

  function hexToRgb(hex: string): [number, number, number] {
    const h = hex.replace('#', '');
    return [parseInt(h.substring(0, 2), 16), parseInt(h.substring(2, 4), 16), parseInt(h.substring(4, 6), 16)];
  }

  const onGenerate = async () => {
    if (USE_TEXTUREGAN) {
      console.log('[App] 🎨 Generate (TextureGAN) start');
      generate({
        prompt,
        primary_color: hexToRgb(primaryColor),
        secondary_color: hexToRgb(secondaryColor),
        seed,
        num_samples: 1,
      });
    } else {
      // Clamp steps to max 30 for SDXL/Euler
      const safeSteps = Math.min(steps, 30);
      console.log('[App] 🤖 Generate (LoRA) start');
      const result = await generate({
        prompt,
        style,
        pattern,
        color_1: primaryColor,
        color_2: secondaryColor,
        seed,
        num_inference_steps: safeSteps,
        guidance_scale: guidance,
        reference_image: referenceImage || undefined,
        strength: referenceImage ? imgStrength : undefined,
      });
      console.log('[App] ✅ Generate result:', result);
      if (result && result.id) {
        console.log('[App] 🔑 Setting generationId:', result.id);
        setGenerationId(result.id);
      } else {
        console.warn('[App] ⚠️ No generation id returned');
      }
    }
  };

  return (
    <div className="min-h-screen text-slate-900 dark:text-slate-100">
      <Header onLogin={() => setAuthOpen(true)} onLogout={logout} token={token} />
      <main className="pt-16">
        <Hero />

        <section className="py-10" id="generator">
          <div className="w-full px-4 space-y-4">
            <HealthCard />
            <div className="grid lg:grid-cols-2 gap-8 items-start">
              <ControlPanel
                prompt={prompt}
                style={style}
                pattern={pattern}
                patterns={availablePatterns}
                primaryColor={primaryColor}
                secondaryColor={secondaryColor}
                steps={steps}
                guidance={guidance}
                seed={seed}
                loading={loading}
                promptRef={promptRef}
                onPrompt={setPrompt}
                onStyle={setStyle}
                onPattern={setPattern}
                onPrimary={setPrimaryColor}
                onSecondary={setSecondaryColor}
                onSteps={setSteps}
                onGuidance={setGuidance}
                onSeed={setSeed}
                onGenerate={onGenerate}
                disableGenerate={!prompt || prompt.length < 3}
                stylesLoaded={styles.length > 0}
                referenceImage={referenceImage}
                imgStrength={imgStrength}
                onReferenceImage={setReferenceImage}
                onImgStrength={setImgStrength}
              />
              <Preview previewUrl={previewImageUrl} status={previewStatus} loading={loading} />
            </div>
            <HistoryPanel />
          </div>
        </section>

      </main>
      <Footer />
      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
