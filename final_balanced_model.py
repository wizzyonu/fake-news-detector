import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils import resample # For balancing
import joblib

# === CONFIGURATION ===
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

SOURCES = {
    'Punch NG': {'url_template': 'https://punchng.com/topics/news/page/{}/', 'selectors': ['h2.entry-title']},
    'Vanguard News': {'url_template': 'https://vanguardngr.com/category/news/page/{}/', 'selectors': ['h2.entry-title']},
    'Premium Times': {'url_template': 'https://www.premiumtimesng.com/news/page/{}/', 'selectors': ['h2.entry-title']},
    'The Cable': {'url_template': 'https://www.thecable.ng/category/news/page/{}/', 'selectors': ['h2.entry-title']}
}

MAX_PAGES_PER_SOURCE = 15 
OUTPUT_FILE = 'balanced_nigerian_dataset_final.csv'
MODEL_FILE = 'model_b_final_balanced.pkl'
VECTORIZER_FILE = 'tfidf_vec_final_balanced.pkl'

# === 1. SCRAPE REAL NEWS ===
def scrape_real_news():
    all_articles = []
    for source_name, config in SOURCES.items():
        print(f"\n🕷️ Scraping REAL News from {source_name}...")
        count = 0
        for page in range(1, MAX_PAGES_PER_SOURCE + 1):
            url = config['url_template'].format(page)
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code != 200: continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                titles = []
                for selector in config['selectors']:
                    elements = soup.select(selector)
                    if elements:
                        titles = [el.get_text(strip=True) for el in elements]
                        break
                
                if not titles: 
                    titles = [t.get_text(strip=True) for t in soup.find_all(['h2', 'h3']) if len(t.get_text(strip=True)) > 15]

                for title in titles:
                    clean_title = re.sub(r'\s+', ' ', title)
                    if 15 < len(clean_title) < 150:
                        all_articles.append({
                            'text': clean_title, 
                            'label': 0, # 0 = REAL
                            'source': source_name,
                            'type': 'Verified_Real'
                        })
                        count += 1
                
                if count >= 200: break # Get ~200 from each source if possible
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                continue
    print(f"✅ Total Real Samples Collected: {len(all_articles)}")
    return all_articles

# === 2. GENERATE SYNTHETIC FAKE NEWS ===
def generate_fake_news(real_articles, target_count):
    fake_articles = []
    print(f"\n🎭 Generating {target_count} SYNTHETIC FAKE News via Augmentation...")
    
    prefixes = ["SHOCKING!!! ", "BREAKING NEWS: ", "URGENT SHARE NOW: ", "YOU WON'T BELIEVE: ", "CONFIRMED!!! "]
    suffixes = [" SHARE TO ALL GROUPS!", " FORWARD IMMEDIATELY!", " DON'T IGNORE THIS!", " !!!", " READ AND SHARE!"]
    
    while len(fake_articles) < target_count:
        base_article = random.choice(real_articles)
        original_text = base_article['text']
        
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        if random.random() > 0.5:
            fake_text = f"{prefix}{original_text}{suffix}"
        else:
            fake_text = f"{prefix}{original_text.upper()}{suffix}"
            
        fake_articles.append({
            'text': fake_text, 
            'label': 1, # 1 = FAKE
            'source': 'Synthetic_Augmentation',
            'type': 'Synthetic_Fake'
        })

    print(f"✅ Total Fake Samples Generated: {len(fake_articles)}")
    return fake_articles

# === 3. TRAIN MODEL B WITH BALANCING ===
def train_model_balanced(df):
    print("\n--- 🧠 Training Model B (Logistic Regression) with Balanced Classes ---")
    
    # Separate classes
    df_real = df[df['label'] == 0]
    df_fake = df[df['label'] == 1]
    
    # Undersample Fake to match Real count (or vice versa)
    # Here we assume Real is the minority. If Fake is larger, we undersample Fake.
    n_samples = min(len(df_real), len(df_fake))
    
    df_real_downsampled = resample(df_real, replace=False, n_samples=n_samples, random_state=42)
    df_fake_downsampled = resample(df_fake, replace=False, n_samples=n_samples, random_state=42)
    
    # Combine balanced classes
    df_balanced = pd.concat([df_real_downsampled, df_fake_downsampled])
    
    print(f"Balanced Dataset Size: {len(df_balanced)} ({n_samples} Real, {n_samples} Fake)")
    
    X = df_balanced['text']
    y = df_balanced['label']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Vectorize
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)
    
    # Train
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_tfidf, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_tfidf)
    
    print(f"✅ Model B Accuracy: {accuracy_score(y_test, y_pred):.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['REAL', 'FAKE']))
    
    # Save
    joblib.dump(model, MODEL_FILE)
    joblib.dump(tfidf, VECTORIZER_FILE)
    print(f"\n💾 Saved balanced model and vectorizer.")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # 1. Scrape Real News
    real_data = scrape_real_news()
    
    # 2. Generate Fake News (Match the count of Real news)
    fake_data = generate_fake_news(real_data, len(real_data))
    
    # 3. Combine
    all_data = real_data + fake_data
    df = pd.DataFrame(all_data)
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Check Balance
    print(f"\n📊 Dataset Overview:")
    print(f"Total Samples: {len(df)}")
    print(f"Label Distribution:\n{df['label'].value_counts()}")
    print(f"Source Distribution:\n{df['source'].value_counts()}")
    
    # 4. Save CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved {len(df)} samples to {OUTPUT_FILE}")
    
    # 5. Train Balanced Model
    train_model_balanced(df)