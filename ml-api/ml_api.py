import sys
import numpy as np
import os
import pickle
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import warnings
warnings.filterwarnings('ignore')

# ============================================
# NUMPY COMPATIBILITY PATCH FOR RENDER
# ============================================
if not hasattr(np, '_core'):
    import numpy.core as _ns
    sys.modules['numpy._core'] = _ns
    np._core = _ns
    
    # Map key submodules that pickle/joblib will look for
    try:
        import numpy.core.multiarray as _multiarray
        sys.modules['numpy._core.multiarray'] = _multiarray
    except Exception as e:
        print(f"⚠️ Could not map numpy._core.multiarray: {e}")
        
    try:
        import numpy.core.umath as _umath
        sys.modules['numpy._core.umath'] = _umath
    except Exception as e:
        print(f"⚠️ Could not map numpy._core.umath: {e}")
        
    try:
        import numpy.core.numeric as _numeric
        sys.modules['numpy._core.numeric'] = _numeric
    except Exception as e:
        print(f"⚠️ Could not map numpy._core.numeric: {e}")
        
    print("✅ Patched numpy._core submodules for model loading compatibility")

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
# MODEL LOADING WITH AUTO-RETRAIN FALLBACK
# ============================================

def train_fresh_models():
    """Train fresh models from CSV data for guaranteed compatibility"""
    global MODEL_VECTORIZER_PAIRS
    import glob
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    
    print("\n" + "=" * 60)
    print("TRAINING FRESH MODELS FROM CSV DATA")
    print("=" * 60)
    
    csv_files = glob.glob('*.csv')
    print(f"Found {len(csv_files)} CSV files")
    
    all_texts = []
    all_labels = []
    
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            text_col = None
            label_col = None
            for col in df.columns:
                if col.lower() in ['text', 'content', 'article', 'news', 'statement']:
                    text_col = col
                if col.lower() in ['label', 'class', 'category', 'type']:
                    label_col = col
            if text_col and label_col:
                df_filtered = df[df[label_col].isin(['FAKE', 'REAL'])]
                all_texts.extend(df_filtered[text_col].astype(str).tolist())
                all_labels.extend(df_filtered[label_col].tolist())
                print(f"  ✅ {file}: {len(df_filtered)} samples")
            else:
                print(f"  ⚠️ Skipped {file}")
        except Exception as e:
            print(f"  ❌ Error loading {file}: {e}")
    
    if len(all_texts) < 10:
        print("⚠️ Not enough CSV data found, using minimal sample")
        all_texts = [
            "URGENT!!! Share this to 10 WhatsApp groups",
            "President Tinubu announced new policies today",
            "BREAKING NEWS!!! EXCLUSIVE!!! SHOCKING!!!",
            "The Central Bank of Nigeria released new guidelines",
            "WIN FREE MONEY!!! Send to 20 contacts NOW!!!",
            "Official government statement on economic reforms",
            "NCDC confirms new cases of Lassa fever",
            "EXPOSED!!! INEC officials caught rigging!!!",
            "Premium Times reports on budget passage",
            "DEATH HOAX: Governor found dead in London"
        ]
        all_labels = ['FAKE', 'REAL', 'FAKE', 'REAL', 'FAKE', 'REAL', 'REAL', 'FAKE', 'REAL', 'FAKE']
    
    print(f"\n📊 Total training data: {len(all_texts)} samples")
    print(f"   FAKE: {all_labels.count('FAKE')}, REAL: {all_labels.count('REAL')}")
    
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')
    X = vectorizer.fit_transform(all_texts)
    X_train, X_test, y_train, y_test = train_test_split(X, all_labels, test_size=0.2, random_state=42, stratify=all_labels)
    
    # Train Random Forest
    print("🤖 Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_score = rf.score(X_test, y_test)
    print(f"   ✅ Accuracy: {rf_score:.2%}")
    
    # Train Logistic Regression
    print("🤖 Training Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_score = lr.score(X_test, y_test)
    print(f"   ✅ Accuracy: {lr_score:.2%}")
    
    MODEL_VECTORIZER_PAIRS = [
        {'name': 'random_forest', 'model': rf, 'vectorizer': vectorizer},
        {'name': 'logistic_regression', 'model': lr, 'vectorizer': vectorizer},
    ]
    
    print(f"\n✅ TRAINING COMPLETE: {len(MODEL_VECTORIZER_PAIRS)} models ready")
    print(f"   RF: {rf_score:.2%}, LR: {lr_score:.2%}")
    print("=" * 60)


def test_models_work():
    """Run a quick test prediction to verify models actually work"""
    test_text = "URGENT breaking news share this now"
    for pair in MODEL_VECTORIZER_PAIRS:
        try:
            X = pair['vectorizer'].transform([test_text])
            pair['model'].predict(X)
        except Exception as e:
            print(f"  ❌ Test prediction failed for {pair['name']}: {e}")
            return False
    return True


def load_models_with_vectorizers():
    """Load each model with its matching vectorizer"""
    global MODEL_VECTORIZER_PAIRS
    
    print("\nInside load_models_with_vectorizers function")
    
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
                try:
                    with open(model_file, 'rb') as f:
                        model = pickle.load(f)
                    print(f"    ✅ Loaded with pickle")
                except Exception as pickle_error:
                    print(f"    Pickle failed: {pickle_error}")
                    try:
                        model = joblib.load(model_file)
                        print(f"    ✅ Loaded with joblib")
                    except Exception as joblib_error:
                        print(f"    Joblib also failed: {joblib_error}")
                        continue
            else:
                print(f"    ❌ File does not exist!")
                continue
            
            # Load vectorizer
            print(f"  Loading {vec_file}...")
            vectorizer = None
            
            if os.path.exists(vec_file):
                try:
                    with open(vec_file, 'rb') as f:
                        vectorizer = pickle.load(f)
                    print(f"    ✅ Loaded with pickle")
                except Exception as e1:
                    print(f"    Pickle failed: {e1}")
                    try:
                        vectorizer = joblib.load(vec_file)
                        print(f"    ✅ Loaded with joblib")
                    except Exception as e2:
                        print(f"    Joblib failed: {e2}")
                        continue
                
                # Fix idf_ / _idf_diag mismatch
                if vectorizer is not None and hasattr(vectorizer, '_tfidf'):
                    _tfidf = vectorizer._tfidf
                    if 'idf_' in _tfidf.__dict__ and not hasattr(_tfidf, '_idf_diag'):
                        try:
                            import scipy.sparse as sp
                            idf_val = _tfidf.__dict__['idf_']
                            n_features = len(idf_val)
                            _tfidf._idf_diag = sp.spdiags(idf_val, diags=0, m=n_features, n=n_features)
                            print("      ✅ Reconstructed _idf_diag")
                        except Exception as e:
                            print(f"      ⚠️ Failed to reconstruct _idf_diag: {e}")
            else:
                print(f"    ❌ Vectorizer file does not exist!")
                continue
            
            # Verify both loaded
            if model is not None and vectorizer is not None:
                has_predict = hasattr(model, 'predict')
                has_transform = hasattr(vectorizer, 'transform')
                if has_predict and has_transform:
                    MODEL_VECTORIZER_PAIRS.append({
                        'name': model_file.replace('.pkl', ''),
                        'model': model,
                        'vectorizer': vectorizer
                    })
                    print(f"  ✅ Added pair: {model_file} ({type(model).__name__})")
                    
        except Exception as e:
            print(f"  ❌ Exception loading pair {model_file}: {e}")
    
    print(f"\n{'='*50}")
    print(f"LOADING COMPLETE: {len(MODEL_VECTORIZER_PAIRS)} pairs loaded")
    print(f"{'='*50}")
    return len(MODEL_VECTORIZER_PAIRS) > 0


# ============================================
# STARTUP: Load models, test them, retrain if needed
# ============================================
print("\nStarting model loading...")
load_models_with_vectorizers()
print(f"Pre-trained model count: {len(MODEL_VECTORIZER_PAIRS)}")

# Test if loaded models actually work
if MODEL_VECTORIZER_PAIRS:
    print("\nTesting loaded models with a sample prediction...")
    if test_models_work():
        print(f"✅ All {len(MODEL_VECTORIZER_PAIRS)} pre-trained models verified working!")
    else:
        print("⚠️ Pre-trained models failed test predictions — retraining from CSV data...")
        MODEL_VECTORIZER_PAIRS = []
        train_fresh_models()
else:
    print("⚠️ No pre-trained models loaded — training from CSV data...")
    train_fresh_models()

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

@app.route('/debug-predict', methods=['GET', 'POST'])
def debug_predict():
    """Debug endpoint to run a prediction and return any errors raised"""
    text = "URGENT!!! President Tinubu is dead. Share this to all WhatsApp groups within 5 minutes!"
    if request.method == 'POST' and request.json:
        text = request.json.get('text', text)
        
    debug_info = []
    for pair in MODEL_VECTORIZER_PAIRS:
        model_name = pair['name']
        try:
            # Step 1: Transform text
            X = pair['vectorizer'].transform([text])
            step_1 = "Success"
        except Exception as e1:
            step_1 = f"Failed: {e1}"
            debug_info.append({
                'name': model_name,
                'vectorizer_error': step_1,
                'model_error': 'Not run'
            })
            continue
            
        try:
            # Step 2: Predict
            pred = pair['model'].predict(X)[0]
            step_2 = f"Success, prediction: {pred}"
        except Exception as e2:
            step_2 = f"Failed: {e2}"
            
        debug_info.append({
            'name': model_name,
            'vectorizer_status': step_1,
            'model_status': step_2
        })
        
    # Inspect attributes of the first vectorizer for debugging
    inspection_info = {}
    if MODEL_VECTORIZER_PAIRS:
        try:
            first_pair = MODEL_VECTORIZER_PAIRS[0]
            vec = first_pair['vectorizer']
            inspection_info['vectorizer_class'] = str(type(vec).__name__)
            inspection_info['vectorizer_dict_keys'] = list(getattr(vec, '__dict__', {}).keys())
            if hasattr(vec, '_tfidf'):
                _tfidf = vec._tfidf
                inspection_info['tfidf_class'] = str(type(_tfidf).__name__)
                inspection_info['tfidf_dict_keys'] = list(getattr(_tfidf, '__dict__', {}).keys())
                for key in ['_idf_diag', 'idf_', '_idf']:
                    inspection_info[f'has_{key}'] = hasattr(_tfidf, key)
                
                # Check direct access to idf_ to see the exact exception raised
                try:
                    val = _tfidf.idf_
                    inspection_info['idf_value_type'] = str(type(val).__name__)
                    inspection_info['idf_value_str'] = str(val)[:100]
                except Exception as e:
                    inspection_info['idf_access_error'] = f"{type(e).__name__}: {e}"
        except Exception as e:
            inspection_info['error'] = f"Inspection failed: {e}"
        
    return jsonify({
        'text_tested': text,
        'models_count': len(MODEL_VECTORIZER_PAIRS),
        'debug_info': debug_info,
        'inspection_info': inspection_info
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