// lib/onnxModel.js
import * as ort from 'onnxruntime-node';
import { getTfidfVectorizer } from './tfidf.js';
import fs from 'fs';
import path from 'path';

class OnnxModelLoader {
  constructor() {
    this.session = null;
    this.modelName = 'final_balanced';
    this.isLoaded = false;
    this.tfidf = null;
  }
  
  async loadModel(modelName = 'final_balanced') {
    if (this.isLoaded && this.modelName === modelName) {
      return this.session;
    }
    
    this.modelName = modelName;
    const modelPath = path.join(process.cwd(), 'public', 'models', `model_${modelName}.onnx`);
    
    // Check if model exists
    if (!fs.existsSync(modelPath)) {
      console.error(`Model not found: ${modelPath}`);
      return null;
    }
    
    try {
      console.log(`Loading ONNX model: ${modelName}`);
      this.session = await ort.InferenceSession.create(modelPath);
      this.isLoaded = true;
      this.tfidf = getTfidfVectorizer();
      
      console.log(`✅ Model loaded successfully`);
      console.log(`   Inputs: ${this.session.inputNames}`);
      console.log(`   Outputs: ${this.session.outputNames}`);
      
      return this.session;
    } catch (error) {
      console.error(`Failed to load ONNX model: ${error}`);
      return null;
    }
  }
  
  async predict(text, metadata = {}) {
    if (!this.isLoaded) {
      await this.loadModel();
    }
    
    if (!this.session) {
      throw new Error('Model not loaded');
    }
    
    try {
      // Transform text using TF-IDF
      const features = this.tfidf.transform(text);
      
      // Convert to Float32Array for ONNX
      const inputData = new Float32Array(features);
      
      // Create input tensor
      const tensor = new ort.Tensor('float32', inputData, [1, features.length]);
      
      // Run inference
      const feeds = { 'float_input': tensor };
      const results = await this.session.run(feeds);
      
      // Get output (logits or probabilities)
      const output = results[this.session.outputNames[0]];
      const probabilities = this.softmax(output.data);
      
      // Determine prediction
      const prediction = probabilities[1] > 0.5 ? 'FAKE' : 'REAL';
      const confidence = Math.max(...probabilities) * 100;
      
      return {
        prediction,
        confidence: Math.round(confidence),
        probabilities: {
          real: probabilities[0],
          fake: probabilities[1]
        },
        metadata
      };
      
    } catch (error) {
      console.error(`Prediction error: ${error}`);
      throw error;
    }
  }
  
  async predictBatch(texts) {
    if (!this.isLoaded) {
      await this.loadModel();
    }
    
    const results = [];
    for (const text of texts) {
      const result = await this.predict(text);
      results.push(result);
    }
    return results;
  }
  
  softmax(arr) {
    const max = Math.max(...arr);
    const exp = arr.map(x => Math.exp(x - max));
    const sum = exp.reduce((a, b) => a + b, 0);
    return exp.map(x => x / sum);
  }
  
  getStatus() {
    return {
      isLoaded: this.isLoaded,
      modelName: this.modelName,
      vocabularySize: this.tfidf?.getVocabularySize() || 0
    };
  }
}

// Singleton instance
let modelInstance = null;

export async function getOnnxModel() {
  if (!modelInstance) {
    modelInstance = new OnnxModelLoader();
    await modelInstance.loadModel('final_balanced'); // Use your best model
  }
  return modelInstance;
}

export default OnnxModelLoader;