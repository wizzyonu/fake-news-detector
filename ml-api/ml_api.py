import os
import pickle
import joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import re

app = Flask(__name__)
CORS(app)

# Global variables for models
MODELS = {}
VECTORIZER = None

# Nigerian fake news patterns
ABSOLUTE_FAKE_INDICATORS = [
    (r'SHARE\s+(THIS|TO)\s+\d+\s+WHATSAPP\s+GROUPS', 50),
    (r'FORWARD\s+THIS\s+MESSAGE\s+TO\s+\d+\s+(GROUPS|CONTACTS)', 50),
    (r'WITHIN\s+\d+\s+MINUTES', 45),
    (r'FAILURE\s+TO\s+SHARE', 45),
    (r'₦\d{4,6}\s+PALLIATIVE', 40),
    (r'EXPOSED!!!+\s+(INEC|PDP|APC|TINUBU|ATIKU|BUHARI)', 50),
    (r'PRE-TICKETED\s+BALLOT', 45),
    (r'(president|tinubu|buhari|gov|governor)\s+is\s+dead', 60),
]

def load_models():
    """Load all .pkl models from the current directory"""
    global MODELS, VECTORIZER
    
    # List all .pkl files in current directory
    pkl_files = [f for f in os.listdir('.') if f.endswith('.pkl')]
    print(f"Found .pkl files: {pkl_files}")
    
    # Try to load each model file
    for file in pkl_files:
        try:
            # Try pickle first
            with open(file, 'rb') as f:
                model = pickle.load(f)
                # Check if it's a classifier (has predict method)
                if hasattr(model, 'predict'):
                    name = file.replace('.pkl', '')
                    MODELS[name] = model
                    print(f"✅ Loaded model: {name}")
        except:
            try:
                # Try joblib
                model = joblib.load(file)
                if hasattr(model, 'predict'):
                    name = file.replace('.pkl', '')
                    MODELS[name] = model
                    print(f"✅ Loaded model with joblib: {name}")
            except Exception as e:
                print(f"❌ Failed to load {file}: {e}")
    
    # Try to identify vectorizer (TfidfVectorizer)
    for file in pkl_files:
        if 'tfidf' in file.lower() or 'vectorizer' in file.lower() or 'vec' in file.lower():
            try:
                with open(file, 'rb') as f:
                    obj = pickle.load(f)
                    if isinstance(obj, TfidfVectorizer) or hasattr(obj, 'transform'):
                        VECTORIZER = obj
                        print(f"✅ Loaded vectorizer: {file}")
                        break
            except:
                try:
                    obj = joblib.load(file)
                    if isinstance(obj, TfidfVectorizer) or hasattr(obj, 'transform'):
                        VECTORIZER = obj
                        print(f"✅ Loaded vectorizer with joblib: {file}")
                        break
                except:
                    pass
    
    return len(MODELS) > 0

def calculate_pattern_score(text):
    """Calculate pattern-based score"""
    text_lower = text.lower()
    fake_score = 0
    
    # Death hoax detection
    if re.search(r'(president|tinubu|buhari|gov|governor).{0,30}dead', text_lower):
        fake_score += 50
    
    # Check absolute indicators
    for pattern, weight in ABSOLUTE_FAKE_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            fake_score += weight
            break
    
    # WhatsApp chain detection
    chain_patterns = [r'share.*groups', r'within.*minutes', r'failure.*share', r'forward.*now']
    chain_count = sum(1 for p in chain_patterns if re.search(p, text_lower))
    if chain_count >= 2:
        fake_score += 20
    
    # Exclamation marks
    exclamation_count = text.count('!')
    if exclamation_count > 5:
        fake_score += 15
    elif exclamation_count > 3:
        fake_score += 10
    
    # Uppercase ratio
    uppercase_chars = sum(1 for c in text if c.isupper())
    total_chars = len(text)
    if total_chars > 0:
        uppercase_ratio = uppercase_chars / total_chars
        if uppercase_ratio > 0.4:
            fake_score += 20
    
    # Real news indicators
    real_indicators = [
        r'premium\s+times\s+reports?',
        r'punch\s+newspaper',
        r'vanguard\s+ng',
        r'according\s+to\s+(premium|punch|vanguard|guardian)',
        r'spokesperson\s+\w+\s+said',
    ]
    
    real_score = 0
    for pattern in real_indicators:
        if re.search(pattern, text_lower):
            real_score += 25
    
    total = fake_score - real_score
    return min(95, max(5, total))

