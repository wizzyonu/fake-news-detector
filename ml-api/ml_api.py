import os

import sys

print("=" * 60)
print("STARTUP DEBUG - Checking for model files")
print("=" * 60)
print(f"Current working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")
print(f"Python path: {sys.path}")
print("=" * 60)

import pickle
import joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Store model-vectorizer pairs
MODEL_VECTORIZER_PAIRS = []

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

def load_file(filepath):
    """Try multiple methods to load a pickle/joblib file"""
    # Try joblib first (more robust)
    try:
        return joblib.load(filepath)
    except:
        pass
    
    # Try pickle with different protocols
    for protocol in [None, 2, 3, 4, 5]:
        try:
            with open(filepath, 'rb') as f:
                if protocol is None:
                    return pickle.load(f)
                else:
                    return pickle.loads(f.read())
        except:
            continue
    
    return None

def load_models_with_vectorizers():
    """Load each model with its matching vectorizer"""
    global MODEL_VECTORIZER_PAIRS
    
    # Define model-vectorizer pairs based on filenames
    pairs = [
        ('model_b_balanced.pkl', 'tfidf_vec_balanced.pkl'),
        ('model_b_final_balanced.pkl', 'tfidf_vec_final_balanced.pkl'),
        ('model_b_logreg.pkl', 'tfidf_vectorizer.pkl'),
        ('model_b_multi_source.pkl', 'tfidf_vec_multi_source.pkl'),
        ('model_latest.pkl', 'tfidf_vec_latest.pkl'),
    ]
    
    for model_file, vec_file in pairs:
        try:
            print(f"Loading {model_file}...")
            model = load_file(model_file)
            
            print(f"Loading {vec_file}...")
            vectorizer = load_file(vec_file)
            
            if model is not None and vectorizer is not None:
                if hasattr(model, 'predict') and hasattr(vectorizer, 'transform'):
                    MODEL_VECTORIZER_PAIRS.append({
                        'name': model_file.replace('.pkl', ''),
                        'model': model,
                        'vectorizer': vectorizer
                    })
                    print(f"✅ Loaded pair: {model_file} + {vec_file}")
                else:
                    print(f"❌ Invalid objects: model has predict={hasattr(model, 'predict')}, vectorizer has transform={hasattr(vectorizer, 'transform')}")
            else:
                print(f"❌ Failed to load: model={model is not None}, vectorizer={vectorizer is not None}")
        except Exception as e:
            print(f"❌ Error loading pair {model_file}: {e}")
    
    return len(MODEL_VECTORIZER_PAIRS) > 0

