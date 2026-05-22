# scripts/scrape_nairaland_factcheckers_fixed.py
"""
Fixed scraper for Nigerian fact-checkers and forums
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse

class NigerianDataCollectorFixed:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.fake_indicators = [
            'breaking', 'urgent', 'share', 'forward', 'confirmed', 'shocking',
            'must read', 'viral', 'trending', 'alert', 'warning',
            'pls share', 'please share', 'copy and paste'
        ]
        
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def scrape_dubawa_fixed(self):
        """Fixed Dubawa scraper with proper element selection"""
        print("\n" + "=" * 60)
        print("✅ SCRAPING DUBAWA (Fixed)")
        print("=" * 60)
        
        fact_checks = []
        
        # Try different URL patterns
        urls_to_try = [
            "https://dubawa.org/fact-check/",
            "https://dubawa.org/category/fact-check/",
            "https://dubawa.org/fact-check/page/{}"
        ]
        
        for page in range(1, 11):  # Limit to 10 pages for testing
            try:
                if page == 1:
                    url = "https://dubawa.org/fact-check/"
                else:
                    url = f"https://dubawa.org/fact-check/page/{page}/"
                
                print(f"  Fetching page {page}: {url}")
                response = requests.get(url, headers=self.get_headers(), timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors for articles
                articles = soup.find_all('article') or soup.find_all('div', class_='post') or soup.find_all('div', class_='fact-check-item')
                
                if not articles:
                    print(f"  No articles found on page {page}")
                    # Debug: print page title
                    title = soup.find('title')
                    if title:
                        print(f"  Page title: {title.text[:100]}")
                    break
                
                for article in articles:
                    # Extract title/claim
                    title_elem = article.find('h2') or article.find('h3') or article.find('h1')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link = title_elem.find('a')
                    url = link['href'] if link else None
                    
                    if url and not url.startswith('http'):
                        url = urljoin("https://dubawa.org", url)
                    
                    # Look for verdict in various places
                    verdict_text = ""
                    verdict_elem = None
                    
                    # Try different selectors for verdict
                    selectors = [
                        ('span', 'class_', 'verdict'),
                        ('div', 'class_', 'conclusion'),
                        ('div', 'class_', 'fact-check-verdict'),
                        ('span', 'class_', 'rating'),
                        ('div', 'class_', 'verdict-box')
                    ]
                    
                    for tag, attr, value in selectors:
                        if attr == 'class_':
                            verdict_elem = article.find(tag, class_=value)
                        if verdict_elem:
                            break
                    
                    if verdict_elem:
                        verdict_text = verdict_elem.text.lower()
                    else:
                        # Try to find verdict in the text content
                        article_text = article.get_text().lower()
                        if any(word in article_text for word in ['false', 'fake', 'misleading']):
                            verdict_text = 'false'
                        elif any(word in article_text for word in ['true', 'correct']):
                            verdict_text = 'true'
                        else:
                            continue  # Skip if no verdict found
                    
                    # Determine label
                    if any(word in verdict_text for word in ['false', 'fake', 'misleading', 'incorrect', 'hoax']):
                        label = 1  # FAKE
                        verdict_str = "FAKE"
                    elif any(word in verdict_text for word in ['true', 'correct', 'accurate', 'real']):
                        label = 0  # REAL
                        verdict_str = "REAL"
                    else:
                        continue
                    
                    # Get full content if URL available
                    full_text = title
                    if url:
                        content = self.scrape_article_content(url)
                        if content:
                            full_text = content[:3000]
                    
                    fact_checks.append({
                        'text': full_text,
                        'label': label,
                        'verdict': verdict_text[:100],
                        'source': 'dubawa',
                        'url': url
                    })
                    
                    print(f"    {verdict_str}: {title[:60]}...")
                
                print(f"  Page {page}: Found {len(articles)} articles, extracted {len([a for a in articles if a.find('h2')])} fact-checks")
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"  Error on page {page}: {e}")
                continue
        
        print(f"\n✅ Collected {len(fact_checks)} fact-checks from Dubawa")
        return fact_checks
    
    def scrape_article_content(self, url):
        """Extract full article content"""
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple content selectors
            content_selectors = [
                ('div', 'class_', 'entry-content'),
                ('div', 'class_', 'post-content'),
                ('div', 'class_', 'content'),
                ('article', None, None)
            ]
            
            content_div = None
            for tag, attr, value in content_selectors:
                if attr == 'class_':
                    content_div = soup.find(tag, class_=value)
                elif attr is None:
                    content_div = soup.find(tag)
                if content_div:
                    break
            
            if content_div:
                paragraphs = content_div.find_all('p')
                text = ' '.join([p.text.strip() for p in paragraphs if len(p.text) > 30])
                return text[:3000]
            
            return None
            
        except Exception as e:
            print(f"    Error fetching article: {e}")
            return None
    
    def scrape_nairaland_fixed(self, max_pages=5):
        """Fixed Nairaland scraper with correct URL handling"""
        print("\n" + "=" * 60)
        print("🌍 SCRAPING NAIRALAND (Fixed)")
        print("=" * 60)
        
        base_url = "https://www.nairaland.com"
        all_posts = []
        
        sections = ['politics', 'news']  # Reduced for testing
        
        for section in sections:
            print(f"\n📁 Section: {section.upper()}")
            
            for page in range(1, max_pages + 1):
                try:
                    # Correct URL construction
                    url = f"{base_url}/{section}/{page}"
                    print(f"  Fetching: {url}")
                    
                    response = requests.get(url, headers=self.get_headers(), timeout=15)
                    
                    if response.status_code != 200:
                        print(f"  HTTP {response.status_code} - Nairaland might be blocking")
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find topic links - Nairaland specific structure
                    # Topics are usually in div with class 'board' or inside <a> tags
                    topics = []
                    
                    # Try different selectors
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        # Nairaland topic URLs look like: /topic/12345.msg12345#msg12345
                        if re.match(r'^/topic/\d+', href):
                            topics.append(link)
                    
                    if not topics:
                        print(f"  No topics found on page {page}")
                        # Debug: print some links
                        sample_links = soup.find_all('a', limit=10)
                        print(f"  Sample links: {[l.get('href') for l in sample_links if l.get('href')]}")
                        continue
                    
                    print(f"  Found {len(topics)} topics on page {page}")
                    
                    for topic in topics[:10]:  # Limit per page
                        topic_url = urljoin(base_url, topic['href'])
                        topic_title = topic.text.strip()
                        
                        if not topic_title or len(topic_title) < 10:
                            continue
                        
                        is_likely_fake = any(
                            indicator in topic_title.lower() 
                            for indicator in self.fake_indicators
                        )
                        
                        # Scrape the topic
                        topic_data = self.scrape_nairaland_topic_fixed(topic_url)
                        
                        if topic_data:
                            topic_data['title'] = topic_title
                            topic_data['is_likely_fake'] = is_likely_fake
                            topic_data['section'] = section
                            all_posts.append(topic_data)
                            
                            status = "⚠️ LIKELY FAKE" if is_likely_fake else "📝 UNKNOWN"
                            print(f"    {status}: {topic_title[:50]}...")
                        
                        time.sleep(random.uniform(2, 3))  # Be respectful
                    
                    time.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    print(f"  Error on page {page}: {e}")
                    continue
        
        print(f"\n✅ Collected {len(all_posts)} posts from Nairaland")
        return all_posts
    
    def scrape_nairaland_topic_fixed(self, url):
        """Scrape individual Nairaland topic with better error handling"""
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get the main post content - Nairaland specific
            all_text = []
            
            # Try multiple selectors for post content
            selectors = [
                ('div', 'class_', 'narrow'),
                ('td', 'class_', 'post_content'),
                ('div', 'class_', 'post')
            ]
            
            for tag, attr, value in selectors:
                if attr == 'class_':
                    posts = soup.find_all(tag, class_=value)
                else:
                    posts = soup.find_all(tag)
                
                if posts:
                    for post in posts[:2]:
                        text = post.get_text().strip()
                        if len(text) > 50:
                            all_text.append(text)
                    break
            
            if not all_text:
                return None
            
            full_text = ' '.join(all_text)
            
            return {
                'text': full_text[:3000],
                'url': url
            }
            
        except Exception as e:
            print(f"    Error scraping topic: {e}")
            return None
    
    def run_pipeline(self):
        """Run the fixed collection pipeline"""
        print("=" * 70)
        print("🚀 NIGERIAN DATA COLLECTION (FIXED)")
        print("=" * 70)
        
        all_data = []
        
        # 1. Scrape Dubawa
        print("\n📌 Phase 1: Collecting from Dubawa")
        dubawa_data = self.scrape_dubawa_fixed()
        all_data.extend(dubawa_data)
        
        # 2. Scrape Nairaland (optional - may still be blocked)
        print("\n📌 Phase 2: Collecting from Nairaland")
        nairaland_data = self.scrape_nairaland_fixed(max_pages=3)
        
        # 3. Create DataFrame
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Save
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            df.to_csv(f'verified_data_{timestamp}.csv', index=False)
            
            print("\n" + "=" * 70)
            print("📊 COLLECTION SUMMARY")
            print("=" * 70)
            print(f"\n✅ TOTAL VERIFIED DATA: {len(df)} samples")
            if 'label' in df.columns:
                print(f"   REAL: {len(df[df['label']==0])}")
                print(f"   FAKE: {len(df[df['label']==1])}")
            
            return df
        else:
            print("\n❌ No data collected!")
            return None

# Alternative: Use API-based approach
def alternative_data_sources():
    """Suggest alternative data sources"""
    print("\n" + "=" * 60)
    print("📚 ALTERNATIVE DATA SOURCES")
    print("=" * 60)
    print("""
    Since web scraping is challenging, consider these alternatives:
    
    1. **Kaggle Datasets**:
       - "Fake News Detection" (many Nigerian-focused datasets)
       - "COVID-19 Fake News" (includes Nigerian content)
       - Download via: kaggle datasets download
    
    2. **Africa Check API** (if available):
       - https://africacheck.org/fact-checks
       - Check if they offer RSS/API
    
    3. **Pre-built NLP Datasets**:
       - Hugging Face Datasets: search "fake news" "nigeria"
       - pip install datasets
    
    4. **Crowdsourced approach**:
       - Use your existing model to label Nairaland posts
       - Manual verification of a subset
       - Semi-supervised learning
    
    5. **Synthetic Data Generation**:
       - Use LLMs (GPT, Llama) to generate Nigerian-style fake/real news
       - Augment with real headlines
    """)

if __name__ == "__main__":
    print("\n🔧 RUNNING FIXED SCRAPER...\n")
    collector = NigerianDataCollectorFixed()
    data = collector.run_pipeline()
    
    if data is None or len(data) == 0:
        alternative_data_sources()