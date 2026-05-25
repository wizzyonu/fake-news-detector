import joblib
import os

print("=" * 60)
print("Fixing model files for Render compatibility")
print("=" * 60)

# List all pickle files
pkl_files = [f for f in os.listdir('.') if f.endswith('.pkl')]

for filepath in pkl_files:
    try:
        print(f"Processing {filepath}...")
        
        # Load the file
        data = joblib.load(filepath)
        
        # Re-save with joblib (handles numpy compatibility better)
        joblib.dump(data, filepath, compress=3)
        
        print(f"  ✅ Fixed {filepath}")
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")

print("\n✅ All files fixed! Now commit and push to GitHub.")