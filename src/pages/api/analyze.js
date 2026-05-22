// src/pages/api/analyze.js
import { getOnnxModel } from '../../../lib/onnxModel.js';
import axios from 'axios';
import * as cheerio from 'cheerio';

// ============================================
// ENHANCED NIGERIAN FAKE NEWS PATTERNS (UPDATED)
// ============================================

// HIGHEST PRIORITY - Absolute fake indicators (these alone should trigger FAKE)
const ABSOLUTE_FAKE_INDICATORS = [
  // WhatsApp viral chain messages
  { pattern: /SHARE\s+(THIS|TO)\s+\d+\s+WHATSAPP\s+GROUPS/i, weight: 50, critical: true },
  { pattern: /FORWARD\s+THIS\s+MESSAGE\s+TO\s+\d+\s+(GROUPS|CONTACTS)/i, weight: 50, critical: true },
  { pattern: /WITHIN\s+\d+\s+MINUTES/i, weight: 45, critical: true },
  { pattern: /FAILURE\s+TO\s+SHARE/i, weight: 45, critical: true },
  { pattern: /SHARE\s+THIS\s+TO\s+GET/i, weight: 45, critical: true },
  { pattern: /SEND\s+THIS\s+TO\s+\d+\s+PEOPLE/i, weight: 45, critical: true },
  
  // Classic scam patterns
  { pattern: /₦\d{4,6}\s+PALLIATIVE/i, weight: 40, critical: true },
  { pattern: /CLAIM\s+YOURS\s+.*\s+BEFORE\s+ITS\s+REMOVED/i, weight: 40, critical: true },
  { pattern: /DON['']T\s+IGNORE\s+THIS\s+MESSAGE/i, weight: 40, critical: true },
  { pattern: /THIS\s+IS\s+NOT\s+A\s+JOKE/i, weight: 35, critical: true },
];

// Nigerian-specific fake news patterns
const NIGERIAN_FAKE_PATTERNS = [
  // Death hoax patterns
  { pattern: /president.*dead|tinubu.*dead|buhari.*dead/i, weight: 40 },
  { pattern: /dies suddenly|found dead|confirmed dead/i, weight: 35 },
  { pattern: /killed in accident|dies in hospital/i, weight: 30 },
  
  // Viral sharing prompts (INCREASED WEIGHTS)
  { pattern: /SHARE\s+TO\s+ALL\s+GROUPS/i, weight: 40 },
  { pattern: /URGENT\s+SHARE\s+NOW/i, weight: 35 },
  { pattern: /FORWARD\s+IMMEDIATELY/i, weight: 35 },
  { pattern: /SHARE\s+THIS\s+MESSAGE/i, weight: 30 },
  { pattern: /SEND\s+TO\s+ALL\s+CONTACTS/i, weight: 35 },
  { pattern: /COPY\s+AND\s+PASTE\s+THIS/i, weight: 30 },
  
  // Scam-specific patterns
  { pattern: /₦\d{4,6}\s+(palliative|money|grant|payment)/i, weight: 35 },
  { pattern: /CLAIM\s+YOUR\s+(money|palliative|grant|funds)/i, weight: 35 },
  { pattern: /BEFORE\s+ITS\s+(removed|closed|deleted)/i, weight: 30 },
  
  // Sensational markers
  { pattern: /BREAKING\s+NEWS.*!.*!/i, weight: 25 },
  { pattern: /CONFIRMED!!!+/i, weight: 25 },
  { pattern: /SHOCKING!!!+/i, weight: 25 },
  { pattern: /[!]{4,}/, weight: 20 },
  { pattern: /[!]{3,}/, weight: 15 },
  
  // Suspicious urgency
  { pattern: /HURRY\s+BEFORE/i, weight: 30 },
  { pattern: /LAST\s+CHANCE/i, weight: 30 },
  { pattern: /EXPIRES\s+SOON/i, weight: 25 },
  
  // Warning language
  { pattern: /WARNING!!!+/i, weight: 25 },
  { pattern: /ALERT!!!+/i, weight: 25 },
  { pattern: /DANGER!!!+/i, weight: 25 },
];

