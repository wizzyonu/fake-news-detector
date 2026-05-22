# scripts/scrape_nigerian_news.py
"""
Enhanced Nigerian News Scraper - Collects news from 2020-2026
Saves to CSV for retraining your model
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime, timedelta
import json
import os

class NigerianNewsScraper:
    def __init__(self):
        self.sources = {
            'premium_times': {
                'url': 'https://www.premiumtimesng.com',
                'category': 'verified',
                'base_url': 'https://www.premiumtimesng.com/category/news/page/{}/',
                'article_selector': 'article h2 a',
                'content_selector': 'div.entry-content p'
            },
            'punch': {
                'url': 'https://punchng.com',
                'category': 'verified',
                'base_url': 'https://punchng.com/page/{}/',
                'article_selector': 'article h2 a',
                'content_selector': 'div.entry-content p'
            },
            'vanguard': {
                'url': 'https://www.vanguardngr.com',
                'category': 'verified',
                'base_url': 'https://www.vanguardngr.com/category/news/page/{}/',
                'article_selector': 'article h2 a',
                'content_selector': 'div.entry-content p'
            },
            'guardian': {
                'url': 'https://guardian.ng',
                'category': 'verified',
                'base_url': 'https://guardian.ng/category/news/page/{}/',
                'article_selector': 'article h2 a',
                'content_selector': 'div.entry-content p'
            }
        }
        
        # Known fake news sources to scrape (for negative examples)
        self.fake_sources = {
            'nairaland_fake': {
                'search_terms': [
                    'breaking news share',
                    'urgent share now',
                    'confirmed',
                    'shocking news',
                    'viral alert'
                ]
            }
        }
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
    
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        }
    
    def scrape_verified_news(self, source_name, pages=50, start_year=2020):
        """Scrape verified news from reputable Nigerian sources"""
        source = self.sources[source_name]
        articles = []
        
        print(f"\n📰 Scraping {source_name} (2020-2026)...")
        
        for page in range(1, pages + 1):
            try:
                url = source['base_url'].format(page)
                response = requests.get(url, headers=self.get_headers(), timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find article links
                article_links = soup.select(source['article_selector'])
                
                for link in article_links[:10]:  # Limit per page
                    href = link.get('href')
                    if not href:
                        continue
                    
                    if not href.startswith('http'):
                        href = source['url'] + href
                    
                    # Scrape individual article
                    article_data = self.scrape_article(href, source_name)
                    
                    if article_data and len(article_data['text']) > 200:
                        # Check if article is from 2020-2026
                        year = self.extract_year(article_data['date'])
                        if year and 2020 <= year <= 2026:
                            article_data['label'] = 0  # REAL news
                            articles.append(article_data)
                            print(f"   ✅ Scraped: {article_data['title'][:50]}... ({year})")
                    
                    time.sleep(random.uniform(1, 3))
                
                print(f"   Page {page}: Found {len(article_links)} articles")
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"   Error on page {page}: {e}")
                continue
        
        return articles
    
    def scrape_article(self, url, source_name):
        """Scrape individual article content"""
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get title
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.text.strip() if title_tag else ""
            
            # Get date
            date = self.extract_date(soup)
            
            # Get content
            paragraphs = soup.select('div.entry-content p, article p, .post-content p')
            text = ' '.join([p.text.strip() for p in paragraphs if len(p.text) > 50])
            
            if len(text) < 100:
                # Fallback to all paragraphs
                all_paragraphs = soup.find_all('p')
                text = ' '.join([p.text.strip() for p in all_paragraphs if len(p.text) > 50])
            
            return {
                'title': title,
                'text': text[:3000],  # Limit length
                'date': date,
                'source': source_name,
                'url': url
            }
            
        except Exception as e:
            print(f"   Error scraping {url}: {e}")
            return None
    
    def extract_date(self, soup):
        """Extract publication date from article"""
        # Common date selectors
        date_selectors = [
            'time', '.date', '.publish-date', '.post-date',
            'meta[property="article:published_time"]',
            'meta[name="publish-date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if selector.startswith('meta'):
                    date_str = element.get('content', '')
                else:
                    date_str = element.text.strip()
                
                if date_str:
                    return date_str
        
        return None
    
    def extract_year(self, date_str):
        """Extract year from date string"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%b %d, %Y', '%d %b %Y', '%Y/%m/%d']:
                try:
                    dt = datetime.strptime(date_str[:10], fmt)
                    return dt.year
                except:
                    continue
            
            # Look for 4-digit year
            import re
            year_match = re.search(r'20\d{2}', date_str)
            if year_match:
                return int(year_match.group())
        except:
            pass
        
        return None
    
    def generate_fake_news_samples(self, count=1000):
        """Generate synthetic fake news samples (for training)"""
        fake_templates = [
            "BREAKING NEWS: SHOCKING!!! {subject} {action} {detail}. SHARE TO ALL GROUPS! DON'T IGNORE THIS!",
            "URGENT SHARE NOW: CONFIRMED!!! {subject} {action} {detail}. Forward immediately to all WhatsApp groups!",
            "YOU WON'T BELIEVE: {subject} {action} {detail}. READ AND SHARE!!!",
            "CONFIRMED!!! {subject} {action} {detail}. This is a MUST READ! Share now!"
        ]
        
        subjects = [
            "President Tinubu", "CBN", "EFCC", "INEC", "APC", "PDP",
            "Governor Sanwo-Olu", "Pastor Adeboye", "Dangote", "Bishop Oyedepo"
        ]
        
        actions = [
            "resigns", "arrested", "fired", "sentenced to prison", "dies suddenly",
            "bans WhatsApp", "suspends all banks", "announces new tax", "flees country"
        ]
        
        details = [
            "effective immediately", "after emergency meeting", "in shocking development",
            "confidential sources confirm", "leaked documents reveal", "breaking overnight"
        ]
        
        fake_articles = []
        
        print(f"\n📝 Generating {count} synthetic fake news samples...")
        
        for i in range(count):
            template = random.choice(fake_templates)
            subject = random.choice(subjects)
            action = random.choice(actions)
            detail = random.choice(details)
            
            text = template.format(subject=subject, action=action, detail=detail)
            
            # Add variety with random punctuation
            if random.random() > 0.5:
                text = text.upper()
            
            fake_articles.append({
                'text': text,
                'label': 1,  # FAKE
                'source': 'synthetic',
                'type': 'generated_fake'
            })
        
        print(f"   ✅ Generated {len(fake_articles)} fake samples")
        return fake_articles
    
    def scrape_news_by_keyword(self, keyword, max_articles=100):
        """Scrape news by keyword (using Google News RSS or similar)"""
        articles = []
        
        # You can implement Google News RSS scraping here
        # This is a placeholder - you can use newsapi.org or similar
        print(f"\n🔍 Searching for '{keyword}' news...")
        
        # Example using NewsAPI (you'd need an API key)
        # api_key = os.getenv('NEWS_API_KEY')
        # url = f'https://newsapi.org/v2/everything?q={keyword}&apiKey={api_key}'
        
        return articles

