// src/pages/index.js
import { useState } from 'react';

export default function Home() {
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setResult(null);
    setError('');

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: input.trim() }),
      });

      const data = await res.json();

      if (res.ok) {
        setResult(data);
      } else {
        setError(data.error || 'Analysis failed. Please try again.');
      }
    } catch (err) {
      setError('Network error. Check your internet connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-green-50 p-4 sm:p-6 font-sans">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-200">
        
        {/* Header */}
        <div className="bg-green-700 p-6 sm:p-8 text-center">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white mb-2 tracking-tight">
             Fake News Detector
          </h1>
          <p className="text-green-100 text-sm sm:text-base font-semibold">
            AI-powered verification for Nigerian citizens — transparent and free
          </p>
        </div>

        <div className="p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="input" className="block text-sm font-bold text-gray-800 mb-2 uppercase tracking-wide">
                Paste News Text or URL
              </label>
              <textarea
                id="input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                rows={4}
                className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 
                           focus:ring-2 focus:ring-green-500 focus:border-green-500 
                           text-gray-900 bg-white placeholder-gray-400 disabled:bg-gray-50 
                           transition-all shadow-sm font-medium"
                placeholder="Example: 'BREAKING!!! Tinubu bans WhatsApp!' or https://punchng.com/..."
                disabled={loading}
              />
              <p className="mt-2 text-xs text-gray-500 text-right font-medium">
                Minimum 15 characters recommended
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-6 rounded-xl 
                         transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed 
                         shadow-md hover:shadow-lg transform hover:-translate-y-0.5 text-lg"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </span>
              ) : 'Analyze News'}
            </button>
          </form>

          {error && (
            <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg animate-pulse">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700 font-bold">{error}</p>
                </div>
              </div>
            </div>
          )}

          {result && (
            <div className={`mt-8 p-6 rounded-xl border-2 ${
              result.classification === 'FAKE' ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
            }`}>
              <h3 className="font-bold text-lg text-gray-800 mb-4 flex items-center">
                🔍 AI Analysis Result
              </h3>
              
              <div className="flex items-center justify-between mb-6">
                <span className="text-sm font-bold text-gray-500 uppercase">Verdict</span>
                <span className={`text-3xl font-extrabold px-6 py-2 rounded-lg ${
                  result.classification === 'FAKE' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                }`}>
                  {result.classification === 'FAKE' ? '🚨 FAKE' : '✅ REAL'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm text-gray-700 mb-4">
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <span className="block text-xs text-gray-500 uppercase font-bold">Confidence</span>
                  <span className="font-bold text-xl">{result.confidence}%</span>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <span className="block text-xs text-gray-500 uppercase font-bold">Model</span>
                  <span className="font-mono text-sm text-blue-600 font-bold truncate" title={result.model}>
                    {result.model || 'bart-large-mnli'}
                  </span>
                </div>
              </div>

              {/* Credibility Signals (if available from backend) */}
              {result.signals && result.signals.length > 0 && (
                <div className="mb-4 p-3 bg-white rounded-lg border border-gray-200">
                  <span className="block text-xs text-gray-500 uppercase font-bold mb-2">Detected Signals</span>
                  <div className="flex flex-wrap gap-2">
                    {result.signals.map((signal, idx) => (
                      <span key={idx} className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs rounded font-semibold">
                        ✓ {signal}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Source Type Indicator */}
              {result.sourceType && (
                <div className="mb-4">
                  <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 text-xs rounded font-bold">
                    Source: {result.sourceType === 'url' ? '🔗 URL (Scraped)' : '📝 Direct Text'}
                  </span>
                </div>
              )}

              <div className="mt-4 p-4 bg-white border border-yellow-200 rounded-lg">
                <p className="text-xs text-gray-600 leading-relaxed font-medium">
                  ⚠️ <strong className="font-bold">Ethical Disclaimer:</strong> This is an AI prediction based on language patterns, 
                  not a verified fact-check. Confidence scores reflect pattern matching, not factual accuracy. 
                  False positives may occur, especially on non-political content. Do not use for punitive decisions.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer - INCREASED FONT WEIGHT */}
        <div className="bg-gray-100 px-6 py-5 border-t border-gray-200 text-center">
          <p className="text-sm text-gray-700 font-bold">
            Project by <span className="text-gray-900 font-extrabold">ONU MICHAEL CHIADIKOBI</span> 
          </p>
          <p className="text-sm text-gray-600 mt-1 font-bold">
            Lead City University | Frugal AI for Nigeria
          </p>
          <p className="text-xs text-gray-500 mt-2 font-semibold">
            © 2026 - All Rights: Reserved
          </p>
        </div>
      </div>
    </div>
  );
}