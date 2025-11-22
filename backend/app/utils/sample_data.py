from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta
import random
from app.models.mention import Mention
from app.models.alert import Alert

async def create_sample_data(db: AsyncSession):
    try:
        result = await db.execute(select(Mention))
        existing_mentions = result.scalars().all()
        
        if existing_mentions:
            return
        
        await db.execute(delete(Mention))
        await db.execute(delete(Alert))
        await db.commit()
        
        sources = ["reddit", "twitter", "news", "forum", "blog"]
        sentiments = ["positive", "negative", "neutral"]
        topics = ["support", "feedback", "complaint", "praise", "feature_request", "bug_report"]
        brands = ["BrandX", "YourBrand", "ProductY", "ServiceZ"]
        authors = ["john_doe", "sarah_smith", "tech_enthusiast", "customer_advocate", "industry_expert"]
        
        mentions = []
        base_time = datetime.utcnow()
        
        for i in range(50):
            hours_ago = random.randint(0, 72)
            minutes_ago = random.randint(0, 59)
            mention_time = base_time - timedelta(hours=hours_ago, minutes=minutes_ago)
            
            sentiment = random.choices(sentiments, weights=[0.3, 0.1, 0.6])[0]
            
            content_templates = {
                "positive": [
                    f"Really loving {random.choice(brands)}! The service is amazing.",
                    f"Great experience with {random.choice(brands)}. Highly recommended!",
                ],
                "negative": [
                    f"Having issues with {random.choice(brands)}. The support is slow.",
                    f"Disappointed with {random.choice(brands)}'s recent update.",
                ],
                "neutral": [
                    f"Has anyone tried {random.choice(brands)}'s new feature?",
                    f"Looking for reviews about {random.choice(brands)}.",
                ]
            }
            
            content = random.choice(content_templates[sentiment])
            
            mention = Mention(
                source=random.choice(sources),
                author=random.choice(authors),
                content=content,
                sentiment=sentiment,
                sentiment_score=random.uniform(0.7, 0.95) if sentiment == "positive" else 
                              random.uniform(0.1, 0.3) if sentiment == "negative" else 
                              random.uniform(0.4, 0.6),
                topic=random.choice(topics),
                category="general",
                timestamp=mention_time,
                engagement_score=random.uniform(10, 100),
                url=f"https://{random.choice(sources)}.com/post/{i}",
                brand_mention=random.choice(brands),
                is_trending=random.random() < 0.2,
                needs_attention=random.random() < 0.1,
                keywords=[random.choice(brands), sentiment]
            )
            mentions.append(mention)
        
        db.add_all(mentions)
        
        alerts = [
            Alert(
                alert_type="volume_spike",
                severity="high",
                message="Mention volume increased by 150% in the last hour",
                source="system",
                is_active=True,
                metadata={"current_count": 45, "previous_count": 18}
            ),
            Alert(
                alert_type="negative_sentiment_spike",
                severity="critical", 
                message="Negative mentions have doubled in the last 2 hours",
                source="sentiment_analyzer",
                is_active=True,
                metadata={"current_negative": 12, "previous_negative": 6}
            )
        ]
        
        db.add_all(alerts)
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        raise