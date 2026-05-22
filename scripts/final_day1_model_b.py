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
OUTPUT_FILE = 'balanced_nigerian_news_2k.csv'
MODEL_FILE = 'model_b_balanced.pkl'
VECTORIZER_FILE = 'tfidf_vec_balanced.pkl'

# === 1. SCRAPE REAL NEWS (Premium Times worked best) ===
def scrape_real_news():
    articles = []
    url_template = 'https://www.premiumtimesng.com/news/page/{}/'
    print("🕷️ Scraping REAL News from Premium Times...")
    
    for page in range(1, 20): # Get ~400 real samples
        url = url_template.format(page)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200: continue
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Adjust selector based on previous success
            titles = soup.find_all('h2', class_='entry-title') 
            if not titles: titles = soup.find_all('a', href=True) # Fallback
            
            for t in titles:
                txt = t.get_text(strip=True)
                if len(txt) > 15 and len(txt) < 150:
                    articles.append({'text': txt, 'label': 0, 'source': 'PremiumTimes_Real'})
            
            time.sleep(random.uniform(1, 2))
            if len(articles) >= 500: break # Target 500 Real
        except Exception as e:
            continue
    return articles

# === 2. GENERATE SYNTHETIC FAKE NEWS (Data Augmentation) ===
def generate_fake_news(real_articles):
    fake_articles = []
    print(" Generating SYNTHETIC FAKE News via Augmentation...")
    
    # Templates to make news look fake/sensational
    prefixes = [
        "SHOCKING!!! ",
        "BREAKING NEWS: ",
        "URGENT SHARE NOW: ",
        "YOU WON'T BELIEVE: ",
        "CONFIRMED!!! ",
        "FINAL WARNING: "
    ]
    
    suffixes = [
        " SHARE TO ALL GROUPS!",
        " FORWARD IMMEDIATELY!",
        " DON'T IGNORE THIS!",
        " !!!",
        " ???",
        " READ AND SHARE!"
    ]
    
    for article in real_articles:
        original_text = article['text']
        
        # Create 2 variations of fake news for every 1 real news
        for _ in range(2):
            prefix = random.choice(prefixes)
            suffix = random.choice(suffixes)
            
            # 50% chance to modify text slightly, 50% just add prefix/suffix
            if random.random() > 0.5:
                fake_text = f"{prefix}{original_text}{suffix}"
            else:
                # Make it all caps for extra sensationalism
                fake_text = f"{prefix}{original_text.upper()}{suffix}"
                
            fake_articles.append({
                'text': fake_text, 
                'label': 1, 
                'source': 'Synthetic_Fake_Augmented'
            })
            
        if len(fake_articles) >= 500: break # Target 500 Fake

    return fake_articles

# === 3. TRAIN MODEL B ===
def train_model(df):
    print("\n--- 🧠 Training Model B (Logistic Regression) on Balanced Data ---")
    
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
    print(f"\n💾 Saved balanced model and vectorizer.")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # 1. Get Real News
    real_data = scrape_real_news()
    print(f"Found {len(real_data)} Real samples.")
    
    # 2. Generate Fake News
    fake_data = generate_fake_news(real_data)
    print(f"Generated {len(fake_data)} Fake samples.")
    
    # 3. Combine
    all_data = real_data + fake_data
    df = pd.DataFrame(all_data)
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Check Balance
    print(f"\nDataset Balance:\n{df['label'].value_counts()}")
    
    # 4. Save CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Saved {len(df)} balanced samples to {OUTPUT_FILE}")
    
    # 5. Train
    train_model(df)