def get_ml_prediction(text):
    """Get prediction from ML models"""
    if not VECTORIZER or not MODELS:
        return None, None
    
    try:
        # Transform text using vectorizer
        X = VECTORIZER.transform([text])
        
        # Get predictions from all models
        predictions = {}
        for name, model in MODELS.items():
            try:
                pred = model.predict(X)[0]
                
                # Try to get probability
                proba = None
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(X)[0]
                elif hasattr(model, 'decision_function'):
                    # For SVM style models
                    decision = model.decision_function(X)[0]
                    proba = [1/(1+np.exp(-decision)), 1/(1+np.exp(decision))]
                
                # Determine if prediction is FAKE
                is_fake = False
                confidence = 50
                
                if hasattr(model, 'classes_'):
                    classes = model.classes_
                    if len(classes) == 2:
                        # Binary classification
                        if classes[0] in ['FAKE', 1, 'fake', 'Fake']:
                            is_fake = (pred == classes[0])
                            if proba is not None:
                                confidence = max(proba) * 100
                        else:
                            is_fake = (pred == classes[1])
                            if proba is not None:
                                confidence = max(proba) * 100
                    else:
                        is_fake = (pred in ['FAKE', 'fake', 1, 'Fake'])
                else:
                    is_fake = (pred in ['FAKE', 'fake', 1, 'Fake'])
                
                predictions[name] = {
                    'prediction': pred,
                    'is_fake': is_fake,
                    'confidence': confidence if proba is not None else (70 if is_fake else 30)
                }
            except Exception as e:
                print(f"Error with model {name}: {e}")
        
        if not predictions:
            return None, None
        
        # Ensemble vote
        fake_votes = sum(1 for p in predictions.values() if p.get('is_fake', False))
        total_models = len(predictions)
        is_fake = fake_votes > total_models / 2
        
        # Average confidence
        confidences = [p.get('confidence', 50) for p in predictions.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else (70 if is_fake else 30)
        
        return is_fake, avg_confidence
        
    except Exception as e:
        print(f"ML prediction error: {e}")
        return None, None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(MODELS),
        'vectorizer_loaded': VECTORIZER is not None,
        'models_list': list(MODELS.keys())
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    text = data.get('text', '')
    
    if not text or len(text) < 20:
        return jsonify({'error': 'Text too short (minimum 20 characters)'}), 400
    
    # Get ML prediction
    ml_is_fake, ml_confidence = get_ml_prediction(text)
    
    # Get pattern score
    pattern_score = calculate_pattern_score(text)
    pattern_is_fake = pattern_score > 50
    pattern_confidence = pattern_score if pattern_is_fake else 100 - pattern_score
    
    # Combine: 70% ML, 30% pattern
    if ml_is_fake is not None:
        combined_is_fake = ml_is_fake
        if ml_is_fake and pattern_is_fake:
            combined_confidence = (ml_confidence * 0.7) + (pattern_confidence * 0.3)
        elif ml_is_fake:
            combined_confidence = (ml_confidence * 0.6) + (pattern_confidence * 0.4)
        else:
            combined_confidence = (ml_confidence * 0.5) + (pattern_confidence * 0.5)
        
        model_used = 'ensemble'
    else:
        # Fallback to pattern only
        combined_is_fake = pattern_is_fake
        combined_confidence = pattern_confidence
        model_used = 'pattern-only-fallback'
    
    # Death hoax override
    if re.search(r'(president|tinubu|buhari).{0,30}dead', text, re.IGNORECASE):
        combined_is_fake = True
        combined_confidence = max(combined_confidence, 85)
    
    return jsonify({
        'classification': 'FAKE' if combined_is_fake else 'REAL',
        'confidence': round(combined_confidence, 1),
        'pattern_score': pattern_score,
        'ml_available': ml_is_fake is not None,
        'ml_prediction': 'FAKE' if ml_is_fake else 'REAL' if ml_is_fake is not None else None,
        'ml_confidence': ml_confidence if ml_is_fake is not None else None,
        'model_used': model_used,
        'models_loaded': list(MODELS.keys())
    })

@app.route('/model-info', methods=['GET'])
def model_info():
    info = {}
    for name, model in MODELS.items():
        info[name] = {
            'type': str(type(model).__name__),
            'has_predict_proba': hasattr(model, 'predict_proba')
        }
    return jsonify({
        'models': info,
        'vectorizer_type': str(type(VECTORIZER)) if VECTORIZER else None,
        'vectorizer_loaded': VECTORIZER is not None
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Loading ML models...")
    print("=" * 50)
    
    if load_models():
        print(f"\n✅ Loaded {len(MODELS)} models successfully")
        print(f"✅ Vectorizer loaded: {VECTORIZER is not None}")
        print(f"📦 Models: {list(MODELS.keys())}")
    else:
        print("\n⚠️ No models loaded. Will fall back to pattern detection.")
    
    print("\n" + "=" * 50)
    print("Starting Flask API server...")
    print("=" * 50)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)