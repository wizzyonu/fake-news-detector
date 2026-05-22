// lib/tfidf.js
import vocabularyData from '../public/models/vocabulary.json' assert { type: 'json' };
import tfidfParams from '../public/models/tfidf_params.json' assert { type: 'json' };

class TfidfVectorizer {
  constructor() {
    this.vocabulary = vocabularyData;
    this.params = tfidfParams;
    this.idf = null; // Will be loaded from model or computed
    this.featureCount = Object.keys(this.vocabulary).length;
    
    console.log(`TF-IDF Vectorizer initialized with ${this.featureCount} features`);
  }
  
  // Tokenize text (matching sklearn's pattern)
  tokenize(text) {
    // Match words of at least 2 characters (sklearn's default: \b\w\w+\b)
    const matches = text.toLowerCase().match(/\b\w\w+\b/g);
    return matches || [];
  }
  
  // Compute term frequency
  computeTF(tokens) {
    const tf = {};
    for (const token of tokens) {
      tf[token] = (tf[token] || 0) + 1;
    }
    return tf;
  }
  
  // Compute term frequency (normalized by document length)
  computeTFNormalized(tokens) {
    const tf = {};
    const tokenCount = tokens.length;
    for (const token of tokens) {
      tf[token] = (tf[token] || 0) + 1;
    }
    // Normalize by document length
    for (const token in tf) {
      tf[token] = tf[token] / tokenCount;
    }
    return tf;
  }
  
  // Compute TF-IDF features (matching sklearn's output)
  transform(text) {
    const tokens = this.tokenize(text);
    const tf = this.computeTF(tokens);
    
    // Create feature vector (sparse representation)
    const features = new Array(this.featureCount).fill(0);
    
    // For each word in vocabulary, set TF value
    for (const [word, idx] of Object.entries(this.vocabulary)) {
      if (tf[word]) {
        // Use raw TF (or normalized if preferred)
        features[idx] = tf[word];
      }
    }
    
    // Optional: Apply sublinear TF (log(1 + tf))
    if (this.params.sublinear_tf) {
      for (let i = 0; i < features.length; i++) {
        if (features[i] > 0) {
          features[i] = Math.log(1 + features[i]);
        }
      }
    }
    
    return features;
  }
  
  // Transform multiple texts
  transformBatch(texts) {
    return texts.map(text => this.transform(text));
  }
  
  // Get feature names (for debugging)
  getFeatureNames() {
    return Object.keys(this.vocabulary);
  }
  
  // Get vocabulary size
  getVocabularySize() {
    return this.featureCount;
  }
}

// Singleton instance
let instance = null;

export function getTfidfVectorizer() {
  if (!instance) {
    instance = new TfidfVectorizer();
  }
  return instance;
}

export default TfidfVectorizer;