// src/pages/api/analyze.js
// ONNX IS COMMENTED OUT - Pattern detection only (Works on Vercel!)

// ============================================
// ONNX IS DISABLED FOR VERCEL COMPATIBILITY
// ============================================
// import { getOnnxModel } from '../../../lib/onnxModel.js';
// axios and cheerio ARE kept for URL scraping functionality
import axios from 'axios';
import * as cheerio from 'cheerio';

// ============================================
// ENHANCED NIGERIAN FAKE NEWS PATTERNS (FULLY UPDATED)
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
  
  // Political manipulation patterns
  { pattern: /EXPOSED!!!+\s+(INEC|PDP|APC|TINUBU|ATIKU|BUHARI)/i, weight: 50, critical: true },
  { pattern: /CAUGHT\s+(WITH|RED-HANDED|ON\s+CAMERA)/i, weight: 45, critical: true },
  { pattern: /PRE-TICKETED\s+BALLOT/i, weight: 45, critical: true },
  { pattern: /RIGGING\s+(PLAN|PLOT|SCHEME|ALLEGATIONS)/i, weight: 40, critical: true },
  
  // DEATH HOAX - CRITICAL PATTERNS
  { pattern: /(president|tinubu|buhari|gov|governor)\s+is\s+dead/i, weight: 60, critical: true },
  { pattern: /^.*(president|tinubu|buhari).{0,20}dead/i, weight: 55, critical: true },
  { pattern: /\b(DEAD|DIES|DIED)\b.*president/i, weight: 55, critical: true },
  { pattern: /president.*\bDEAD\b/i, weight: 60, critical: true },
];

// Nigerian-specific fake news patterns
const NIGERIAN_FAKE_PATTERNS = [
  // ENHANCED DEATH HOAX PATTERNS
  { pattern: /president\s+is\s+dead/i, weight: 60 },
  { pattern: /tinubu\s+is\s+dead/i, weight: 60 },
  { pattern: /buhari\s+is\s+dead/i, weight: 60 },
  { pattern: /^.{0,50}(dead|dies|died).{0,50}$/i, weight: 45 },
  { pattern: /\bDEAD\b.*president/i, weight: 55 },
  { pattern: /president.*\bDEAD\b/i, weight: 55 },
  { pattern: /dies suddenly|found dead|confirmed dead/i, weight: 40 },
  { pattern: /killed in accident|dies in hospital/i, weight: 35 },
  
  // Viral sharing prompts
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
  { pattern: /EXPOSED!!!+/i, weight: 35 },
  { pattern: /[!]{4,}/, weight: 20 },
  { pattern: /[!]{3,}/, weight: 15 },
  
  // Suspicious urgency
  { pattern: /HURRY\s+BEFORE/i, weight: 30 },
  { pattern: /LAST\s+CHANCE/i, weight: 30 },
  { pattern: /EXPIRES\s+SOON/i, weight: 25 },
  
  // Political manipulation
  { pattern: /CAUGHT\s+ON\s+CAMERA/i, weight: 35 },
  { pattern: /BALLOT\s+BOX\s+(SNATCHING|STUFFING)/i, weight: 30 },
  { pattern: /ELECTION\s+(FRAUD|MANIPULATION)/i, weight: 30 },
  { pattern: /VOTE\s+(BUYING|SELLING)/i, weight: 25 },
];

// Real news indicators (NEGATIVE weights - very specific patterns only)
const REAL_NEWS_INDICATORS = [
  // Verified Nigerian news sources
  { pattern: /premium\s+times\s+reports?/i, weight: -30, source: true },
  { pattern: /punch\s+newspaper/i, weight: -30, source: true },
  { pattern: /vanguard\s+ng/i, weight: -25, source: true },
  { pattern: /guardian\.ng/i, weight: -25, source: true },
  { pattern: /according\s+to\s+(premium|punch|vanguard|guardian)/i, weight: -25, source: true },
  
  // Official government communication (SPECIFIC patterns only)
  { pattern: /cbn\s+governor\s+(\w+)\s+(said|announced|confirmed)/i, weight: -20 },
  { pattern: /ncdc\s+has\s+confirmed\s+\d+\s+new\s+cases/i, weight: -20 },
  { pattern: /inec\s+spokesperson\s+(\w+)\s+(said|confirmed|announced)/i, weight: -25 },
  { pattern: /in\s+a\s+statement\s+(signed|issued)\s+by/i, weight: -20 },
  { pattern: /spokesperson\s+(\w+)\s+said/i, weight: -20 },
  
  // Date-specific legitimate news
  { pattern: /(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},\s+202[4-5]/i, weight: -15 },
  
  // Official event markers
  { pattern: /at\s+the\s+(presidential\s+villa|national\s+assembly|state\s+house)/i, weight: -15 },
  
  // Professional journalistic language
  { pattern: /in\s+an\s+interview\s+with/i, weight: -15 },
  { pattern: /reports\s+that/i, weight: -12 },
  { pattern: /confirmed\s+to\s+([A-Z]+)\s+newspaper/i, weight: -15 },
];

