import sys
import os
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

# Rest of your code remains the same...
# ============================================
# STARTUP DEBUG - Check files at runtime
# ============================================
print("=" * 60)
print("STARTUP DEBUG - Checking for model files")
print("=" * 60)
print(f"Current working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")
print(f"Python version: {sys.version}")
try:
    import numpy as np
    print(f"Numpy version: {np.__version__}")
except:
    print("Numpy version: Not found")
print("=" * 60)

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

# ============================================
# MODEL LOADING WITH FIXES
# ============================================

def load_models_with_vectorizers():
    """Load each model with its matching vectorizer"""
    global MODEL_VECTORIZER_PAIRS
    
    print("\nInside load_models_with_vectorizers function")
    
    # Define model-vectorizer pairs
    pairs = [
        ('model_b_balanced.pkl', 'tfidf_vec_balanced.pkl'),
        ('model_b_final_balanced.pkl', 'tfidf_vec_final_balanced.pkl'),
        ('model_b_logreg.pkl', 'tfidf_vectorizer.pkl'),
        ('model_b_multi_source.pkl', 'tfidf_vec_multi_source.pkl'),
        ('model_latest.pkl', 'tfidf_vec_latest.pkl'),
    ]
    
    print(f"Will try to load {len(pairs)} model pairs")
    
    for model_file, vec_file in pairs:
        try:
            print(f"\n--- Processing pair: {model_file} + {vec_file} ---")
            
            # Load model
            print(f"  Loading {model_file}...")
            model = None
            
            if os.path.exists(model_file):
                file_size = os.path.getsize(model_file)
                print(f"    File exists, size: {file_size} bytes")
                
                # Try pickle first
                try:
                    with open(model_file, 'rb') as f:
                        model = pickle.load(f)
                    print(f"    ✅ Loaded with pickle")
                except Exception as pickle_error:
                    print(f"    Pickle failed: {pickle_error}")
                    # Try joblib
                    try:
                        model = joblib.load(model_file)
                        print(f"    ✅ Loaded with joblib")
                    except Exception as joblib_error:
                        print(f"    Joblib also failed: {joblib_error}")
                        continue
            else:
                print(f"    ❌ File does not exist!")
                continue
            
            # Load vectorizer with special handling for numpy version
            print(f"  Loading {vec_file}...")
            vectorizer = None
            
            if os.path.exists(vec_file):
                try:
                    # Try pickle first
                    with open(vec_file, 'rb') as f:
                        vectorizer = pickle.load(f)
                    print(f"    ✅ Loaded with pickle")
                except Exception as e1:
                    print(f"    Pickle failed: {e1}")
                    try:
                        # Try joblib
                        vectorizer = joblib.load(vec_file)
                        print(f"    ✅ Loaded with joblib")
                    except Exception as e2:
                        print(f"    Joblib failed: {e2}")
                        
                        # Last resort: try loading with explicit protocol handling
                        try:
                            import io
                            with open(vec_file, 'rb') as f:
                                # Try reading as bytes and loading with different protocol
                                data_bytes = f.read()
                                # Try different pickle protocols
                                for protocol in [2, 3, 4, 5]:
                                    try:
                                        vectorizer = pickle.loads(data_bytes)
                                        print(f"    ✅ Loaded with pickle protocol {protocol}")
                                        break
                                    except:
                                        continue
                        except Exception as e3:
                            print(f"    All loading methods failed: {e3}")
                            continue
            else:
                print(f"    ❌ Vectorizer file does not exist!")
                continue
            
            # Verify both loaded correctly
            if model is not None and vectorizer is not None:
                has_predict = hasattr(model, 'predict')
                has_transform = hasattr(vectorizer, 'transform')
                
                if has_predict and has_transform:
                    MODEL_VECTORIZER_PAIRS.append({
                        'name': model_file.replace('.pkl', ''),
                        'model': model,
                        'vectorizer': vectorizer
                    })
                    print(f"  ✅ Successfully added pair: {model_file}")
                    print(f"     Model type: {type(model).__name__}")
                    print(f"     Vectorizer type: {type(vectorizer).__name__}")
                else:
                    print(f"  ❌ Invalid objects: predict={has_predict}, transform={has_transform}")
            else:
                print(f"  ❌ Failed to load: model={model is not None}, vectorizer={vectorizer is not None}")
                
        except Exception as e:
            print(f"  ❌ Exception loading pair {model_file}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"LOADING COMPLETE: {len(MODEL_VECTORIZER_PAIRS)} pairs loaded")
    print(f"{'='*50}")
    return len(MODEL_VECTORIZER_PAIRS) > 0

# Call the loader immediately
print("\nStarting model loading...")
load_models_with_vectorizers()
print(f"Final model count: {len(MODEL_VECTORIZER_PAIRS)}")

# ============================================
# HELPER FUNCTIONS
# ============================================

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

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(MODEL_VECTORIZER_PAIRS),
        'models_list': [p['name'] for p in MODEL_VECTORIZER_PAIRS]
    })

@app.route('/debug-models', methods=['GET'])
def debug_models():
    """Debug endpoint to check model loading"""
    result = {
        'cwd': os.getcwd(),
        'files': [f for f in os.listdir('.') if f.endswith('.pkl')],
        'models_loaded': len(MODEL_VECTORIZER_PAIRS),
        'model_names': [p['name'] for p in MODEL_VECTORIZER_PAIRS]
    }
    return jsonify(result)

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
        }
    return jsonify({
        'models': info,
        'total_models': len(MODEL_VECTORIZER_PAIRS)
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Flask API server...")
    print("=" * 50)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)