// Real news indicators (NEGATIVE weights - very specific patterns only)
const REAL_NEWS_INDICATORS = [
  // Verified Nigerian news sources (high confidence)
  { pattern: /premium\s+times\s+reports?/i, weight: -30, source: true },
  { pattern: /punch\s+newspaper/i, weight: -30, source: true },
  { pattern: /vanguard\s+ng/i, weight: -25, source: true },
  { pattern: /guardian\.ng/i, weight: -25, source: true },
  { pattern: /according\s+to\s+(premium|punch|vanguard|guardian)/i, weight: -25, source: true },
  
  // Official government communication
  { pattern: /(cbn|ncdc|inec|ncc|npa|firs|nigerian\s+army)\s+(announced|confirmed|stated|said)/i, weight: -20 },
  { pattern: /in\s+a\s+statement\s+(signed|issued)\s+by/i, weight: -20 },
  { pattern: /spokesperson\s+(\w+)\s+said/i, weight: -20 },
  { pattern: /central\s+bank\s+of\s+nigeria/i, weight: -20 },
  { pattern: /nigeria\s+centre\s+for\s+disease\s+control/i, weight: -20 },
  
  // Date-specific legitimate news
  { pattern: /(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},\s+202[4-5]/i, weight: -15 },
  
  // Official event markers
  { pattern: /at\s+the\s+(presidential\s+villa|national\s+assembly|apec|state\s+house)/i, weight: -15 },
  { pattern: /at\s+the\s+state\s+house\s+abuja/i, weight: -15 },
  
  // News structure indicators
  { pattern: /in\s+an\s+interview\s+with/i, weight: -15 },
  { pattern: /reports\s+that/i, weight: -12 },
  { pattern: /confirmed\s+to\s+([A-Z]+)\s+newspaper/i, weight: -15 },
  
  // Professional journalistic language
  { pattern: /the\s+([A-Za-z]+)\s+learned\s+that/i, weight: -15 },
  { pattern: /sources\s+close\s+to\s+the\s+matter\s+revealed/i, weight: -12 },
];

// High-priority fake patterns (legacy - kept for compatibility)
const HIGH_PRIORITY_FAKE = [
  /dead|dies?|died|death|killed|assassinated/i,
  /resigns?|resignation|steps down|leaves office/i,
  /arrested|detained|jailed|imprisoned/i,
  /banned|prohibited|forbidden/i,
];

// Common fake patterns (legacy - kept for compatibility)
const FAKE_PATTERNS = [
  { pattern: /SHARE\s+TO\s+ALL\s+GROUPS/i, weight: 25 },
  { pattern: /URGENT\s+SHARE\s+NOW/i, weight: 25 },
  { pattern: /FORWARD\s+IMMEDIATELY/i, weight: 25 },
  { pattern: /DON['']T\s+IGNORE\s+THIS/i, weight: 20 },
  { pattern: /BREAKING\s+NEWS.*!.*!/i, weight: 20 },
  { pattern: /CONFIRMED!!!+/i, weight: 20 },
  { pattern: /SHOCKING!!!+/i, weight: 20 },
  { pattern: /YOU\s+WON['']T\s+BELIEVE/i, weight: 20 },
  { pattern: /[!]{3,}/, weight: 15 },
  { pattern: /president.*dead/i, weight: 30 },
  { pattern: /tinubu.*dead/i, weight: 30 },
  { pattern: /dies suddenly|found dead/i, weight: 30 },
  { pattern: /killed in accident|dies in hospital/i, weight: 25 },
];

// Real news indicators (legacy - kept for compatibility)
const REAL_PATTERNS = [
  { pattern: /premium\s+times/i, weight: -25 },
  { pattern: /punch\s+ng/i, weight: -20 },
  { pattern: /vanguard\s+ng/i, weight: -20 },
  { pattern: /guardian\.ng/i, weight: -20 },
  { pattern: /according\s+to\s+the\s+[A-Z]+/i, weight: -15 },
  { pattern: /spokesperson\s+said/i, weight: -15 },
  { pattern: /in an interview with/i, weight: -15 },
  { pattern: /reports that/i, weight: -10 },
  { pattern: /confirmed to [A-Z]+/i, weight: -15 },
];