// ============================================
// DEATH HOAX DETECTION FUNCTION
// ============================================

function detectDeathHoax(text) {
  const textLower = text.toLowerCase();
  const textLength = text.length;
  
  // Death keywords
  const deathKeywords = ['dead', 'dies', 'died', 'death', 'killed', 'assassinated'];
  const hasDeathWord = deathKeywords.some(kw => textLower.includes(kw));
  
  if (!hasDeathWord) return { isDeathHoax: false, score: 0, reasons: [] };
  
  // Nigerian leaders
  const leaders = ['tinubu', 'buhari', 'jonathan', 'obasanjo', 'president', 'gov', 'governor'];
  const hasLeader = leaders.some(leader => textLower.includes(leader));
  
  let score = 0;
  let reasons = [];
  
  // VERY SHORT text + death + leader = almost certainly fake
  if (textLength < 100 && hasDeathWord && hasLeader) {
    score = 75;
    reasons.push("⚠️ Extremely short death announcement (typical hoax pattern)");
  }
  
  // Direct "X is dead" pattern
  if (/president\s+is\s+dead/i.test(text) || /tinubu\s+is\s+dead/i.test(text)) {
    score = 85;
    reasons.push("⚠️ Direct 'President is dead' claim - common Nigerian death hoax");
  }
  
  // No source attribution
  if (!/according to|reports|sources|confirmed|announced/i.test(text)) {
    score += 15;
    reasons.push("⚠️ No source attribution - suspicious for death news");
  }
  
  // No official language
  if (!/spokesperson|palace|aides|family|hospital/i.test(text)) {
    score += 10;
    reasons.push("⚠️ Lacks official confirmation language");
  }
  
  // Check for ALL CAPS death (classic)
  if (/DEAD|DIES|DIED/.test(text) && text === text.toUpperCase()) {
    score += 20;
    reasons.push("⚠️ ALL CAPS death announcement (viral hoax pattern)");
  }
  
  return {
    isDeathHoax: score > 50,
    score: Math.min(score, 95),
    reasons: reasons.slice(0, 3)
  };
}

// ============================================
// MAIN PATTERN SCORE CALCULATION
// ============================================

