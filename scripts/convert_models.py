# scripts/convert_models.py
import joblib
import json
import os
import numpy as np

# Helper function to convert numpy types to Python native types
def convert_to_native(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {convert_to_native(k): convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native(item) for item in obj]
    else:
        return obj

print("=" * 70)
print("🚀 CONVERTING NIGERIAN FAKE NEWS MODELS (USING JOBLIB)")
print("=" * 70)

# Create output directory
os.makedirs('public/models', exist_ok=True)

# ============================================
# STEP 1: Load the vectorizer (TF-IDF)
# ============================================
print("\n📊 Loading TF-IDF Vectorizer...")

vectorizer_files = [
    'tfidf_vec_final_balanced.pkl',
    'tfidf_vec_balanced.pkl',
    'tfidf_vec_multi_source.pkl',
    'tfidf_vectorizer.pkl'
]

vectorizer = None
vectorizer_name = None

for vf in vectorizer_files:
    if os.path.exists(vf):
        try:
            vectorizer = joblib.load(vf)
            vectorizer_name = vf
            print(f"   ✅ Loaded: {vf}")
            print(f"   Vocabulary size: {len(vectorizer.vocabulary_)} words")
            break
        except Exception as e:
            print(f"   ❌ Failed to load {vf}: {e}")

if not vectorizer:
    print("   ❌ Could not load any vectorizer!")
    exit(1)

# Convert vocabulary to native Python types
vocabulary = {str(word): int(idx) for word, idx in vectorizer.vocabulary_.items()}
with open('public/models/vocabulary.json', 'w') as f:
    json.dump(vocabulary, f)
print(f"   ✅ Saved {len(vocabulary)} words to public/models/vocabulary.json")

# Save TF-IDF parameters (convert numpy types)
tfidf_params = {
    'vocabulary_size': int(len(vocabulary)),
    'ngram_range': [int(x) for x in vectorizer.ngram_range],
    'max_features': int(vectorizer.max_features) if vectorizer.max_features else None,
    'use_idf': bool(vectorizer.use_idf),
    'smooth_idf': bool(vectorizer.smooth_idf),
    'sublinear_tf': bool(vectorizer.sublinear_tf),
    'stop_words': str(vectorizer.stop_words) if hasattr(vectorizer, 'stop_words') else None,
    'vectorizer_file': vectorizer_name
}

with open('public/models/tfidf_params.json', 'w') as f:
    json.dump(tfidf_params, f, indent=2)
print(f"   ✅ Saved TF-IDF params to public/models/tfidf_params.json")

# ============================================
# STEP 2: Load the best model
# ============================================
print("\n🤖 Loading trained model...")

model_files = [
    'model_b_final_balanced.pkl',
    'model_b_balanced.pkl',
    'model_b_multi_source.pkl',
    'model_b_logreg.pkl',
    'model_latest.pkl'
]

model = None
model_name = None

for mf in model_files:
    if os.path.exists(mf):
        try:
            model = joblib.load(mf)
            model_name = mf
            print(f"   ✅ Loaded: {mf}")
            print(f"   Type: {type(model).__name__}")
            print(f"   Classes: {model.classes_}")
            print(f"   Features: {model.n_features_in_}")
            break
        except Exception as e:
            print(f"   ❌ Failed to load {mf}: {e}")

if not model:
    print("   ❌ Could not load any model!")
    exit(1)

# Save model metadata (convert numpy types)
model_metadata = {
    'name': model_name,
    'classes': [int(c) for c in model.classes_],
    'class_names': ['REAL', 'FAKE'] if model.classes_[0] == 0 else ['FAKE', 'REAL'],
    'n_features': int(model.n_features_in_),
    'model_type': type(model).__name__,
    'intercept': float(model.intercept_[0]),
    'coef_shape': [int(x) for x in model.coef_.shape]
}

with open('public/models/model_metadata.json', 'w') as f:
    json.dump(model_metadata, f, indent=2)
print(f"   ✅ Saved model metadata to public/models/model_metadata.json")

# Save model coefficients (convert numpy array to list)
coefficients = model.coef_[0].tolist()
with open('public/models/model_coefficients.json', 'w') as f:
    json.dump(coefficients, f)
print(f"   ✅ Saved {len(coefficients)} coefficients to public/models/model_coefficients.json")

# ============================================
# STEP 3: Create simplified prediction config
# ============================================
print("\n⚙️ Creating prediction configuration...")

# Get feature names and coefficients
coefs = model.coef_[0]
feature_names = list(vocabulary.keys())
feature_indices = list(vocabulary.values())

# Create mapping from index to word
idx_to_word = {idx: word for word, idx in vocabulary.items()}

# Get top fake indicators (positive coefficients)
fake_indicators = []
real_indicators = []

for i, coef in enumerate(coefs):
    word = idx_to_word.get(i, None)
    if word:
        if coef > 0.3:  # Strong fake indicator
            fake_indicators.append({'word': word, 'weight': float(coef)})
        elif coef < -0.3:  # Strong real indicator
            real_indicators.append({'word': word, 'weight': float(coef)})

# Sort by absolute weight
fake_indicators.sort(key=lambda x: x['weight'], reverse=True)
real_indicators.sort(key=lambda x: x['weight'])

prediction_config = {
    'threshold': 0.5,
    'intercept': float(model.intercept_[0]),
    'total_features': int(len(coefs)),
    'fake_indicators': fake_indicators[:50],
    'real_indicators': real_indicators[:50]
}

with open('public/models/prediction_config.json', 'w') as f:
    json.dump(prediction_config, f, indent=2)
print(f"   ✅ Saved prediction config")
print(f"   Fake indicators found: {len(fake_indicators)}")
print(f"   Real indicators found: {len(real_indicators)}")

# ============================================
# STEP 4: Create a lightweight JS-friendly model
# ============================================
print("\n📱 Creating JavaScript-friendly model format...")

# Create a simplified model that JS can use directly
js_model = {
    'intercept': float(model.intercept_[0]),
    'coefficients': coefficients,
    'vocabulary': {word: int(idx) for word, idx in list(vocabulary.items())[:1000]},  # Limit size
    'metadata': model_metadata
}

with open('public/models/js_model.json', 'w') as f:
    json.dump(js_model, f)
print(f"   ✅ Saved JS-friendly model to public/models/js_model.json")

# ============================================
# STEP 5: Try ONNX conversion (optional)
# ============================================
print("\n🔄 Attempting ONNX conversion (optional)...")

onnx_success = False
try:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    import onnx
    
    # Define input type
    initial_type = [('float_input', FloatTensorType([None, model.n_features_in_]))]
    
    # Convert
    onnx_model = convert_sklearn(
        model,
        initial_types=initial_type,
        target_opset=12,
        options={id(model): {'zipmap': False}}
    )
    
    # Save ONNX
    onnx_path = 'public/models/nigerian_fake_news_model.onnx'
    onnx.save_model(onnx_model, onnx_path)
    print(f"   ✅ ONNX model saved to {onnx_path}")
    print(f"   File size: {os.path.getsize(onnx_path) / 1024:.1f} KB")
    onnx_success = True
    
except ImportError:
    print("   ⚠️ skl2onnx not installed. Run: pip install skl2onnx onnx onnxruntime")
except Exception as e:
    print(f"   ⚠️ ONNX conversion skipped: {e}")

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 70)
print("✅ CONVERSION COMPLETE!")
print("=" * 70)

