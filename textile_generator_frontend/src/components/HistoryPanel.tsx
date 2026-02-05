import { useEffect, useState } from 'react';
import { getGallery } from '../services/api';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

interface GalleryImage {
  filename: string;
  url: string;
  created_at: string;
  size_bytes: number;
}

export function HistoryPanel() {
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<GalleryImage | null>(null);
  const [loadedCount, setLoadedCount] = useState(50);

  const loadGallery = () => {
    setLoading(true);
    getGallery(loadedCount, 0)
      .then(setImages)
      .catch(() => toast.error('Unable to load gallery'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadGallery();
  }, [loadedCount]);

  const getBackendUrl = () => import.meta.env.VITE_API_URL || 'http://localhost:5000';

  return (
    <div className="card-surface rounded-2xl p-5 space-y-4" id="history">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-primary-600">Gallery</p>
          <p className="text-lg font-bold text-slate-900">Generated patterns</p>
        </div>
        <span className="text-xs text-slate-500">{images.length} total</span>
      </div>

      {loading && !images.length && (
        <div className="flex justify-center py-8">
          <div className="text-slate-500">Loading gallery...</div>
        </div>
      )}

      {!loading && images.length === 0 && (
        <div className="flex justify-center py-12">
          <p className="text-slate-500">No generated images yet.</p>
        </div>
      )}

      {/* Gallery Grid */}
      {images.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {images.map((image, idx) => (
            <motion.div
              key={image.filename}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => setSelectedImage(image)}
              className="group relative aspect-square cursor-pointer overflow-hidden rounded-xl border border-slate-200 bg-slate-100 hover:border-primary-400 transition-all"
            >
              <img
                src={`${getBackendUrl()}${image.url}`}
                alt={image.filename}
                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-200"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200 flex items-center justify-center">
                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Load More Button */}
      {images.length > 0 && images.length < 200 && (
        <div className="flex justify-center pt-4">
          <button
            onClick={() => setLoadedCount(prev => prev + 50)}
            disabled={loading}
            className="px-6 py-2 text-sm font-semibold text-primary-600 border border-primary-300 rounded-lg hover:bg-primary-50 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}

      {/* Image Preview Modal */}
      {selectedImage && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setSelectedImage(null)}
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white dark:bg-slate-900 rounded-xl overflow-hidden max-w-2xl w-full max-h-[80vh]"
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="font-semibold text-slate-900 dark:text-white truncate">{selectedImage.filename}</h3>
              <button
                onClick={() => setSelectedImage(null)}
                className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4 flex flex-col gap-4">
              <img
                src={`${getBackendUrl()}${selectedImage.url}`}
                alt={selectedImage.filename}
                className="w-full h-auto rounded-lg"
              />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500 dark:text-slate-400">File</p>
                  <p className="font-semibold text-slate-900 dark:text-white truncate">{selectedImage.filename}</p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Size</p>
                  <p className="font-semibold text-slate-900 dark:text-white">{(selectedImage.size_bytes / 1024).toFixed(1)} KB</p>
                </div>
                <div className="col-span-2">
                  <p className="text-slate-500 dark:text-slate-400">Created</p>
                  <p className="font-semibold text-slate-900 dark:text-white">{new Date(selectedImage.created_at).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex gap-3">
                <a
                  href={`${getBackendUrl()}${selectedImage.url}`}
                  download={selectedImage.filename}
                  className="flex-1 px-4 py-2 text-center bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-semibold"
                >
                  Download
                </a>
                <a
                  href={`${getBackendUrl()}${selectedImage.url}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 px-4 py-2 text-center border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors font-semibold"
                >
                  Open in New Tab
                </a>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
