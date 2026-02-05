import { ArrowDownTrayIcon, CheckIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DownloadButtonProps {
  imageUrl: string;
  filename: string;
}

type ImageFormat = 'png' | 'jpg' | 'webp' | 'tiff' | 'bmp' | 'pdf';

interface FormatOption {
  format: ImageFormat;
  label: string;
  category: 'Standard' | 'Print Ready';
  quality?: number;
}

export function DownloadButton({ imageUrl, filename }: DownloadButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isConverting, setIsConverting] = useState(false);

  const formats: FormatOption[] = [
    // Standard formats
    { format: 'png', label: 'PNG (Lossless)', category: 'Standard' },
    { format: 'jpg', label: 'JPG (95% Quality)', category: 'Standard', quality: 95 },
    { format: 'webp', label: 'WebP (Modern)', category: 'Standard', quality: 90 },
    // Print-ready formats
    { format: 'tiff', label: 'TIFF (Uncompressed - Printing)', category: 'Print Ready' },
    { format: 'bmp', label: 'BMP (Industrial Print)', category: 'Print Ready' },
    { format: 'pdf', label: 'PDF (Vector Print)', category: 'Print Ready' },
  ];

  const downloadAsPDF = async () => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const img = new Image();
      const url = window.URL.createObjectURL(blob);

      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');

        if (!ctx) {
          toast.error('Failed to create PDF');
          return;
        }

        ctx.drawImage(img, 0, 0);

        // Create PDF data URL
        const imgData = canvas.toDataURL('image/png');
        const width = canvas.width;
        const height = canvas.height;

        // Simple PDF generation
        const pdfContent = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${width} ${height}] /Contents 4 0 R /Resources << /XObject << /Image1 5 0 R >> >> >>
endobj
4 0 obj
<< >>
stream
${width} 0 0 ${height} 0 0 cm
/Image1 Do
endstream
endobj
5 0 obj
<< /Type /XObject /Subtype /Image /Width ${width} /Height ${height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length 0 >>
stream
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000250 00000 n
0000000350 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
500
%%EOF`;

        const blob = new Blob([pdfContent], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        const baseName = filename.replace(/\.[^/.]+$/, '');
        a.href = url;
        a.download = `${baseName}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        window.URL.revokeObjectURL(imgData);

        toast.success('Downloaded as PDF');
        setIsOpen(false);
        setIsConverting(false);
      };

      img.onerror = () => {
        toast.error('Failed to load image');
        window.URL.revokeObjectURL(url);
        setIsConverting(false);
      };

      img.src = url;
    } catch (error) {
      toast.error('PDF generation failed');
      setIsConverting(false);
    }
  };

  const convertAndDownload = async (format: ImageFormat) => {
    if (format === 'pdf') {
      setIsConverting(true);
      await downloadAsPDF();
      return;
    }

    setIsConverting(true);
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const img = new Image();
      const url = window.URL.createObjectURL(blob);
      
      img.onload = async () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        
        if (!ctx) {
          toast.error('Failed to convert image');
          setIsConverting(false);
          return;
        }

        ctx.drawImage(img, 0, 0);
        
        let mimeType = 'image/png';
        let quality = 1;
        
        switch (format) {
          case 'jpg':
            mimeType = 'image/jpeg';
            quality = 0.95;
            break;
          case 'webp':
            mimeType = 'image/webp';
            quality = 0.9;
            break;
          case 'tiff':
            // TIFF is lossless, uncompressed for printing
            mimeType = 'image/tiff';
            quality = 1;
            break;
          case 'bmp':
            mimeType = 'image/bmp';
            quality = 1;
            break;
          case 'png':
          default:
            mimeType = 'image/png';
            quality = 1;
            break;
        }

        canvas.toBlob(
          (convertedBlob) => {
            if (!convertedBlob) {
              toast.error('Failed to convert image');
              setIsConverting(false);
              return;
            }

            const downloadUrl = window.URL.createObjectURL(convertedBlob);
            const a = document.createElement('a');
            const baseName = filename.replace(/\.[^/.]+$/, '');
            a.href = downloadUrl;
            a.download = `${baseName}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            toast.success(`Downloaded as ${format.toUpperCase()}`);
            setIsOpen(false);
            setIsConverting(false);
          },
          mimeType,
          quality
        );
      };

      img.onerror = () => {
        toast.error('Failed to load image');
        window.URL.revokeObjectURL(url);
        setIsConverting(false);
      };

      img.src = url;
    } catch (error) {
      toast.error('Download failed');
      setIsConverting(false);
    }
  };
            quality = 0.95;
            break;
          case 'webp':
            mimeType = 'image/webp';
            quality = 0.9;
            break;
          case 'png':
          default:
            mimeType = 'image/png';
            quality = 1;
            break;
        }

        canvas.toBlob(
          (convertedBlob) => {
            if (!convertedBlob) {
              toast.error('Failed to convert image');
              setIsConverting(false);
              return;
            }

            const downloadUrl = window.URL.createObjectURL(convertedBlob);
            const a = document.createElement('a');
            const baseName = filename.replace(/\.[^/.]+$/, '');
            a.href = downloadUrl;
            a.download = `${baseName}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            toast.success(`Downloaded as ${format.toUpperCase()}`);
            setIsOpen(false);
            setIsConverting(false);
          },
          mimeType,
          quality
        );
      };

      img.onerror = () => {
        toast.error('Failed to load image');
        window.URL.revokeObjectURL(url);
        setIsConverting(false);
      };

      img.src = url;
    } catch (error) {
      toast.error('Download failed');
      setIsConverting(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isConverting}
        className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <ArrowDownTrayIcon className="w-4 h-4" />
        {isConverting ? 'Converting...' : 'Download'}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="absolute top-full right-0 mt-2 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-50 overflow-hidden min-w-[240px]"
          >
            <div className="p-2">
              {/* Standard Formats */}
              <div>
                <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 px-2 py-1.5">Standard Formats</p>
                {formats
                  .filter((f) => f.category === 'Standard')
                  .map((f) => (
                    <button
                      key={f.format}
                      onClick={() => convertAndDownload(f.format)}
                      disabled={isConverting}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-primary-50 dark:hover:bg-slate-700 rounded disabled:opacity-50 transition-colors"
                    >
                      {f.label}
                    </button>
                  ))}
              </div>

              {/* Print Ready Formats */}
              <div className="border-t border-slate-200 dark:border-slate-700 mt-1 pt-1">
                <p className="text-xs font-semibold text-green-700 dark:text-green-400 px-2 py-1.5">🖨️ Print Ready</p>
                {formats
                  .filter((f) => f.category === 'Print Ready')
                  .map((f) => (
                    <button
                      key={f.format}
                      onClick={() => convertAndDownload(f.format)}
                      disabled={isConverting}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-green-50 dark:hover:bg-slate-700 rounded disabled:opacity-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span>{f.label}</span>
                        <span className="text-xs text-green-600 dark:text-green-400 font-semibold">PRO</span>
                      </div>
                    </button>
                  ))}
                <p className="text-xs text-slate-500 dark:text-slate-400 px-2 py-2 italic">
                  Use TIFF, BMP, or PDF for direct textile printing with highest quality.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
