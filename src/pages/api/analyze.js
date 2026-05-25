// src/pages/api/analyze.js
// NOW CALLS FLASK API ON RAILWAY

import axios from 'axios';
import * as cheerio from 'cheerio';

// ============================================
// FLASK API CONFIGURATION
// ============================================
// For local testing: http://localhost:5000
// For production: set FLASK_API_URL in Vercel env variables
const FLASK_API_URL = process.env.FLASK_API_URL || 'http://localhost:5000';

// ============================================
// URL DETECTION AND SCRAPING
// ============================================

function isUrl(text) {
  return /^https?:\/\//i.test(text);
}

async function scrapeArticleText(url) {
  try {
    const response = await axios.get(url, {
      timeout: 10000,
      headers: { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
      }
    });
    
    const $ = cheerio.load(response.data);
    $('script, style, nav, footer, .advertisement, .sidebar, .comments, header').remove();
    
    const selectors = ['article', '.article-content', '.post-content', '.entry-content', 'main'];
    let articleText = '';
    
    for (const selector of selectors) {
      const element = $(selector);
      if (element.length > 0) {
        articleText = element.text().replace(/\s+/g, ' ').trim();
        if (articleText.length > 200) break;
      }
    }
    
    if (articleText.length < 200) {
      const paragraphs = [];
      $('p').each((i, el) => {
        const text = $(el).text().trim();
        if (text.length > 50 && 
            !text.toLowerCase().includes('copyright') &&
            !text.toLowerCase().includes('advertisement')) {
          paragraphs.push(text);
        }
      });
      articleText = paragraphs.join(' ');
    }
    
    if (articleText.length < 50) {
      throw new Error('Could not extract meaningful content from URL');
    }
    
    return articleText.substring(0, 2000);
    
  } catch (error) {
    console.error('Scraping error:', error.message);
    throw new Error('Could not extract content from URL. Please paste the text directly.');
  }
}

// ============================================
// FALLBACK PATTERN DETECTION (if Flask API is down)
// ============================================

function fallbackPatternDetection(text) {
  let fakeScore = 0;
  
  // Death hoax
  if (/(president|tinubu|buhari).{0,30}dead/i.test(text)) {
    fakeScore += 60;
  }
  
  // WhatsApp chain
  if (/(SHARE|FORWARD).*(GROUPS|CONTACTS)/i.test(text)) {
    fakeScore += 30;
  }
  
  // Exclamation marks
  const exclamationCount = (text.match(/!/g) || []).length;
  if (exclamationCount > 5) fakeScore += 15;
  if (exclamationCount > 3) fakeScore += 10;
  
  // Uppercase ratio
  const uppercaseChars = (text.match(/[A-Z]/g) || []).length;
  const totalLength = text.length;
  if (totalLength > 0 && uppercaseChars / totalLength > 0.4) {
    fakeScore += 20;
  }
  
  // Real indicators
  if (/premium times|punch newspaper|vanguard|guardian\.ng/i.test(text)) {
    fakeScore -= 30;
  }
  
  const finalScore = Math.min(95, Math.max(5, fakeScore));
  return {
    isFake: finalScore > 50,
    confidence: finalScore > 50 ? finalScore : 100 - finalScore,
    score: finalScore
  };
}

