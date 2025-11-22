import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict


def scrape_news(brand_keywords: List[str], limit: int = 50) -> List[Dict]:
    """
    Scrape mentions from Google News RSS
    """
    mentions = []
    
    try:
        for keyword in brand_keywords:
            # Google News RSS feed
            rss_url = f"https://news.google.com/rss/search?q={keyword}&hl=en-US&gl=US&ceid=US:en"
            
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:limit]:
                mentions.append({
                    'text': f"{entry.title}. {entry.get('summary', '')}",
                    'source': 'news',
                    'author': entry.get('source', {}).get('title', 'Unknown'),
                    'url': entry.link,
                    'timestamp': datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.utcnow()
                })
        
        return mentions[:limit]
    
    except Exception as e:
        print(f"News scraping error: {e}")
        return generate_mock_news_mentions(brand_keywords, limit)


def generate_mock_news_mentions(brand_keywords: List[str], limit: int = 10) -> List[Dict]:
    """
    Generate mock news mentions for testing
    """
    mock_articles = [
        {
            'title': f"{brand_keywords[0]} Announces Major Product Update",
            'summary': "The company unveiled new features aimed at improving user experience."
        },
        {
            'title': f"{brand_keywords[0]} Faces Customer Complaints Over Service",
            'summary': "Several users have reported issues with the platform's reliability."
        },
        {
            'title': f"Industry Analysis: {brand_keywords[0]} vs Competitors",
            'summary': "Experts weigh in on how the company stacks up against rivals."
        },
        {
            'title': f"{brand_keywords[0]} Wins Innovation Award",
            'summary': "The company was recognized for its groundbreaking technology."
        },
        {
            'title': f"{brand_keywords[0]} Expands to New Markets",
            'summary': "The company announced plans to enter three new regions."
        },
        {
            'title': f"Customer Review: My Experience with {brand_keywords[0]}",
            'summary': "A detailed look at the pros and cons of using the service."
        },
        {
            'title': f"{brand_keywords[0]} Updates Privacy Policy",
            'summary': "New terms aim to give users more control over their data."
        },
        {
            'title': f"Stock Watch: {brand_keywords[0]} Shares Rise",
            'summary': "Positive earnings report drives investor confidence."
        },
        {
            'title': f"{brand_keywords[0]} Launches Community Initiative",
            'summary': "The company commits to supporting local communities."
        },
        {
            'title': f"Tech Roundup: {brand_keywords[0]} in the News",
            'summary': "A summary of recent developments and announcements."
        },
    ]
    
    mentions = []
    for i, article in enumerate(mock_articles[:limit]):
        mentions.append({
            'text': f"{article['title']}. {article['summary']}",
            'source': 'news',
            'author': f"News Source {i+1}",
            'url': f"https://news.example.com/article/{i}",
            'timestamp': datetime.utcnow() - timedelta(hours=i*2)
        })
    
    return mentions