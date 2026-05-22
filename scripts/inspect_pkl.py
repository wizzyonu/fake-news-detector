# scripts/inspect_pkl.py
import os
import sys

print("=" * 70)
print("INSPECTING YOUR .PKL FILES")
print("=" * 70)

# List all .pkl files
pkl_files = [f for f in os.listdir('.') if f.endswith('.pkl')]
print(f"\n📁 Found {len(pkl_files)} .pkl files:")
for f in pkl_files:
    size = os.path.getsize(f) / 1024  # KB
    print(f"   - {f} ({size:.1f} KB)")

print("\n🔍 Attempting to read each file...")
print("-" * 50)

for pkl_file in pkl_files:
    print(f"\n📄 {pkl_file}")
    
    # Try different methods
    methods = [
        ('pickle', lambda f: __import__('pickle').load(f)),
        ('joblib', lambda f: __import__('joblib').load(f)),
    ]
    
    for method_name, loader in methods:
        try:
            if method_name == 'pickle':
                import pickle
                with open(pkl_file, 'rb') as f:
                    obj = pickle.load(f)
            else:
                import joblib
                obj = joblib.load(pkl_file)
            
            print(f"   ✅ Success with {method_name}")
            print(f"   Type: {type(obj).__name__}")
            
            if hasattr(obj, 'classes_'):
                print(f"   Classes: {obj.classes_}")
            if hasattr(obj, 'n_features_in_'):
                print(f"   Features: {obj.n_features_in_}")
            if hasattr(obj, 'vocabulary_'):
                print(f"   Vocabulary size: {len(obj.vocabulary_)}")
                # Show first 10 words
                words = list(obj.vocabulary_.keys())[:10]
                print(f"   Sample words: {words}")
            
            break
            
        except Exception as e:
            print(f"   ❌ {method_name} failed: {str(e)[:100]}")
    else:
        print(f"   ❌ Could not read with any method")

print("\n" + "=" * 70)