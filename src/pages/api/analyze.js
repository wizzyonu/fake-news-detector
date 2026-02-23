
// Import official Hugging Face Inference client for Node.js
// This is the recommended library for free-tier API integration
import { InferenceClient } from '@huggingface/inference';

// Import axios for reliable HTTP requests (URL fetching)
import axios from 'axios';

// Import cheerio for fast, lightweight HTML parsing (like jQuery for Node.js)
import * as cheerio from 'cheerio';

// === CONFIGURATION SECTION ===
// Initialize Hugging Face client using API token from environment variables
// WARNING: Never hardcode token. Store in .env.local as HF_API_TOKEN
const hf = new InferenceClient(process.env.HF_API_TOKEN);

// Specify the zero-shot classification model to use
// This model is active, free-tier compatible, and returns probability scores
const MODEL_ID = 'facebook/bart-large-mnli';

// Define maximum input length to avoid token overflow errors
// Model supports 512 tokens; 450 chars is a safe conservative limit for English
const MAX_INPUT_LENGTH = 450;

// === RATE LIMITING SECTION ===
// In-memory store for tracking request counts per IP address
// Uses JavaScript Map for O(1) access; cleared on server restart (acceptable for free-tier)
const rateLimitStore = new Map();

// Rate limit policy: Allow 5 requests per IP address every 60 seconds
// Prevents Hugging Face free-tier quota exhaustion during demos or testing
const MAX_REQUESTS = 5;
const WINDOW_MS = 60 * 1000; // 60 seconds in milliseconds

/**
 * Checks if a given IP address is within rate limit quota
 * @param {string} ip - Client IP address
 * @returns {Object} - { allowed: boolean, remaining?: number, reset?: number }
 *   - allowed: true if request should proceed
 *   - remaining: number of requests left in current window
 *   - reset: seconds until next window resets (if blocked)
 */
function checkRateLimit(ip) {
  const now = Date.now(); // Get current timestamp in milliseconds
  const record = rateLimitStore.get(ip); // Retrieve existing record for this IP

  // If record exists and window hasn't expired
  if (record && record.resetTime > now) {
    // If already at max requests, deny access
    if (record.count >= MAX_REQUESTS) {
      return { 
        allowed: false, 
        reset: Math.ceil((record.resetTime - now) / 1000) // Return seconds to reset
      };
    }
    // Increment request count and update store
    rateLimitStore.set(ip, { count: record.count + 1, resetTime: record.resetTime });
    return { 
      allowed: true, 
      remaining: MAX_REQUESTS - record.count - 1 
    };
  } else {
    // Create new rate limit window for this IP
    rateLimitStore.set(ip, { count: 1, resetTime: now + WINDOW_MS });
    return { 
      allowed: true, 
      remaining: MAX_REQUESTS - 1 
    };
  }
}

// === MAIN API HANDLER ===
/**
 * Main request handler for POST /api/analyze
 * Validates input, enforces rate limits, processes text/URL, and returns AI result
 */
