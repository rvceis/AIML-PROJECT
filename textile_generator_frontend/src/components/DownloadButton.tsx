import { ArrowDownTrayIcon, ChevronDownIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import { useState } from 'react';

interface DownloadButtonProps {
  imageUrl: string;
  filename: string;
}

export function DownloadButton({ imageUrl, filename }: DownloadButtonProps) {
  const [showDropdown, setShowDropdown] = useState(false);

  const handleDownload = async (format: 'png' | 'tiff') => {
    try {
      setShowDropdown(false);
      let downloadUrl = imageUrl;
      let downloadFilename = filename;

      if (format === 'tiff') {
        // Request TIFF conversion from backend
        const imagePath = imageUrl.split('/api/images/')[1];
        downloadUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/images/${imagePath}/download?format=tiff`;
        downloadFilename = filename.replace('.png', '.tiff');
      }

      const response = await fetch(downloadUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = downloadFilename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(`Downloaded as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Download failed');
    }
  };

  return (
    <div className="relative">
      <div className="flex">
        <button
          onClick={() => handleDownload('png')}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-l-lg text-sm font-medium hover:bg-slate-300 dark:hover:bg-slate-600 transition-all"
        >
          <ArrowDownTrayIcon className="w-4 h-4" />
          Download
        </button>
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="px-2 py-1.5 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-r-lg text-sm border-l border-slate-300 dark:border-slate-600 hover:bg-slate-300 dark:hover:bg-slate-600 transition-all"
        >
          <ChevronDownIcon className="w-3 h-3" />
        </button>
      </div>
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-32 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50">
          <button
            onClick={() => handleDownload('png')}
            className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-t-lg"
          >
            PNG
          </button>
          <button
            onClick={() => handleDownload('tiff')}
            className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-b-lg border-t border-slate-200 dark:border-slate-700"
          >
            TIFF (High Quality)
          </button>
        </div>
      )}
    </div>
  );
}
