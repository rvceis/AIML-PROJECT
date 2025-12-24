import { useMemo } from 'react';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import docsContent from '../docs/content.md?raw';

export function DocsFixed() {
  const html = useMemo(() => {
    marked.setOptions({
      gfm: true,
      breaks: true,
    });
    const raw = marked.parse(docsContent);
    return DOMPurify.sanitize(raw);
  }, []);

  return (
    <section id="docs" className="py-12">
      <div className="max-w-6xl mx-auto px-4 card-surface rounded-3xl p-6 shadow-lg border border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs font-semibold text-primary-600">Docs</p>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Technical Documentation</h2>
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-300">Rendered markdown</span>
        </div>
        <div className="rounded-2xl bg-white/80 border border-slate-200 p-6 overflow-y-auto max-h-[70vh]">
          <article className="prose prose-slate max-w-none" dangerouslySetInnerHTML={{ __html: html }} />
        </div>
      </div>
    </section>
  );
}
