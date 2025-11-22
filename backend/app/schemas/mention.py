from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class MentionBase(BaseModel):
    text: str
    source: str
    author: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[datetime] = None


class MentionCreate(MentionBase):
    pass


class MentionResponse(MentionBase):
    id: int
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    topic: Optional[str] = None
    toxicity: Optional[float] = None
    category: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    type: str
    message: str
    severity: str
    timestamp: datetime
    is_read: int
    
    class Config:
        from_attributes = True


class TopicResponse(BaseModel):
    id: int
    label: str
    keywords: Optional[List[str]] = []
    color: Optional[str] = None
    mention_count: int
    
    class Config:
        from_attributes = True


class StatDailyResponse(BaseModel):
    date: datetime
    positive: int
    neutral: int
    negative: int
    total: int
    avg_sentiment: float
    avg_toxicity: float
    
    class Config:
        from_attributes = True


class SentimentStats(BaseModel):
    positive: int
    neutral: int
    negative: int
    total: int
    avg_score: float


class TrendingTopic(BaseModel):
    label: str
    count: int
    sentiment: str
    keywords: List[str]