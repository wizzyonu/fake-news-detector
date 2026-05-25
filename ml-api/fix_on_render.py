import pickle
import joblib
import os

print("=" * 60)
print("RE-SAVING VECTORIZERS FOR COMPATIBILITY")
print("=" * 60)

vectorizer_files = [
    'tfidf_vec_balanced.pkl',
    'tfidf_vec_final_balanced.pkl',
    'tfidf_vectorizer.pkl',
    'tfidf_vec_multi_source.pkl',
    'tfidf_vec_latest.pkl'
]

for f in vectorizer_files:
    if os.path.exists(f):
        print(f"\nProcessing {f}...")
        try:
            # Load with joblib
            data = joblib.load(f)
            print(f"  Loaded successfully")
            
            # Re-save with pickle protocol 2
            with open(f, 'wb') as out:
                pickle.dump(data, out, protocol=2)
            print(f"  ✅ Re-saved with protocol 2")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    else:
        print(f"  ⚠️ {f} not found")

print("\n" + "=" * 60)
print("Done! Redeploy to test.")