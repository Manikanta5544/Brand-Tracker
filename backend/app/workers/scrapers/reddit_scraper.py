import praw
from datetime import datetime, timedelta
from typing import List, Dict
from ...core.config import settings


def scrape_reddit(brand_keywords: List[str], limit: int = 100) -> List[Dict]:
    """
    Scrape mentions from Reddit
    """
    mentions = []
    
    try:
        if not settings.REDDIT_CLIENT_ID:
            print("Reddit API credentials not configured")
            return generate_mock_reddit_mentions(brand_keywords, limit)
        
        reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT
        )
        
        # Search for brand mentions
        for keyword in brand_keywords:
            for submission in reddit.subreddit('all').search(keyword, limit=limit, time_filter='day'):
                mentions.append({
                    'text': f"{submission.title} {submission.selftext}",
                    'source': 'reddit',
                    'author': str(submission.author),
                    'url': f"https://reddit.com{submission.permalink}",
                    'timestamp': datetime.fromtimestamp(submission.created_utc)
                })
                
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list()[:5]:
                    mentions.append({
                        'text': comment.body,
                        'source': 'reddit',
                        'author': str(comment.author),
                        'url': f"https://reddit.com{comment.permalink}",
                        'timestamp': datetime.fromtimestamp(comment.created_utc)
                    })
        
        return mentions[:limit]
    
    except Exception as e:
        print(f"Reddit scraping error: {e}")
        return generate_mock_reddit_mentions(brand_keywords, limit)


def generate_mock_reddit_mentions(brand_keywords: List[str], limit: int = 10) -> List[Dict]:
    mock_texts = [
        f"Just tried {brand_keywords[0]} and I'm impressed! Great product.",
        f"Has anyone else had issues with {brand_keywords[0]} customer service?",
        f"Comparing {brand_keywords[0]} to competitors - thoughts?",
        f"{brand_keywords[0]} pricing seems a bit high, but quality is good.",
        f"Love the new features in {brand_keywords[0]}!",
        f"Disappointed with my {brand_keywords[0]} experience.",
        f"Is {brand_keywords[0]} worth the investment?",
        f"{brand_keywords[0]} support team was very helpful!",
        f"Thinking about switching to {brand_keywords[0]}.",
        f"Anyone know when {brand_keywords[0]} will add feature X?",
    ]
    
    mentions = []
    for i, text in enumerate(mock_texts[:limit]):
        mentions.append({
            'text': text,
            'source': 'reddit',
            'author': f'user_{i}',
            'url': f'https://reddit.com/r/example/comments/mock_{i}',
            'timestamp': datetime.utcnow() - timedelta(hours=i)
        })
    
    return mentions