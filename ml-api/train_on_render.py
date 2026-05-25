import pandas as pd
import pickle
import joblib
import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

print("=" * 70)
print("TRAINING MODELS ON RENDER")
print("=" * 70)

# Find all CSV files
csv_files = glob.glob('*.csv')
print(f"Found {len(csv_files)} CSV files")

# Also check in parent directory
if not csv_files:
    csv_files = glob.glob('../*.csv')
    print(f"Found {len(csv_files)} CSV files in parent directory")

all_data = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        print(f"File {file} columns: {df.columns.tolist()}")
        
        if 'text' in df.columns and 'label' in df.columns:
            all_data.append(df[['text', 'label']])
            print(f"✅ Loaded {file}: {len(df)} samples")
        elif 'content' in df.columns and 'label' in df.columns:
            df = df.rename(columns={'content': 'text'})
            all_data.append(df[['text', 'label']])
            print(f"✅ Loaded {file}: {len(df)} samples (renamed content→text)")
        else:
            print(f"⚠️ Skipped {file}: no text/label columns")
    except Exception as e:
        print(f"❌ Error loading {file}: {e}")

if not all_data:
    print("\n❌ No datasets found! Creating sample data for testing...")
    # Create sample data for testing
    sample_data = pd.DataFrame({
        'text': [
            "URGENT!!! Share this to 10 WhatsApp groups",
            "President Tinubu announced new policies today",
            "BREAKING NEWS!!! EXCLUSIVE!!! SHOCKING!!!",
            "The Central Bank of Nigeria released new guidelines",
            "WIN FREE MONEY!!! Send to 20 contacts NOW!!!"
        ],
        'label': ['FAKE', 'REAL', 'FAKE', 'REAL', 'FAKE']
    })
    all_data.append(sample_data)
    print(f"✅ Created {len(sample_data)} sample training examples")

# Combine data
data = pd.concat(all_data, ignore_index=True)
print(f"\n📊 Total training samples: {len(data)}")
print(f"   FAKE: {len(data[data['label'] == 'FAKE'])}")
print(f"   REAL: {len(data[data['label'] == 'REAL'])}")

# Prepare for training
X = data['text'].values
y = data['label'].values

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Create and train vectorizer
print("\n📝 Training vectorizer...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english'
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)
print(f"   Features created: {X_train_vec.shape[1]}")

# Train Random Forest
print("\n🤖 Training Random Forest...")
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train_vec, y_train)
rf_score = rf.score(X_test_vec, y_test)
print(f"   Random Forest accuracy: {rf_score:.2%}")

# Train Logistic Regression
print("\n🤖 Training Logistic Regression...")
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_vec, y_train)
lr_score = lr.score(X_test_vec, y_test)
print(f"   Logistic Regression accuracy: {lr_score:.2%}")

# Save models with protocol 2 (max compatibility)
print("\n💾 Saving models...")

# Save vectorizer
with open('tfidf_vectorizer_retrained.pkl', 'wb') as f:
    pickle.dump(vectorizer, f, protocol=2)
print("   ✅ Saved tfidf_vectorizer_retrained.pkl")

# Also save as expected name
with open('tfidf_vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f, protocol=2)
print("   ✅ Saved tfidf_vectorizer.pkl")

# Save Random Forest
with open('model_rf_retrained.pkl', 'wb') as f:
    pickle.dump(rf, f, protocol=2)
print("   ✅ Saved model_rf_retrained.pkl")

# Also save as expected names
with open('model_b_final_balanced.pkl', 'wb') as f:
    pickle.dump(rf, f, protocol=2)
print("   ✅ Saved model_b_final_balanced.pkl")

# Save Logistic Regression
with open('model_lr_retrained.pkl', 'wb') as f:
    pickle.dump(lr, f, protocol=2)
print("   ✅ Saved model_lr_retrained.pkl")

# Also save as expected name
with open('model_b_logreg.pkl', 'wb') as f:
    pickle.dump(lr, f, protocol=2)
print("   ✅ Saved model_b_logreg.pkl")

# Save metadata
metadata = {
    'rf_accuracy': float(rf_score),
    'lr_accuracy': float(lr_score),
    'total_samples': len(data),
    'features': X_train_vec.shape[1]
}
with open('training_metadata.json', 'w') as f:
    import json
    json.dump(metadata, f, indent=2)
print(f"   ✅ Saved training_metadata.json")

print("\n" + "=" * 70)
print("✅ TRAINING COMPLETE!")
print(f"   Random Forest accuracy: {rf_score:.2%}")
print(f"   Logistic Regression accuracy: {lr_score:.2%}")
print("=" * 70)