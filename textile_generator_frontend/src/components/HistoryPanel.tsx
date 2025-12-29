import { useEffect, useState } from 'react';
import { getHistory } from '../services/api';
import type { GenerationStatus } from '../types';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';

export function HistoryPanel() {
  const { token } = useAuth();
  const [items, setItems] = useState<GenerationStatus[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load history regardless of auth status (guests can see all generations)
    setLoading(true);
    getHistory(10, 0)
      .then(setItems)
      .catch(() => toast.error('Unable to load history'))
      .finally(() => setLoading(false));
  }, [token]); // Reload when auth changes

  return (
    <div className="card-surface rounded-2xl p-5 text-sm text-slate-700 space-y-4" id="history">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-primary-600">History</p>
          <p className="text-lg font-bold text-slate-900 dark:text-slate-100">Recent generations</p>
        </div>
        <span className="text-xs text-slate-500">Last 10</span>
      </div>
      {loading && <p className="text-slate-500">Loading...</p>}
      {!loading && items.length === 0 && <p className="text-slate-500">No items yet.</p>}
      <div className="space-y-3">
        {items.map((item) => (
          <motion.div key={item.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between rounded-xl border border-slate-200 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 px-3 py-2">
            <div>
              <p className="font-semibold text-slate-900 dark:text-slate-100">{item.prompt}</p>
              <p className="text-xs text-slate-500">{item.style} · {item.status}</p>
            </div>
            {item.image_url && (
              <a
                href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${item.image_url}`}
                target="_blank"
                rel="noreferrer"
                className="text-primary-600 dark:text-primary-400 text-xs font-semibold hover:underline"
              >
                View
              </a>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