def main():
    """Main scraping function"""
    print("=" * 70)
    print("🚀 NIGERIAN NEWS SCRAPER (2020-2026)")
    print("=" * 70)
    
    scraper = NigerianNewsScraper()
    
    all_articles = []
    
    # 1. Scrape verified news sources
    verified_sources = ['premium_times', 'punch', 'vanguard', 'guardian']
    
    for source in verified_sources:
        articles = scraper.scrape_verified_news(source, pages=30)
        all_articles.extend(articles)
        print(f"   Total from {source}: {len(articles)} articles")
    
    # 2. Generate synthetic fake news for balance
    fake_articles = scraper.generate_fake_news_samples(count=2000)
    all_articles.extend(fake_articles)
    
    # 3. Convert to DataFrame
    df = pd.DataFrame(all_articles)
    
    # 4. Clean and deduplicate
    df = df.drop_duplicates(subset=['text'])
    df = df[df['text'].str.len() > 100]
    
    print(f"\n📊 Total collected: {len(df)} unique articles")
    print(f"   REAL news: {len(df[df['label']==0])}")
    print(f"   FAKE news: {len(df[df['label']==1])}")
    
    # 5. Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = f'nigerian_news_{timestamp}.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Saved to: {csv_path}")
    
    return df

if __name__ == "__main__":
    df = main()