// src/pages/api/analyze.js
import { NextApiRequest, NextApiResponse } from 'next';
import { InferenceClient } from '@huggingface/inference';
import axios from 'axios';
import * as cheerio from 'cheerio';

// Initialize Hugging Face Client
// Make sure you have HF_API_TOKEN in your .env.local file
const hf = new InferenceClient(process.env.HF_API_TOKEN);
const MODEL_ID = 'facebook/bart-large-mnli'; // Or your preferred zero-shot model

// === HELPER: Detect URL ===
function isUrl(text) {
  return /^https?:\/\//i.test(text);
}

// === HELPER: Scrape Article Text from URL ===
async function scrapeArticleText(url) {
  try {
    const response = await axios.get(url, {
      timeout: 10000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    const $ = cheerio.load(response.data);
    
    // Remove scripts, styles, navs, footers, ads, etc.
    $('script, style, nav, footer, .advertisement, .sidebar, .comments, header').remove();

    // Selectors for main content
    const selectors = [
      'article', 
      '.article-content', 
      '.post-content', 
      '.entry-content', 
      'main', 
      'p'
    ];
    
    let articleText = '';

    for (const selector of selectors) {
      const element = $(selector);
      if (element.length > 0) {
        // Get text from the largest content block found
        const text = element.text().replace(/\s+/g, ' ').trim();
        if (text.length > articleText.length) {
          articleText = text;
        }
      }
    }

    // Fallback to body if specific selectors fail
    if (articleText.length < 100) {
      articleText = $('body').text().replace(/\s+/g, ' ').trim();
    }

    if (articleText.length < 50) {
      throw new Error('Could not extract meaningful content from URL');
    }

    // Limit text length to avoid API token limits (usually ~500-1000 tokens is safe for zero-shot)
    return articleText.substring(0, 800); 

  } catch (err) {
    console.error('Scraping error:', err.message);
    throw new Error('Failed to fetch or parse article content.');
  }
}

// === HELPER: Heuristic Credibility Signals ===
function analyzeCredibilitySignals(text) {
  const signals = { positive: [], negative: [], score: 0 };

  // --- Positive Signals (Indicators of Real News) ---
  if (/\d+\s*(feared|killed|rescued|abducted|injured|dead)/i.test(text)) {
    signals.positive.push('Numeric casualty specificity');
    signals.score += 15;
  }

  if (/Police|Government|Officials|Authorities|Ministry|Commission/i.test(text)) {
    signals.positive.push('Official source mentioned');
    signals.score += 15;
  }

  if (/(in|at|from)\s*(Niger|Ogun|Yobe|Lagos|Abuja|Kano|Rivers|Delta|Nigeria)/i.test(text)) {
    signals.positive.push('Specific location mentioned');
    signals.score += 10;
  }

  if (/probe|warns|threatens|rescued|abducted|capsizes|assault|investigates/i.test(text)) {
    signals.positive.push('Standard news vocabulary');
    signals.score += 10;
  }

  if (/(Tinubu|Okpebholo|Sanwo-Olu|El-Rufai|Wike|Inspector-General|Commissioner)/i.test(text)) {
    signals.positive.push('Named public official');
    signals.score += 10;
  }

  if (text.length > 200) {
    signals.positive.push('Substantial article length');
    signals.score += 10;
  }

  if (!/[!]{2,}/.test(text) && !/SHARE NOW|MUST READ|URGENT/i.test(text)) {
    signals.positive.push('No sensationalist markers');
    signals.score += 10;
  }

  // --- Negative Signals (Indicators of Fake News) ---
  if (/[!]{3,}/.test(text)) {
    signals.negative.push('Excessive exclamation marks');
    signals.score -= 20;
  }

  if (/SHARE NOW|FORWARD TO|SEND TO ALL|WHATSAPP GROUP/i.test(text)) {
    signals.negative.push('Viral manipulation language');
    signals.score -= 20;
  }

  if (/FOREVER|BANNED|ILLEGAL|ARRESTED.*NOW/i.test(text)) {
    signals.negative.push('Absolute/unverified claims');
    signals.score -= 15;
  }

  const capsWords = text.match(/\b[A-Z]{5,}\b/g);
  if (capsWords && capsWords.length > 2) {
    signals.negative.push('Excessive capitalization');
    signals.score -= 10;
  }

  return signals;
}

// === MAIN API HANDLER ===
export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const { input } = req.body;

  // Validate Input
  if (!input || typeof input !== 'string' || !input.trim()) {
    return res.status(400).json({ error: 'Input required.' });
  }

  const processedInput = input.trim();
  if (processedInput.length < 10) {
    return res.status(400).json({ error: 'Input too short (min 10 chars).' });
  }

  let textToAnalyze = processedInput;
  let sourceType = 'text';

  try {
    // 1. Check if Input is URL and Scrape if necessary
    if (isUrl(processedInput)) {
      sourceType = 'url';
      textToAnalyze = await scrapeArticleText(processedInput);
    }

    // 2. Run Heuristic Analysis (Local Logic)
    const heuristicSignals = analyzeCredibilitySignals(textToAnalyze);
    
    // 3. Run AI Model (Hugging Face Zero-Shot)
    // Note: Ensure HF_API_TOKEN is set in your .env.local file
    let aiLabel = 'REAL';
    let aiConfidence = 0.5;
    let modelUsed = 'bart-large-mnli';

    try {
      const result = await hf.zeroShotClassification({
        model: MODEL_ID,
        inputs: textToAnalyze,
        parameters: {
          candidate_labels: ['fake news', 'real news'],
        },
      });

      // Hugging Face returns labels sorted by score usually, but we check explicitly
      const scores = {};
      result.labels.forEach((label, i) => {
        scores[label] = result.scores[i];
      });

      if (scores['fake news'] > scores['real news']) {
        aiLabel = 'FAKE';
        aiConfidence = scores['fake news'];
      } else {
        aiLabel = 'REAL';
        aiConfidence = scores['real news'];
      }
    } catch (aiError) {
      console.error('Hugging Face API Error:', aiError);
      // Fallback if API fails: Use Heuristics only
      aiLabel = heuristicSignals.score < -10 ? 'FAKE' : 'REAL';
      aiConfidence = 0.6; // Lower confidence for fallback
      modelUsed = 'heuristic-fallback';
    }

    // 4. Combine Results for Final Verdict
    // You can adjust this logic. Currently, we prioritize AI but use heuristics for explanation.
    let finalVerdict = aiLabel;
    let finalConfidence = Math.round(aiConfidence * 100);

    // Optional: Boost confidence if heuristics agree with AI
    if ((aiLabel === 'FAKE' && heuristicSignals.score < -10) || 
        (aiLabel === 'REAL' && heuristicSignals.score > 10)) {
      finalConfidence = Math.min(99, finalConfidence + 5);
    }

    // 5. Send Response
    return res.status(200).json({
      verdict: finalVerdict,
      confidence: finalConfidence,
      model: modelUsed,
      sourceType: sourceType,
      signals: heuristicSignals,
      disclaimer: 'This is an AI prediction based on pattern matching. Always verify with trusted sources.',
      rawTextPreview: textToAnalyze.substring(0, 100) + '...'
    });

  } catch (error) {
    console.error('Server Error:', error);
    return res.status(500).json({ error: error.message || 'Internal Server Error' });
  }
}