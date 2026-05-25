import pickle
import pandas as pd
import glob
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

print("=" * 60)
print("TRAINING MODELS WITH YOUR REAL NIGERIAN DATASETS")
print("=" * 60)

# Find all CSV files in the directory
csv_files = glob.glob('*.csv')
print(f"\n📁 Found {len(csv_files)} CSV files")

# Load and combine all datasets
all_texts = []
all_labels = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        print(f"\n📄 Loading {file}:")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   Shape: {df.shape}")
        
        # Try to find text and label columns
        text_col = None
        label_col = None
        
        for col in df.columns:
            if col.lower() in ['text', 'content', 'article', 'news', 'statement']:
                text_col = col
            if col.lower() in ['label', 'class', 'category', 'type']:
                label_col = col
        
        if text_col and label_col:
            # Filter to only FAKE and REAL labels
            df_filtered = df[df[label_col].isin(['FAKE', 'REAL'])]
            texts = df_filtered[text_col].astype(str).tolist()
            labels = df_filtered[label_col].tolist()
            
            all_texts.extend(texts)
            all_labels.extend(labels)
            print(f"   ✅ Added {len(texts)} samples (FAKE/REAL only)")
        else:
            print(f"   ⚠️ Skipped - couldn't find text/label columns")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n" + "=" * 60)
print(f"📊 TOTAL TRAINING DATA: {len(all_texts)} samples")
print(f"   FAKE: {all_labels.count('FAKE')}")
print(f"   REAL: {all_labels.count('REAL')}")
print("=" * 60)

if len(all_texts) < 100:
    print("\n⚠️ Not enough data found! Using sample data as fallback...")
    # Fallback to sample data
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
    print(f"   Using {len(all_texts)} sample training examples")

# Train vectorizer
print("\n📝 Training TF-IDF Vectorizer...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english'
)
X = vectorizer.fit_transform(all_texts)
print(f"   ✅ Created {X.shape[1]} features from {X.shape[0]} samples")

# Split for evaluation
X_train, X_test, y_train, y_test = train_test_split(
    X, all_labels, test_size=0.2, random_state=42, stratify=all_labels
)

# Train Random Forest
print("\n🤖 Training Random Forest Classifier...")
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_score = rf.score(X_test, y_test)
print(f"   ✅ Random Forest accuracy: {rf_score:.2%}")

# Train Logistic Regression
print("\n🤖 Training Logistic Regression...")
lr = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
lr.fit(X_train, y_train)
lr_score = lr.score(X_test, y_test)
print(f"   ✅ Logistic Regression accuracy: {lr_score:.2%}")

# Save models with protocol 2 (max compatibility)
print("\n💾 Saving models...")

with open('tfidf_vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f, protocol=2)
print("   ✅ Saved tfidf_vectorizer.pkl")

with open('model_b_final_balanced.pkl', 'wb') as f:
    pickle.dump(rf, f, protocol=2)
print("   ✅ Saved model_b_final_balanced.pkl")

with open('model_b_logreg.pkl', 'wb') as f:
    pickle.dump(lr, f, protocol=2)
print("   ✅ Saved model_b_logreg.pkl")

# Save metadata
metadata = {
    'total_samples': len(all_texts),
    'fake_count': all_labels.count('FAKE'),
    'real_count': all_labels.count('REAL'),
    'rf_accuracy': float(rf_score),
    'lr_accuracy': float(lr_score),
    'features': X.shape[1]
}
with open('training_metadata.json', 'w') as f:
    import json
    json.dump(metadata, f, indent=2)
print("   ✅ Saved training_metadata.json")

print("\n" + "=" * 60)
print("✅ TRAINING COMPLETE!")
print(f"   Total samples trained: {len(all_texts)}")
print(f"   Random Forest accuracy: {rf_score:.2%}")
print(f"   Logistic Regression accuracy: {lr_score:.2%}")
print("=" * 60)