import pickle
import joblib
import numpy as np
import os
import sys

print("=" * 70)
print("FIXING VECTORIZERS FOR NUMPY 1.x COMPATIBILITY")
print("=" * 70)
print(f"Python version: {sys.version}")
print(f"Numpy version: {np.__version__}")
print(f"Numpy has _core: {hasattr(np, '_core')}")
print("=" * 70)

# List all vectorizer files
vectorizer_files = [
    'tfidf_vec_balanced.pkl',
    'tfidf_vec_final_balanced.pkl',
    'tfidf_vectorizer.pkl',
    'tfidf_vec_multi_source.pkl',
    'tfidf_vec_latest.pkl'
]

fixed_count = 0
for vec_file in vectorizer_files:
    if os.path.exists(vec_file):
        print(f"\n📁 Processing: {vec_file}")
        print(f"   File size: {os.path.getsize(vec_file)} bytes")
        
        try:
            # Try multiple loading methods
            data = None
            
            # Method 1: Try joblib
            try:
                data = joblib.load(vec_file)
                print(f"   ✅ Loaded with joblib")
            except Exception as e:
                print(f"   ⚠️ Joblib failed: {str(e)[:50]}")
                
                # Method 2: Try pickle
                try:
                    with open(vec_file, 'rb') as f:
                        data = pickle.load(f)
                    print(f"   ✅ Loaded with pickle")
                except Exception as e2:
                    print(f"   ⚠️ Pickle failed: {str(e2)[:50]}")
                    
                    # Method 3: Try with numpy patching
                    try:
                        # Create a custom unpickler
                        import io
                        class NumpyUnpickler(pickle.Unpickler):
                            def find_class(self, module, name):
                                if module == 'numpy._core' and name == 'multiarray':
                                    module = 'numpy.core'
                                return super().find_class(module, name)
                        
                        with open(vec_file, 'rb') as f:
                            data = NumpyUnpickler(f).load()
                        print(f"   ✅ Loaded with custom unpickler")
                    except Exception as e3:
                        print(f"   ❌ All loading methods failed")
                        continue
            
            if data is not None:
                # Re-save with protocol 2 (most compatible)
                with open(vec_file, 'wb') as f:
                    pickle.dump(data, f, protocol=2)
                print(f"   ✅ Re-saved with protocol 2")
                fixed_count += 1
            else:
                print(f"   ❌ Could not load file")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print(f"\n⚠️ File not found: {vec_file}")

print("\n" + "=" * 70)
print(f"✅ Fixed {fixed_count}/{len(vectorizer_files)} vectorizer files")
print("=" * 70)