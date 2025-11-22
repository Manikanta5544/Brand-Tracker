from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON, func
import logging
from app.core.database import Base
from typing import Any

logger = logging.getLogger(__name__)


class Mention(Base):
    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author = Column(String(255), nullable=True, index=True)
    source = Column(String(100), nullable=False, index=True)
    url = Column(Text, nullable=True)
    
    sentiment = Column(String(50), nullable=True, index=True)
    sentiment_score = Column(Float, default=0.0)
    
    topic = Column(String(255), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    keywords = Column(JSON, nullable=True)
    
    toxicity = Column(Float, default=0.0)
    is_toxic = Column(Boolean, default=False, index=True)
    
    engagement_score = Column(Float, default=0.0)
    is_trending = Column(Boolean, default=False, index=True)
    trend_score = Column(Float, default=0.0)
    
    brand_mention = Column(String(255), nullable=True, index=True)
    brand_sentiment = Column(String(50), nullable=True, index=True)
    language = Column(String(10), default='en', index=True)
    
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    is_processed = Column(Boolean, default=False, index=True)
    needs_attention = Column(Boolean, default=False, index=True)

    def to_dict(self) -> dict[str, Any]:
        try:
            return {
                "id": self.id,
                "content": self.content or "",
                "author": self.author,
                "source": self.source,
                "url": self.url,
                "sentiment": self.sentiment or "neutral",
                "sentiment_score": float(self.sentiment_score or 0.0),
                "topic": self.topic,
                "category": self.category,
                "keywords": self.keywords or [],
                "toxicity": float(self.toxicity or 0.0),
                "is_toxic": bool(self.is_toxic),
                "engagement_score": float(self.engagement_score or 0.0),
                "is_trending": bool(self.is_trending),
                "trend_score": float(self.trend_score or 0.0),
                "brand_mention": self.brand_mention,
                "brand_sentiment": self.brand_sentiment,
                "language": self.language or "en",
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "is_processed": bool(self.is_processed),
                "needs_attention": bool(self.needs_attention)
            }
        except Exception as e:
            logger.error(f"Error converting Mention to dict: {e}", exc_info=True)
            return {}

    def __repr__(self) -> str:
        return f"<Mention(id={self.id}, source={self.source}, sentiment={self.sentiment})>"