function calculatePatternScore(text) {
  // STEP 1: Death hoax detection (highest priority)
  const deathHoaxAnalysis = detectDeathHoax(text);
  
  let fakeScore = deathHoaxAnalysis.score;
  let realScore = 0;
  let reason = [...deathHoaxAnalysis.reasons];
  let criticalFakeDetected = deathHoaxAnalysis.isDeathHoax;
  let chainCount = 0;
  
  // If death hoax detected, set minimum score
  if (deathHoaxAnalysis.isDeathHoax) {
    fakeScore = Math.max(fakeScore, 70);
    if (!reason.includes("🚨 DEATH HOAX DETECTED")) {
      reason.unshift("🚨 DEATH HOAX DETECTED");
    }
  }
  
  // STEP 2: Check ABSOLUTE fake indicators
  for (const { pattern, weight, critical } of ABSOLUTE_FAKE_INDICATORS) {
    if (pattern.test(text)) {
      fakeScore += weight;
      criticalFakeDetected = true;
      if (!reason.some(r => r.includes(pattern.source.slice(0, 30)))) {
        reason.push(`🚨 CRITICAL: ${pattern.source.slice(0, 50)}... detected`);
      }
      break;
    }
  }
  
  // STEP 3: Boost for critical patterns
  if (criticalFakeDetected) {
    fakeScore += 30;
    if (!reason.includes("⚠️ Contains classic scam patterns")) {
      reason.push("⚠️ Contains classic scam patterns");
    }
  }
  
  // STEP 4: Check Nigerian-specific fake patterns
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
  
  // STEP 5: WhatsApp chain detection
  const whatsappChainIndicators = [
    /SHARE.*GROUPS/i, /WITHIN.*MINUTES/i, /FAILURE.*SHARE/i,
    /FORWARD.*NOW/i, /SEND.*CONTACTS/i, /SHARE.*THIS.*MESSAGE/i
  ];
  
  for (const pattern of whatsappChainIndicators) {
    if (pattern.test(text)) chainCount++;
  }
  
  if (chainCount >= 2) {
    fakeScore += 20;
    reason.push(`⚠️ WhatsApp chain message pattern detected (${chainCount} indicators)`);
  }
  
  // STEP 6: Check formatting (caps + exclamations)
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
  
  // STEP 7: Check REAL news indicators
  for (const { pattern, weight, source } of REAL_NEWS_INDICATORS) {
    if (pattern.test(text)) {
      realScore += Math.abs(weight);
      if (source && !reason.some(r => r.includes('Verified source'))) {
        reason.push(`✅ Verified source pattern detected`);
      }
    }
  }
  
  // STEP 8: Calculate final score with forced minimums
  let totalScore = fakeScore - realScore;
  
  // Force high scores for certain patterns
  if (chainCount >= 3 || criticalFakeDetected) {
    totalScore = Math.max(totalScore, 70);
  }
  
  if (/₦\d{4,6}\s+PALLIATIVE/i.test(text) && chainCount >= 2) {
    totalScore = Math.max(totalScore, 85);
  }
  
  if (/(president|tinubu|buhari).{0,30}dead/i.test(text)) {
    totalScore = Math.max(totalScore, 80);
  }
  
  if (/EXPOSED|CAUGHT|RIGGING|PRE-TICKETED/i.test(text)) {
    totalScore = Math.max(totalScore, 75);
  }
  
  // Death hoax special handling
  if (deathHoaxAnalysis.isDeathHoax) {
    totalScore = Math.max(totalScore, 85);
  }
  
  // Clamp to 0-100
  totalScore = Math.min(95, Math.max(5, totalScore));
  
  return {
    score: Math.round(totalScore),
    isFake: totalScore > 50,
    fakeScore: Math.round(fakeScore),
    realScore: Math.round(realScore),
    reason: reason.slice(0, 5),
    criticalDetected: criticalFakeDetected,
    chainCount: chainCount,
    exclamationCount: exclamationCount,
    uppercaseRatio: Math.round((uppercaseChars / totalLength) * 100) || 0,
    isDeathHoax: deathHoaxAnalysis.isDeathHoax
  };
}

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
    
    // Calculate pattern score
    const patternAnalysis = calculatePatternScore(textToAnalyze);
    
    // ============================================
    // ONNX MODEL IS COMPLETELY DISABLED
    // Pattern detection only - works perfectly on Vercel!
    // ============================================
    let finalVerdict = patternAnalysis.isFake ? 'FAKE' : 'REAL';
    let finalConfidence = patternAnalysis.isFake ? patternAnalysis.score : 100 - patternAnalysis.score;
    let modelUsed = 'pattern-detection';
    
    // Special handling for death hoaxes (override anything else)
    if (/(president|tinubu|buhari|governor).{0,30}dead/i.test(textToAnalyze)) {
      finalVerdict = 'FAKE';
      finalConfidence = Math.max(finalConfidence, 88);
    }
    
    // Handle low confidence edge cases
    if (finalConfidence >= 45 && finalConfidence <= 55) {
      if (/EXPOSED|CAUGHT|RIGGING|PRE-TICKETED/i.test(textToAnalyze)) {
        finalVerdict = 'FAKE';
        finalConfidence = Math.max(finalConfidence, 75);
      }
    }
    
    // Generate explanation
    let explanation = '';
    if (finalVerdict === 'FAKE') {
      if (patternAnalysis.isDeathHoax) {
        explanation = '🚨 DEATH HOAX DETECTED: This appears to be a false death announcement. ';
      } else if (patternAnalysis.criticalDetected) {
        explanation = '⚠️ This contains classic scam patterns. ';
      } else if (patternAnalysis.chainCount >= 2) {
        explanation = '⚠️ This appears to be a WhatsApp chain message. ';
      }
      
      if (patternAnalysis.reason.length > 0) {
        explanation += patternAnalysis.reason.join(' ').replace(/⚠️|🚨/g, '').trim() + ' ';
      } else {
        explanation += 'This content matches patterns commonly found in Nigerian fake news. ';
      }
      
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
      explanation += 'Always cross-reference with trusted Nigerian news sources.';
    }
    
    let confidenceLevel = 'LOW';
    if (finalConfidence >= 80) confidenceLevel = 'HIGH';
    else if (finalConfidence >= 60) confidenceLevel = 'MEDIUM';
    
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
        uppercaseRatio: patternAnalysis.uppercaseRatio,
        isDeathHoax: patternAnalysis.isDeathHoax
      },
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
    
    return res.status(200).json(response);
    
  } catch (error) {
    console.error('Analysis error:', error);
    return res.status(500).json({ 
      error: 'Analysis failed. Please try again.',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}