function calculatePatternScore(text) {
  let fakeScore = 0;
  let realScore = 0;
  let reason = [];
  let criticalFakeDetected = false;
  let chainCount = 0;
  
  // STEP 1: Check ABSOLUTE fake indicators first (these override everything)
  for (const { pattern, weight, critical } of ABSOLUTE_FAKE_INDICATORS) {
    if (pattern.test(text)) {
      fakeScore += weight;
      criticalFakeDetected = true;
      reason.push(`🚨 CRITICAL: ${pattern.source.slice(0, 50)}... detected`);
      break; // Once we find a critical pattern, stop checking others
    }
  }
  
  // STEP 2: If critical fake detected, boost score significantly
  if (criticalFakeDetected) {
    fakeScore += 30; // Boost to ensure FAKE classification
    if (!reason.includes("⚠️ Contains classic WhatsApp scam patterns")) {
      reason.push("⚠️ Contains classic WhatsApp scam patterns");
    }
  }
  
  // STEP 3: Check Nigerian-specific fake patterns
  for (const { pattern, weight } of NIGERIAN_FAKE_PATTERNS) {
    if (pattern.test(text)) {
      const matches = (text.match(pattern) || []).length;
      const count = Math.min(matches, 2);
      fakeScore += weight * count;
      
      if (weight >= 30 && !reason.some(r => r.includes(pattern.source.slice(0, 30)))) {
        reason.push(`⚠️ ${pattern.source.slice(0, 50)}... detected`);
      }
    }
  }
  
  // STEP 4: Check for WhatsApp chain message structure
  const whatsappChainIndicators = [
    /SHARE.*GROUPS/i,
    /WITHIN.*MINUTES/i,
    /FAILURE.*SHARE/i,
    /FORWARD.*NOW/i,
    /SEND.*CONTACTS/i,
    /SHARE.*THIS.*MESSAGE/i,
    /PLEASE.*FORWARD/i,
  ];
  
  for (const pattern of whatsappChainIndicators) {
    if (pattern.test(text)) chainCount++;
  }
  
  if (chainCount >= 2) {
    fakeScore += 20;
    reason.push(`⚠️ WhatsApp chain message pattern detected (${chainCount} indicators)`);
  }
  
  // STEP 5: Check for excessive formatting (caps + exclamations)
  const uppercaseChars = (text.match(/[A-Z]/g) || []).length;
  const exclamationCount = (text.match(/!/g) || []).length;
  const totalLength = text.length;
  
  if (totalLength > 0) {
    const uppercaseRatio = uppercaseChars / totalLength;
    if (uppercaseRatio > 0.4) {
      fakeScore += 20;
      reason.push(`⚠️ Excessive capitalization (${Math.round(uppercaseRatio * 100)}% uppercase)`);
    }
    
    if (exclamationCount > 5) {
      fakeScore += 15;
      reason.push(`⚠️ ${exclamationCount} exclamation marks detected`);
    } else if (exclamationCount > 3) {
      fakeScore += 10;
    }
  }
  
  // STEP 6: Check for REAL news indicators (very specific patterns only)
  for (const { pattern, weight, source } of REAL_NEWS_INDICATORS) {
    if (pattern.test(text)) {
      realScore += Math.abs(weight);
      
      // Only add reason for source-based indicators
      if (source && !reason.some(r => r.includes('Verified source'))) {
        reason.push(`✅ Verified source pattern detected`);
      }
    }
  }
  
  // STEP 7: Check for professional news language
  const professionalMarkers = [
    /\b(according to|reports indicate|sources confirm)\b/i,
    /\b(interview|conference|briefing|press release)\b/i,
    /\b(statement|announcement|declaration)\b\s+(issued|released|made available)/i,
  ];
  
  for (const marker of professionalMarkers) {
    if (marker.test(text)) {
      realScore += 10;
    }
  }
  
  // STEP 8: Calculate final score with strong bias against FAKE for WhatsApp scams
  let totalScore = fakeScore - realScore;
  
  // If it's a WhatsApp chain message, force higher score
  if (chainCount >= 3 || criticalFakeDetected) {
    totalScore = Math.max(totalScore, 70); // Minimum 70% fake for chain messages
  }
  
  // Special case: Palliative scams
  if (/₦\d{4,6}\s+PALLIATIVE/i.test(text) && chainCount >= 2) {
    totalScore = Math.max(totalScore, 85); // Force high fake score for palliative scams
  }
  
  // Death hoax bonus
  if (/(president|tinubu|buhari).*dead/i.test(text) && exclamationCount > 2) {
    totalScore = Math.max(totalScore, 80);
  }
  
  // Clamp to 0-100 range
  totalScore = Math.min(95, Math.max(5, totalScore));
  
  // Normalize
  const normalizedScore = Math.round(totalScore);
  
  return {
    score: normalizedScore,
    isFake: normalizedScore > 50,
    fakeScore: Math.round(fakeScore),
    realScore: Math.round(realScore),
    reason: reason.slice(0, 4), // Top 4 reasons
    criticalDetected: criticalFakeDetected,
    chainCount: chainCount,
    exclamationCount: exclamationCount,
    uppercaseRatio: Math.round((uppercaseChars / totalLength) * 100) || 0
  };
}

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
    
    // Calculate pattern score (primary detection)
    const patternAnalysis = calculatePatternScore(textToAnalyze);
    
    // Try ONNX model if available (optional)
    let modelResult = null;
    let finalVerdict = patternAnalysis.isFake ? 'FAKE' : 'REAL';
    let finalConfidence = patternAnalysis.isFake ? patternAnalysis.score : 100 - patternAnalysis.score;
    let modelUsed = 'pattern-enhanced';
    
    try {
      const model = await getOnnxModel();
      if (model && model.isLoaded) {
        modelUsed = 'hybrid-model-pattern';
        modelResult = await model.predict(textToAnalyze);
        
        // Weighted combination: 70% pattern, 30% model (pattern takes precedence for Nigerian scams)
        const patternWeight = 0.7;
        const modelWeight = 0.3;
        
        const patternFakeScore = patternAnalysis.isFake ? patternAnalysis.score / 100 : (100 - patternAnalysis.score) / 100;
        const modelFakeScore = modelResult.probabilities.fake;
        
        // If critical patterns detected, give pattern even more weight
        let finalPatternWeight = patternWeight;
        if (patternAnalysis.criticalDetected || patternAnalysis.chainCount >= 2) {
          finalPatternWeight = 0.85; // 85% pattern, 15% model for clear scams
        }
        
        const combinedFakeScore = (patternFakeScore * finalPatternWeight) + (modelFakeScore * (1 - finalPatternWeight));
        finalVerdict = combinedFakeScore > 0.5 ? 'FAKE' : 'REAL';
        finalConfidence = Math.round(combinedFakeScore * 100);
        
        // Boost confidence for clear scam patterns
        if (patternAnalysis.criticalDetected && finalConfidence < 85) {
          finalConfidence = Math.min(95, finalConfidence + 15);
        }
      }
    } catch (modelError) {
      console.error('ONNX Model error:', modelError.message);
      // Fall back to pattern-only detection
      modelUsed = 'pattern-only';
    }
    
    // Generate detailed explanation
    let explanation = '';
    if (finalVerdict === 'FAKE') {
      if (patternAnalysis.criticalDetected) {
        explanation = '⚠️ This contains classic WhatsApp scam patterns. ';
      } else if (patternAnalysis.chainCount >= 2) {
        explanation = '⚠️ This appears to be a WhatsApp chain message. ';
      }
      
      if (patternAnalysis.reason.length > 0) {
        explanation += patternAnalysis.reason.join(' ').replace(/⚠️/g, '').trim() + ' ';
      } else {
        explanation += 'This content matches patterns commonly found in Nigerian fake news. ';
      }
      
      // Add specific guidance
      if (/palliative|grant|money|payment/i.test(textToAnalyze)) {
        explanation += 'Financial scams promising money are common. Government palliatives are NEVER distributed via WhatsApp forwards. ';
      }
      if (/dead|dies|death|killed/i.test(textToAnalyze)) {
        explanation += 'Death hoaxes are a common type of Nigerian fake news. Always verify with official sources. ';
      }
      if (/share|forward|send to/i.test(textToAnalyze)) {
        explanation += 'Legitimate news never asks you to share to multiple groups. ';
      }
    } else {
      explanation = '✅ This content appears legitimate based on language patterns. ';
      if (patternAnalysis.realScore > 0) {
        explanation += 'Verified source patterns detected. ';
      }
      explanation += 'Always cross-reference with trusted Nigerian news sources like Premium Times, Punch, or Vanguard.';
    }
    
    // Determine confidence level
    let confidenceLevel = 'LOW';
    if (finalConfidence >= 80) confidenceLevel = 'HIGH';
    else if (finalConfidence >= 60) confidenceLevel = 'MEDIUM';
    
    // Prepare response
    const response = {
      classification: finalVerdict,
      confidence: finalConfidence,
      confidenceLevel: confidenceLevel,
      explanation: explanation.trim(),
      model: modelUsed,
      sourceType: sourceType,
      patternDetails: {
        fakeScore: patternAnalysis.fakeScore,
        realScore: patternAnalysis.realScore,
        totalScore: patternAnalysis.score,
        reasons: patternAnalysis.reason,
        criticalDetected: patternAnalysis.criticalDetected,
        chainCount: patternAnalysis.chainCount,
        exclamationCount: patternAnalysis.exclamationCount,
        uppercaseRatio: patternAnalysis.uppercaseRatio
      },
      textPreview: textToAnalyze.length > 200 ? textToAnalyze.substring(0, 200) + '...' : textToAnalyze,
      disclaimer: 'AI analysis based on Nigerian news patterns. Always verify with trusted sources like Premium Times, Punch, Vanguard, or official government channels.',
      tips: finalVerdict === 'FAKE' ? [
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
    
    // Add model results if available
    if (modelResult) {
      response.probabilities = {
        real: Math.round(modelResult.probabilities.real * 100),
        fake: Math.round(modelResult.probabilities.fake * 100)
      };
      response.modelConfidence = modelResult.confidence;
    }
    
    return res.status(200).json(response);
    
  } catch (error) {
    console.error('Analysis error:', error);
    return res.status(500).json({ 
      error: 'Analysis failed. Please try again.',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}