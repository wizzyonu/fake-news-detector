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
import joblib

# === CONFIGURATION ===
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Define multiple sources
SOURCES = {
    'Punch NG': {
        'url_template': 'https://punchng.com/topics/news/page/{}/',
        'selectors': ['h2.entry-title', 'h3.post-title', 'a.title-link']
    },
    'Vanguard News': {
        'url_template': 'https://vanguardngr.com/category/news/page/{}/',
        'selectors': ['h2.entry-title', 'h3.post-title', 'div.post-title a']
    },
    'Premium Times': {
        'url_template': 'https://www.premiumtimesng.com/news/page/{}/',
        'selectors': ['h2.entry-title', 'h3.post-title', 'div.post-title h2 a']
    },
    'The Cable': {
        'url_template': 'https://www.thecable.ng/category/news/page/{}/',
        'selectors': ['h2.entry-title', 'h3.post-title', 'div.post-title a']
    }
}

MAX_PAGES_PER_SOURCE = 10  # 10 pages * ~15 articles = ~150 per source. Total ~600 Real samples.
OUTPUT_FILE = 'multi_source_nigerian_news_1k.csv'
MODEL_FILE = 'model_b_multi_source.pkl'
VECTORIZER_FILE = 'tfidf_vec_multi_source.pkl'

# === 1. SCRAPE REAL NEWS FROM MULTIPLE SOURCES ===
def scrape_real_news():
    all_articles = []
    
    for source_name, config in SOURCES.items():
        print(f"\n🕷️ Scraping REAL News from {source_name}...")
        count = 0
        for page in range(1, MAX_PAGES_PER_SOURCE + 1):
            url = config['url_template'].format(page)
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code != 200: 
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Try specific selectors first, then fallback
                titles = []
                for selector in config['selectors']:
                    elements = soup.select(selector)
                    if elements:
                        titles = [el.get_text(strip=True) for el in elements]
                        break
                
                if not titles: # Fallback
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
                
                if count >= 150: break # Get ~150 from each source
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                continue
                
    print(f"✅ Total Real Samples Collected: {len(all_articles)}")
    return all_articles

# === 2. GENERATE SYNTHETIC FAKE NEWS (Augmentation) ===
def generate_fake_news(real_articles):
    fake_articles = []
    print("\n🎭 Generating SYNTHETIC FAKE News via Augmentation...")
    
    prefixes = ["SHOCKING!!! ", "BREAKING NEWS: ", "URGENT SHARE NOW: ", "YOU WON'T BELIEVE: ", "CONFIRMED!!! "]
    suffixes = [" SHARE TO ALL GROUPS!", " FORWARD IMMEDIATELY!", " DON'T IGNORE THIS!", " !!!", " READ AND SHARE!"]
    
    # We need ~500 Fake samples to balance the ~600 Real ones
    for i in range(500):
        # Pick a random real headline to transform
        base_article = random.choice(real_articles)
        original_text = base_article['text']
        
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        # Create variation
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

# === 3. TRAIN MODEL B ===
def train_model(df):
    print("\n--- 🧠 Training Model B (Logistic Regression) on Multi-Source Data ---")
    
    X = df['text']
    y = df['label']
    
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
    print(f"\n💾 Saved multi-source model and vectorizer.")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # 1. Scrape Real News from 4 Sources
    real_data = scrape_real_news()
    
    # 2. Generate Fake News
    fake_data = generate_fake_news(real_data)
    
    # 3. Combine
    all_data = real_data + fake_data
    df = pd.DataFrame(all_data)
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Check Balance & Sources
    print(f"\n📊 Dataset Overview:")
    print(f"Total Samples: {len(df)}")
    print(f"Label Distribution:\n{df['label'].value_counts()}")
    print(f"Source Distribution:\n{df['source'].value_counts()}")
    
    # 4. Save CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved {len(df)} samples to {OUTPUT_FILE}")
    
    # 5. Train
    train_model(df)