print("\n📁 Files created in 'public/models/':")
print("   📄 vocabulary.json - All words your model knows")
print("   📄 tfidf_params.json - Vectorizer settings")
print("   📄 model_metadata.json - Model information")
print("   📄 model_coefficients.json - Model weights")
print("   📄 prediction_config.json - Top fake/real indicators")
print("   📄 js_model.json - JavaScript-friendly model")
if onnx_success:
    print("   📄 nigerian_fake_news_model.onnx - ONNX model")

print("\n📊 Model Statistics:")
print(f"   Vocabulary size: {len(vocabulary)} words")
print(f"   Model features: {model.n_features_in_}")
print(f"   Classes: REAL (0), FAKE (1)")

print("\n🔍 Top 10 Fake News Indicators (from YOUR Nigerian data):")
for i, ind in enumerate(fake_indicators[:10]):
    print(f"   {i+1}. '{ind['word']}' (weight: {ind['weight']:.3f})")

print("\n✅ Top 10 Real News Indicators (from YOUR Nigerian data):")
for i, ind in enumerate(real_indicators[:10]):
    print(f"   {i+1}. '{ind['word']}' (weight: {-ind['weight']:.3f})")

print("\n📝 NEXT STEPS:")
print("   1. Install ONNX (optional): pip install skl2onnx onnx onnxruntime")
print("   2. Copy the JavaScript helper files (tfidf.js, onnxModel.js)")
print("   3. Update your analyze.js to use the model")
print("   4. Test with: npm run dev")

print("\n🎉 Your Nigerian-trained model is ready! The JSON files are in public/models/")