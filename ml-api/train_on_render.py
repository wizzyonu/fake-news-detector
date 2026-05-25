import pandas as pd
import pickle
import joblib
import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

print("=" * 60)
print("TRAINING MODELS ON RENDER")
print("=" * 60)

# Load all datasets
all_data = []
csv_files = glob.glob('*.csv')
print(f"Found {len(csv_files)} CSV files")

for file in csv_files:
    try:
        df = pd.read_csv(file)
        if 'text' in df.columns and 'label' in df.columns:
            all_data.append(df)
            print(f"✅ Loaded {file}: {len(df)} samples")
        elif 'content' in df.columns and 'label' in df.columns:
            df = df.rename(columns={'content': 'text'})
            all_data.append(df)
            print(f"✅ Loaded {file}: {len(df)} samples (renamed)")
    except Exception as e:
        print(f"❌ Error loading {file}: {e}")

if not all_data:
    print("No datasets found!")
    exit(1)

# Combine data
data = pd.concat(all_data, ignore_index=True)
print(f"\n📊 Total samples: {len(data)}")
print(f"   FAKE: {len(data[data['label'] == 'FAKE'])}")
print(f"   REAL: {len(data[data['label'] == 'REAL'])}")

# Prepare for training
X = data['text'].values
y = data['label'].values

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Create vectorizer
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english'
)

print("\n📝 Vectorizing text...")
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)
print(f"   Features: {X_train_vec.shape[1]}")

# Train models
print("\n🤖 Training models...")

# Random Forest
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train_vec, y_train)
rf_score = rf.score(X_test_vec, y_test)
print(f"   Random Forest accuracy: {rf_score:.2%}")

# Logistic Regression
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_vec, y_train)
lr_score = lr.score(X_test_vec, y_test)
print(f"   Logistic Regression accuracy: {lr_score:.2%}")

# Save models
print("\n💾 Saving models...")

# Save vectorizer (now compatible!)
with open('tfidf_vectorizer_retrained.pkl', 'wb') as f:
    pickle.dump(vectorizer, f, protocol=2)

# Save models
with open('model_rf_retrained.pkl', 'wb') as f:
    pickle.dump(rf, f, protocol=2)

with open('model_lr_retrained.pkl', 'wb') as f:
    pickle.dump(lr, f, protocol=2)

# Also save as expected names
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
joblib.dump(rf, 'model_b_final_balanced.pkl')
joblib.dump(lr, 'model_b_logreg.pkl')

print("\n✅ Training complete!")
print("   Saved: tfidf_vectorizer.pkl")
print("   Saved: model_b_final_balanced.pkl")
print("   Saved: model_b_logreg.pkl")