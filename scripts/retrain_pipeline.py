# scripts/retrain_pipeline.py
"""
Complete retraining pipeline - Loads ALL datasets (old + new) and retrains
"""
import pandas as pd
import pickle
import joblib
import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import json
from datetime import datetime

def load_all_datasets():
    """Load ALL CSV files in the project"""
    print("\n📂 Loading all datasets...")
    
    # Find all CSV files
    csv_files = glob.glob('*.csv')
    csv_files = [f for f in csv_files if 'nigerian' in f.lower() or 'news' in f.lower()]
    
    all_dfs = []
    
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            
            # Check for required columns
            if 'text' in df.columns and 'label' in df.columns:
                all_dfs.append(df[['text', 'label']])
                print(f"   ✅ {file}: {len(df)} rows")
            elif 'text' in df.columns and 'class' in df.columns:
                df = df.rename(columns={'class': 'label'})
                all_dfs.append(df[['text', 'label']])
                print(f"   ✅ {file}: {len(df)} rows (renamed class→label)")
            else:
                print(f"   ⚠️ {file}: Skipped (columns: {df.columns.tolist()})")
                
        except Exception as e:
            print(f"   ❌ {file}: Error - {e}")
    
    if not all_dfs:
        print("   ❌ No valid datasets found!")
        return None
    
    # Combine all
    combined = pd.concat(all_dfs, ignore_index=True)
    
    # Remove duplicates
    before = len(combined)
    combined = combined.drop_duplicates(subset=['text'])
    after = len(combined)
    
    print(f"\n📊 Combined data:")
    print(f"   Total: {len(combined)} unique articles")
    print(f"   Removed {before - after} duplicates")
    print(f"   REAL (0): {len(combined[combined['label']==0])}")
    print(f"   FAKE (1): {len(combined[combined['label']==1])}")
    
    return combined

def train_new_model(df, max_features=5000):
    """Train a new model with the combined dataset"""
    print("\n🤖 Training new model...")
    
    # Prepare data
    X = df['text'].values
    y = df['label'].values
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    
    # Create vectorizer
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        sublinear_tf=True,
        stop_words='english'
    )
    
    # Transform
    print("   Vectorizing text...")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # Train
    print("   Training logistic regression...")
    model = LogisticRegression(max_iter=1000, random_state=42, C=1.0)
    model.fit(X_train_vec, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n📊 Model Performance:")
    print(f"   Accuracy: {accuracy:.4f} ({accuracy*100:.1f}%)")
    print(f"\n   Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['REAL', 'FAKE']))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n   Confusion Matrix:")
    print(f"   REAL predicted REAL: {cm[0,0]}")
    print(f"   REAL predicted FAKE: {cm[0,1]}")
    print(f"   FAKE predicted REAL: {cm[1,0]}")
    print(f"   FAKE predicted FAKE: {cm[1,1]}")
    
    return model, vectorizer, accuracy

def save_models(model, vectorizer, accuracy):
    """Save the trained models"""
    print("\n💾 Saving models...")
    
    # Create backup of old models
    import shutil
    os.makedirs('models_backup', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save new models with timestamp
    joblib.dump(model, f'models_backup/model_{timestamp}.pkl')
    joblib.dump(vectorizer, f'models_backup/vectorizer_{timestamp}.pkl')
    
    # Update main model files
    joblib.dump(model, 'model_b_final_balanced.pkl')
    joblib.dump(vectorizer, 'tfidf_vec_final_balanced.pkl')
    
    # Also save as backup copies
    joblib.dump(model, 'model_latest.pkl')
    joblib.dump(vectorizer, 'tfidf_vec_latest.pkl')
    
    print(f"   ✅ Saved: model_b_final_balanced.pkl")
    print(f"   ✅ Saved: tfidf_vec_final_balanced.pkl")
    print(f"   ✅ Backup saved: models_backup/model_{timestamp}.pkl")
    
    # Save metadata
    metadata = {
        'timestamp': timestamp,
        'accuracy': float(accuracy),
        'features': vectorizer.max_features,
        'vocabulary_size': len(vectorizer.vocabulary_),
        'training_date': datetime.now().isoformat(),
        'model_type': 'LogisticRegression'
    }
    
    with open('model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"   ✅ Saved metadata to model_metadata.json")

def main():
    """Main retraining pipeline"""
    print("=" * 70)
    print("🔄 COMPLETE RETRAINING PIPELINE")
    print("=" * 70)
    
    # Load all data
    df = load_all_datasets()
    if df is None:
        return
    
    # Train new model
    model, vectorizer, accuracy = train_new_model(df)
    
    # Save models
    save_models(model, vectorizer, accuracy)
    
    print("\n" + "=" * 70)
    print("✅ RETRAINING COMPLETE!")
    print("=" * 70)
    print("\n📌 NEXT STEPS:")
    print("   1. Run: python scripts/convert_models.py")
    print("   2. Restart your Next.js app")
    print("   3. Your model is now improved with more data!")

if __name__ == "__main__":
    main()