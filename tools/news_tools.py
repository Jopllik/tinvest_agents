import urllib.request
from xml.etree import ElementTree as ET
from urllib.parse import urlparse
from typing import List, Dict


def fetch_rss_feed(url: str = "https://www.interfax.ru/rss.asp") -> List[Dict]:
    """Fetch and parse RSS news from Interfax or TASS (uses urllib, no extra deps)."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            xml_data = response.read().decode('utf-8')
        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall('.//item')[:5]:  # top 5 news
            title = item.find('title').text or ''
            description = item.find('description').text or ''
            link = item.find('link').text or ''
            items.append({
                'title': title,
                'description': description,
                'link': link,
                'sentiment': analyze_sentiment(title + ' ' + description)
            })
        return items
    except Exception as e:
        print(f"RSS fetch error: {e}")
        return [{'title': 'Mock news', 'description': 'No critical events', 'sentiment': 'neutral'}]


def analyze_sentiment(text: str) -> str:
    """Simple keyword-based sentiment for news (positive/negative/neutral)."""
    text = text.lower()
    if any(word in text for word in ['рост', 'прибыль', 'позитив', 'рекомендация покупать']):
        return 'positive'
    if any(word in text for word in ['падение', 'убыток', 'риск', 'проблемы', 'штраф']):
        return 'negative'
    return 'neutral'


def get_news_for_tickers(tickers: List[str] = None) -> Dict:
    """Get relevant news for portfolio tickers."""
    news = fetch_rss_feed()
    if tickers:
        relevant = [n for n in news if any(t.lower() in n['title'].lower() or t.lower() in n['description'].lower() for t in tickers)]
        return {'news': relevant or news, 'summary': 'No critical events for portfolio.'}
    return {'news': news, 'summary': 'Market news analyzed. Follow SMA signals.'}
