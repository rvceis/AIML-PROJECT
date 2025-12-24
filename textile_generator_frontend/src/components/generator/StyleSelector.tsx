import clsx from 'clsx';
import type { StyleId } from '../../types';

const styles: { id: StyleId; name: string; icon: string; description: string }[] = [
  { id: 'bandhani', name: 'Bandhani', icon: '🎯', description: 'Tie-dye circular motifs' },
  { id: 'ikat', name: 'Ikat', icon: '⚡', description: 'Blurred resist dye' },
  { id: 'block_print', name: 'Block Print', icon: '📐', description: 'Stamped repeats' },
  { id: 'paisley', name: 'Paisley', icon: '🌀', description: 'Classic teardrops' },
];

interface Props {
  value: StyleId;
  onChange: (style: StyleId) => void;
}

export function StyleSelector({ value, onChange }: Props) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-700">Style</p>
        <p className="text-xs text-slate-500">Pick one</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {styles.map((style) => {
          const active = value === style.id;
          return (
            <button
              key={style.id}
              type="button"
              onClick={() => onChange(style.id)}
              className={clsx(
                'w-full text-left rounded-xl border px-4 py-3 transition-all',
                'shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary-500',
                active
                  ? 'border-primary-200 bg-primary-50 text-primary-700'
                  : 'border-slate-200 bg-white text-slate-700',
              )}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">{style.icon}</span>
                <div>
                  <p className="text-sm font-semibold">{style.name}</p>
                  <p className="text-xs text-slate-500">{style.description}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
