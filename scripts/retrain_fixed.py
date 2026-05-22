# scripts/retrain_fixed.py
"""
Fixed retraining script - handles data properly
"""
import pandas as pd
import numpy as np
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
    """Load ALL CSV files properly"""
    print("\n📂 Loading all datasets...")
    
    # Find all CSV files
    csv_files = glob.glob('*.csv')
    # Filter for news datasets
    csv_files = [f for f in csv_files if 'nigerian' in f.lower() or 'news' in f.lower() or 'balanced' in f.lower()]
    
    all_dfs = []
    
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            
            # Check for required columns
            if 'text' in df.columns and 'label' in df.columns:
                # Ensure text is string
                df['text'] = df['text'].astype(str)
                df['label'] = df['label'].astype(int)
                all_dfs.append(df[['text', 'label']])
                print(f"   ✅ {file}: {len(df)} rows")
            elif 'text' in df.columns and 'class' in df.columns:
                df = df.rename(columns={'class': 'label'})
                df['text'] = df['text'].astype(str)
                df['label'] = df['label'].astype(int)
                all_dfs.append(df[['text', 'label']])
                print(f"   ✅ {file}: {len(df)} rows (renamed class→label)")
            else:
                print(f"   ⚠️ {file}: Skipped (columns: {df.columns.tolist()[:5]}...)")
                
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
    
    # Remove very short texts
    combined = combined[combined['text'].str.len() > 50]
    
    print(f"\n📊 Combined data:")
    print(f"   Total unique: {len(combined)} articles")
    print(f"   Removed {before - after} duplicates")
    print(f"   REAL (0): {len(combined[combined['label']==0])}")
    print(f"   FAKE (1): {len(combined[combined['label']==1])}")
    
    return combined

def balance_dataset(df):
    """Balance the dataset (equal REAL and FAKE samples)"""
    print("\n⚖️ Balancing dataset...")
    
    df_real = df[df['label'] == 0]
    df_fake = df[df['label'] == 1]
    
    print(f"   Before: REAL={len(df_real)}, FAKE={len(df_fake)}")
    
    if len(df_real) < len(df_fake):
        # Sample down FAKE to match REAL count
        df_fake_sampled = df_fake.sample(n=len(df_real), random_state=42)
        df_balanced = pd.concat([df_real, df_fake_sampled])
    elif len(df_fake) < len(df_real):
        # Sample down REAL to match FAKE count
        df_real_sampled = df_real.sample(n=len(df_fake), random_state=42)
        df_balanced = pd.concat([df_real_sampled, df_fake])
    else:
        df_balanced = df
    
    # Shuffle
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"   After: REAL={len(df_balanced[df_balanced['label']==0])}, FAKE={len(df_balanced[df_balanced['label']==1])}")
    
    return df_balanced

def train_new_model(df, max_features=5000):
    """Train a new model with the combined dataset"""
    print("\n🤖 Training new model...")
    
    # Convert to lists (fix for the indexing error)
    X = df['text'].tolist()  # Convert to list instead of numpy array
    y = df['label'].tolist()
    
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
    print(f"   REAL → REAL: {cm[0,0]}")
    print(f"   REAL → FAKE: {cm[0,1]}")
    print(f"   FAKE → REAL: {cm[1,0]}")
    print(f"   FAKE → FAKE: {cm[1,1]}")
    
    return model, vectorizer, accuracy

def save_models(model, vectorizer, accuracy):
    """Save the trained models"""
    print("\n💾 Saving models...")
    
    # Create backup of old models
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
    
    # Also show top features
    coefs = model.coef_[0]
    feature_names = vectorizer.get_feature_names_out()
    
    # Top FAKE indicators
    fake_indices = coefs.argsort()[-20:][::-1]
    print(f"\n🔍 Top 10 FAKE news indicators:")
    for i, idx in enumerate(fake_indices[:10]):
        print(f"   {i+1}. '{feature_names[idx]}': {coefs[idx]:.3f}")
    
    # Top REAL indicators
    real_indices = coefs.argsort()[:20]
    print(f"\n✅ Top 10 REAL news indicators:")
    for i, idx in enumerate(real_indices[:10]):
        print(f"   {i+1}. '{feature_names[idx]}': {coefs[idx]:.3f}")

def main():
    """Main retraining pipeline"""
    print("=" * 70)
    print("🔄 COMPLETE RETRAINING PIPELINE (FIXED)")
    print("=" * 70)
    
    # Load all data
    df = load_all_datasets()
    if df is None:
        return
    
    # Balance the dataset
    df_balanced = balance_dataset(df)
    
    # Train new model
    model, vectorizer, accuracy = train_new_model(df_balanced)
    
    # Save models
    save_models(model, vectorizer, accuracy)
    
    print("\n" + "=" * 70)
    print("✅ RETRAINING COMPLETE!")
    print("=" * 70)
    print("\n📌 NEXT STEPS:")
    print("   1. Run: python scripts/convert_models.py")
    print("   2. Restart your Next.js app")
    print("   3. Your model now has more data!")

if __name__ == "__main__":
    main()