def get_ensemble_prediction(text):
    """Get predictions from all model-vectorizer pairs"""
    if not MODEL_VECTORIZER_PAIRS:
        return None, None, []
    
    predictions = []
    
    for pair in MODEL_VECTORIZER_PAIRS:
        try:
            # Transform text using this model's specific vectorizer
            X = pair['vectorizer'].transform([text])
            
            # Get prediction
            pred = pair['model'].predict(X)[0]
            
            # Get confidence if available
            confidence = 50.0
            if hasattr(pair['model'], 'predict_proba'):
                proba = pair['model'].predict_proba(X)[0]
                confidence = float(max(proba) * 100)
            
            # Determine if prediction is FAKE
            is_fake = False
            if hasattr(pair['model'], 'classes_'):
                classes = pair['model'].classes_
                if len(classes) == 2:
                    # Convert to string for comparison
                    class_str = str(classes[0]).upper()
                    if class_str in ['FAKE', '1', 'FALSE']:
                        is_fake = bool(pred == classes[0])
                    else:
                        is_fake = bool(pred == classes[1])
                else:
                    pred_str = str(pred).upper()
                    is_fake = pred_str in ['FAKE', '1', 'FALSE']
            else:
                pred_str = str(pred).upper()
                is_fake = pred_str in ['FAKE', '1', 'FALSE']
            
            predictions.append({
                'name': pair['name'],
                'is_fake': is_fake,
                'confidence': confidence
            })
            print(f"  {pair['name']}: {'FAKE' if is_fake else 'REAL'} (conf: {confidence:.1f}%)")
        except Exception as e:
            print(f"Error with {pair['name']}: {e}")
    
    if not predictions:
        return None, None, []
    
    # Ensemble voting
    fake_votes = sum(1 for p in predictions if p['is_fake'])
    total_models = len(predictions)
    is_fake = fake_votes > total_models / 2
    
    # Average confidence of models that agree
    agreeing_confidences = [p['confidence'] for p in predictions if p['is_fake'] == is_fake]
    avg_confidence = sum(agreeing_confidences) / len(agreeing_confidences) if agreeing_confidences else 50.0
    
    return bool(is_fake), float(avg_confidence), predictions

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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(MODEL_VECTORIZER_PAIRS),
        'models_list': [p['name'] for p in MODEL_VECTORIZER_PAIRS]
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    text = data.get('text', '')
    
    if not text or len(text) < 20:
        return jsonify({'error': 'Text too short (minimum 20 characters)'}), 400
    
    # Get ensemble predictions
    ml_is_fake, ml_confidence, model_predictions = get_ensemble_prediction(text)
    
    # Get pattern score
    pattern_score = calculate_pattern_score(text)
    pattern_is_fake = pattern_score > 50
    pattern_confidence = pattern_score if pattern_is_fake else 100 - pattern_score
    
    # Combine: 70% ML, 30% pattern
    if ml_is_fake is not None:
        combined_is_fake = bool(ml_is_fake)
        if ml_is_fake and pattern_is_fake:
            combined_confidence = (ml_confidence * 0.7) + (pattern_confidence * 0.3)
        elif ml_is_fake:
            combined_confidence = (ml_confidence * 0.6) + (pattern_confidence * 0.4)
        else:
            combined_confidence = (ml_confidence * 0.5) + (pattern_confidence * 0.5)
        
        model_used = 'ensemble'
    else:
        combined_is_fake = pattern_is_fake
        combined_confidence = pattern_confidence
        model_used = 'pattern-only-fallback'
    
    # Death hoax override
    if re.search(r'(president|tinubu|buhari).{0,30}dead', text, re.IGNORECASE):
        combined_is_fake = True
        combined_confidence = max(combined_confidence, 85)
    
    # Convert model predictions to JSON-serializable format
    serializable_predictions = []
    for p in model_predictions:
        serializable_predictions.append({
            'name': str(p['name']),
            'is_fake': bool(p['is_fake']),
            'confidence': float(p['confidence'])
        })
    
    return jsonify({
        'classification': 'FAKE' if combined_is_fake else 'REAL',
        'confidence': round(float(combined_confidence), 1),
        'pattern_score': int(pattern_score),
        'ml_available': ml_is_fake is not None,
        'ml_confidence': round(float(ml_confidence), 1) if ml_is_fake is not None else None,
        'model_used': str(model_used),
        'models_loaded': [str(p['name']) for p in MODEL_VECTORIZER_PAIRS],
        'model_votes': serializable_predictions
    })

@app.route('/model-info', methods=['GET'])
def model_info():
    """Detailed information about loaded models"""
    info = {}
    for pair in MODEL_VECTORIZER_PAIRS:
        model = pair['model']
        vectorizer = pair['vectorizer']
        info[pair['name']] = {
            'model_type': str(type(model).__name__),
            'has_predict_proba': hasattr(model, 'predict_proba'),
            'vectorizer_type': str(type(vectorizer).__name__),
            'feature_count': len(vectorizer.get_feature_names_out()) if hasattr(vectorizer, 'get_feature_names_out') else 'unknown'
        }
    return jsonify({
        'models': info,
        'total_models': len(MODEL_VECTORIZER_PAIRS)
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Loading ML models with their vectorizers...")
    print("=" * 50)
    
    if load_models_with_vectorizers():
        print(f"\n✅ Loaded {len(MODEL_VECTORIZER_PAIRS)} model-vectorizer pairs")
        for pair in MODEL_VECTORIZER_PAIRS:
            print(f"   - {pair['name']}")
    else:
        print("\n⚠️ No models loaded. Will fall back to pattern detection.")
    
    print("\n" + "=" * 50)
    print("Starting Flask API server...")
    print("=" * 50)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)