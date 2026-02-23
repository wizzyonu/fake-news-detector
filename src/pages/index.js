import { useState } from 'react';


// Cache pipeline to avoid reloading


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
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-4 sm:p-6">
      <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-6 sm:p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">
            🕵️‍♂️ Fake News Detector
          </h1>
          <p className="text-gray-600 text-sm sm:text-base">
            AI-powered verification for Nigerian citizens — transparent and free
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="input" className="block text-sm font-medium text-gray-700 mb-2">
              Paste news text or URL:
            </label>
            <textarea
              id="input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={4}
              className="w-full border border-gray-800 rounded-md px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-transparent "
              placeholder="Example: 'Tinubu bans WhatsApp!' or https://punchng.com/..."
            />
          </div>

          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-md transition duration-200 disabled:opacity-50"
          >
            {loading ? '🔍 Analyzing with AI...' : 'Analyze'}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-center">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-8 p-5 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-lg text-gray-800 mb-3">🔍 AI Analysis Result</h3>
            
            <div className="mb-3">
              <span className={`text-2xl font-bold ${
                result.classification === 'FAKE' 
                  ? 'text-red-600' 
                  : 'text-green-600'
              }`}>
                {result.classification === 'FAKE' ? '🚨 FAKE' : '✅ REAL'}
              </span>
            </div>

            <div className="text-sm text-gray-700 space-y-1">
              <p>
                <span className="font-medium">Confidence:</span>{' '}
                <span className="font-semibold">{result.confidence}%</span>
              </p>
              <p>
                <span className="font-medium">AI Model:</span>{' '}
                <span className="font-mono text-blue-600">{result.model}</span>
              </p>
              <p>
                <span className="font-medium">Analyzed:</span> {result.analyzed}
              </p>
            </div>

            <div className="mt-4 p-3 bg-white border border-yellow-100 rounded">
              <p className="text-xs text-gray-700 italic">
                ⚠️ <strong>Note:</strong> Confidence is estimated by the system. 
                {result.model} provides a verdict but not a native probability score.
              </p>
              <p className="text-xs text-red-600 italic mt-1">
                This is an AI prediction, not a fact-check. False positives may occur. 
                Do not use for punitive decisions.
              </p>
            </div>
          </div>
        )}

        <div className="mt-8 text-center text-xs text-gray-500">
          <p>Project by ONU MICHAEL CHIADIKOBI | Lead City University</p>
          <p className="mt-1">CSC 407 Final Year Project | Frugal AI for Nigeria</p>
        </div>
      </div>
    </div>
  );
}