// ============================================
// MAIN API HANDLER
// ============================================

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  const { input } = req.body;
  
  if (!input || typeof input !== 'string' || !input.trim()) {
    return res.status(400).json({ error: 'Please provide text or URL to analyze' });
  }
  
  let textToAnalyze = input.trim();
  let sourceType = 'text';
  
  try {
    // Handle URL
    if (isUrl(textToAnalyze)) {
      sourceType = 'url';
      textToAnalyze = await scrapeArticleText(textToAnalyze);
      if (!textToAnalyze || textToAnalyze.length < 50) {
        return res.status(400).json({ error: 'Could not extract enough content from URL' });
      }
    }
    
    if (textToAnalyze.length < 20) {
      return res.status(400).json({ error: 'Text too short (minimum 20 characters)' });
    }
    
    // Call Flask API for ML prediction
    let mlResult = null;
    let usingML = false;
    
    try {
      const response = await axios.post(`${FLASK_API_URL}/predict`, {
        text: textToAnalyze.substring(0, 2000)
      }, {
        timeout: 8000
      });
      
      mlResult = response.data;
      usingML = mlResult.ml_available && mlResult.model_used !== 'pattern-only-fallback';
      console.log('ML API response:', mlResult);
      
    } catch (mlError) {
      console.error('Flask API error:', mlError.message);
      // Fall back to pattern detection
      mlResult = fallbackPatternDetection(textToAnalyze);
      mlResult.model_used = 'pattern-fallback';
      mlResult.ml_available = false;
    }
    
    // Build explanation
    let explanation = '';
    if (mlResult.classification === 'FAKE') {
      if (/(president|tinubu|buhari).{0,30}dead/i.test(textToAnalyze)) {
        explanation = '🚨 DEATH HOAX DETECTED: This appears to be a false death announcement. ';
      } else if (mlResult.pattern_score && mlResult.pattern_score > 50) {
        explanation = '⚠️ This matches patterns commonly found in Nigerian fake news. ';
      } else {
        explanation = '⚠️ Our ML model identified this as potentially fake news. ';
      }
      
      if (usingML) {
        explanation += `The ensemble model (${mlResult.models_loaded?.join(', ') || 'multiple models'}) classified this with ${mlResult.confidence}% confidence. `;
      }
      
      if (/palliative|grant|money|payment/i.test(textToAnalyze)) {
        explanation += 'Financial scams promising money are common. Government palliatives are NEVER distributed via WhatsApp forwards. ';
      }
      if (/(share|forward|send to).*(groups|contacts)/i.test(textToAnalyze)) {
        explanation += 'Legitimate news never asks you to share to multiple groups. ';
      }
    } else {
      explanation = '✅ This content appears legitimate based on our analysis. ';
      if (usingML) {
        explanation += `Our ML ensemble (${mlResult.models_loaded?.join(', ') || 'multiple models'}) classified this as REAL with ${mlResult.confidence}% confidence. `;
      }
      explanation += 'Always cross-reference with trusted Nigerian news sources like Premium Times, Punch, or Vanguard.';
    }
    
    let confidenceLevel = 'LOW';
    if (mlResult.confidence >= 80) confidenceLevel = 'HIGH';
    else if (mlResult.confidence >= 60) confidenceLevel = 'MEDIUM';
    
    const response = {
      classification: mlResult.classification,
      confidence: mlResult.confidence,
      confidenceLevel: confidenceLevel,
      explanation: explanation.trim(),
      model: mlResult.model_used || (usingML ? 'ensemble' : 'pattern'),
      ml_available: mlResult.ml_available !== false,
      sourceType: sourceType,
      ml_details: mlResult.ml_available !== false ? {
        pattern_score: mlResult.pattern_score,
        ml_prediction: mlResult.ml_prediction,
        models_used: mlResult.models_loaded || []
      } : null,
      disclaimer: 'AI analysis using ML models trained on 7,000+ Nigerian news samples. Always verify with trusted sources.',
      tips: mlResult.classification === 'FAKE' ? [
        '✓ Check if the news appears on verified Nigerian news websites',
        '✓ Look for official statements from government or police',
        '✓ Be suspicious of messages asking you to share or forward',
        '✓ Verify with fact-checking platforms like Dubawa.org'
      ] : [
        '✓ Still verify with official sources when possible',
        '✓ Check the publication date for timeliness',
        '✓ Look for the original source of the information'
      ]
    };
    
    return res.status(200).json(response);
    
  } catch (error) {
    console.error('Analysis error:', error);
    return res.status(500).json({ 
      error: 'Analysis failed. Please try again.',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}