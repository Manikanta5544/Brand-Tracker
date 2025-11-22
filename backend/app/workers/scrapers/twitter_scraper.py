import tweepy
from datetime import datetime, timedelta
from typing import List, Dict
from ...core.config import settings


def scrape_twitter(brand_keywords: List[str], limit: int = 100) -> List[Dict]:
    mentions = []
    
    try:
        if not settings.TWITTER_BEARER_TOKEN:
            print("Twitter API credentials not configured")
            return generate_mock_twitter_mentions(brand_keywords, limit)
        
        client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)
        
        # Search for brand mentions
        query = ' OR '.join(brand_keywords)
        tweets = client.search_recent_tweets(
            query=query,
            max_results=min(limit, 100),
            tweet_fields=['created_at', 'author_id', 'public_metrics']
        )
        
        if tweets.data:
            for tweet in tweets.data:
                mentions.append({
                    'text': tweet.text,
                    'source': 'twitter',
                    'author': str(tweet.author_id),
                    'url': f"https://twitter.com/i/web/status/{tweet.id}",
                    'timestamp': tweet.created_at
                })
        
        return mentions
    
    except Exception as e:
        print(f"Twitter scraping error: {e}")
        return generate_mock_twitter_mentions(brand_keywords, limit)
        


def generate_mock_twitter_mentions(brand_keywords: List[str], limit: int = 10) -> List[Dict]:
    mock_texts = [
        f"Really enjoying {brand_keywords[0]}! 🎉",
        f"Not happy with {brand_keywords[0]} lately 😞",
        f"Shoutout to {brand_keywords[0]} for excellent service! 👏",
        f"{brand_keywords[0]} needs to improve their app",
        f"Best decision was switching to {brand_keywords[0]}",
        f"Anyone else having problems with {brand_keywords[0]}?",
        f"{brand_keywords[0]} just released a great update!",
        f"Considering {brand_keywords[0]} vs alternatives",
        f"{brand_keywords[0]} customer support is top-notch",
        f"Disappointed with {brand_keywords[0]} pricing",
    ]
    
    mentions = []
    for i, text in enumerate(mock_texts[:limit]):
        mentions.append({
            'text': text,
            'source': 'twitter',
            'author': f'@user{i}',
            'url': f'https://twitter.com/user{i}/status/mock{i}',
            'timestamp': datetime.utcnow() - timedelta(minutes=i*30)
        })
    
    return mentions