export default async function handler(req, res) {
  // Extract client IP address with fallbacks for Vercel, Render, and local dev
  const clientIP = 
    req.headers['x-forwarded-for']?.toString().split(',')[0]?.trim() || // Vercel/Render proxy
    req.socket.remoteAddress || // Direct connection
    '127.0.0.1'; // Localhost fallback

  // Enforce rate limiting BEFORE any resource-intensive operation
  const rateCheck = checkRateLimit(clientIP);
  if (!rateCheck.allowed) {
    // Return 429 Too Many Requests with human-readable message
    return res.status(429).json({
      error: `Too many requests. Try again in ${rateCheck.reset} seconds.`
    });
  }

  // Set standard rate limit headers for transparency (good REST practice)
  res.setHeader('X-RateLimit-Limit', MAX_REQUESTS.toString());
  res.setHeader('X-RateLimit-Remaining', (rateCheck.remaining || 0).toString());
  if (rateCheck.reset) {
    res.setHeader('X-RateLimit-Reset', rateCheck.reset.toString());
  }

  // === INPUT VALIDATION ===
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed. Use POST.' });
  }

  // Extract and validate input from request body
  const { input } = req.body;
  if (!input || typeof input !== 'string' || !input.trim()) {
    return res.status(400).json({ error: 'Input must be a non-empty string.' });
  }

  // === INPUT PROCESSING ===
  const textInput = input.trim();
  const isUrl = /^https?:\/\//i.test(textInput); // Simple URL detection
  let processedText = '';

  // If input is a URL, scrape the main article content
  if (isUrl) {
    try {
      // Fetch webpage with browser-like User-Agent to avoid bot blocking
      const response = await axios.get(textInput, {
        timeout: 10000, // 10-second network timeout
        headers: {
          'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
        }
      });

      // Load HTML into cheerio for DOM manipulation
      const $ = cheerio.load(response.data);

      // Remove non-content elements that interfere with text extraction
      $('script, style, nav, footer, .advertisement, .sidebar').remove();

      // Priority list of HTML selectors to extract main article body
      // Ordered from most semantic (article) to fallback (p)
      const contentSelectors = [
        'article',
        'main',
        '.post-content',
        '.entry-content',
        '.article-body',
        '.content',
        'p'
      ];

      // Iterate through selectors and extract first meaningful text block
      for (const selector of contentSelectors) {
        const element = $(selector);
        if (element.length > 0) {
          // Normalize whitespace (replace multiple spaces/tabs with single space)
          processedText = element.text().replace(/\s+/g, ' ').trim();
          if (processedText.length > 50) break; // Ensure content is substantial
        }
      }

      // Fallback: if no meaningful content found, use entire body
      if (processedText.length < 50) {
        processedText = $('body').text().replace(/\s+/g, ' ').trim();
      }

      // Reject if extracted text is too short to analyze
      if (processedText.length < 20) {
        return res.status(400).json({ error: 'Could not extract meaningful text from URL.' });
      }

    } catch (err) {
      // Log detailed error for debugging (not exposed to user)
      console.error('URL scraping failed:', err.message);
      return res.status(500).json({ error: 'Failed to fetch or parse URL content.' });
    }
  } else {
    // Input is plain text — use as-is
    processedText = textInput;
  }

  // Truncate input to stay within model token limits
  if (processedText.length > MAX_INPUT_LENGTH) {
    processedText = processedText.substring(0, MAX_INPUT_LENGTH);
  }
  // === INPUT QUALITY VALIDATION ===
// Reject inputs that are too short or lack real words
if (processedText.length < 10) {
  return res.status(400).json({
    error: 'Input too short. Enter at least 10 meaningful characters.'
  });
}

// Check if input contains at least 2 alphabetic words
const wordCount = processedText.trim().split(/\s+/).filter(word => 
  /^[a-zA-Z]/.test(word) && word.length >= 2
).length;

if (wordCount < 2) {
  return res.status(400).json({
    error: 'Input must contain at least two real words (e.g., "Nigeria elections").'
  });
}

// Optional: reject inputs with high entropy (likely random)
const hasRealWords = /[a-zA-Z]{3,}/.test(processedText); // at least one 3-letter word
if (!hasRealWords) {
  return res.status(400).json({
    error: 'Input appears to be random text. Please enter real sentences.'
  });
}


    // === AI INFERENCE: Use facebook/bart-large-mnli with proper labels ===
  try {
    const result = await hf.zeroShotClassification({
      model: 'facebook/bart-large-mnli',
      inputs: processedText,
      parameters: {
        candidate_labels: ['contains false information', 'is factually accurate'],
        multi_class: false
      }
    });

    // Hugging Face returns array of {label, score}
    if (!Array.isArray(result) || result.length === 0) {
      throw new Error('Empty response');
    }

    // Find highest score
    const top = result.reduce((max, item) => 
      item.score > max.score ? item : max
    , { score: -1 });

    let classification, confidence;
    if (top.label === 'contains false information') {
      classification = 'FAKE';
      confidence = Math.round(top.score * 100);
    } else if (top.label === 'is factually accurate') {
      classification = 'REAL';
      confidence = Math.round(top.score * 100);
    // } else {
    //   // Fallback: use score threshold
    //   classification = top.score > 0.5 ? 'FAKE' : 'REAL';
    //   confidence = Math.round(top.score * 100);
    }

    return res.status(200).json({
      classification,
      confidence,
      model: 'facebook/bart-large-mnli',
      analyzed: new Date().toISOString()
    });

 
  } catch (err) {
    console.error('Hugging Face API error:', err);

    if (err.message?.includes('rate limit') || err.statusCode === 429) {
      return res.status(429).json({
        error: 'Too many requests. Try again in 60 seconds.'
      });
    }

    if (err.message?.includes('loading') || err.statusCode === 503) {
      return res.status(503).json({
        error: 'Model is loading. Wait 30 seconds and retry.'
      });
    }

    if (processedText.length < 10) {
      return res.status(400).json({
        error: 'Input too short. Enter at least 10 characters.'
      });
    }

    return res.status(500).json({
      error: 'AI analysis failed. Try a different input.'
    });
  }
}