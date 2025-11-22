from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from datetime import datetime, timezone, timedelta
from typing import Any
import logging
import asyncio

from app.core.database import get_db
from app.models.mention import Mention

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    try:
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        total_mentions, sentiment_counts, sources_result, recent_mentions, spike_alerts, trending_topics = await asyncio.gather(
            _get_total_mentions(start_time, db),
            _get_sentiment_breakdown(start_time, db),
            _get_top_sources(start_time, db),
            _get_recent_mentions(db),
            _check_spike_alerts(start_time, db),
            _get_trending_topics(start_time, db)
        )
        
        positive = sentiment_counts.get('positive', 0)
        negative = sentiment_counts.get('negative', 0)
        total_scored = positive + negative
        sentiment_score = round((positive / total_scored * 100), 2) if total_scored > 0 else 50.0
        
        mentions_over_time = await _generate_time_series(start_time, hours, db)
        
        return {
            "total_mentions": total_mentions,
            "positive_mentions": positive,
            "negative_mentions": negative,
            "neutral_mentions": sentiment_counts.get('neutral', 0),
            "sentiment_score": sentiment_score,
            "recent_mentions": recent_mentions,
            "top_sources": [row[0] for row in sources_result],
            "mentions_over_time": mentions_over_time,
            "spike_alerts": spike_alerts,
            "trending_topics": trending_topics,
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"Error in dashboard stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")


@router.get("/sentiment/breakdown")
async def get_sentiment_breakdown(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    try:
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        sentiment_counts = await _get_sentiment_breakdown(start_time, db)
        total = sum(sentiment_counts.values())
        
        breakdown = {
            sentiment: {
                "count": count,
                "percentage": round((count / total * 100), 2) if total > 0 else 0
            }
            for sentiment, count in sentiment_counts.items()
        }
        
        return {
            "breakdown": breakdown,
            "total": total,
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"Error getting sentiment breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch sentiment breakdown")


@router.get("/sources/performance")
async def get_sources_performance(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    try:
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        sources_result = await _get_top_sources(start_time, db)
        
        sources: list[dict[str, Any]] = []
        for source, count, avg_sentiment, avg_engagement in sources_result:
            sources.append({
                "source": source,
                "mention_count": count,
                "avg_sentiment_score": round(float(avg_sentiment or 0), 2),
                "avg_engagement_score": round(float(avg_engagement or 0), 2)
            })
        
        return {
            "sources": sources,
            "total_sources": len(sources),
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"Error getting sources performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch sources performance")


async def _check_spike_alerts(start_time: datetime, db: AsyncSession) -> list[dict[str, Any]]:
    try:
        previous_start = start_time - timedelta(hours=24)
        current_count: int = await db.scalar(
            select(func.count(Mention.id)).where(Mention.timestamp >= start_time)
        ) or 0
        previous_count: int = await db.scalar(
            select(func.count(Mention.id)).where(
                and_(Mention.timestamp >= previous_start, Mention.timestamp < start_time)
            )
        ) or 1
        
        spike_alerts: list[dict[str, Any]] = []
        if current_count > previous_count * 1.5:
            percentage_increase = ((current_count / previous_count) - 1) * 100
            spike_alerts.append({
                "type": "volume_spike",
                "severity": "high" if percentage_increase > 100 else "medium",
                "message": f"Mentions increased by {percentage_increase:.1f}%",
                "current_period": current_count,
                "previous_period": previous_count,
                "percentage_increase": round(percentage_increase, 2)
            })
        
        return spike_alerts
    except Exception as e:
        logger.error(f"Error in spike detection: {e}", exc_info=True)
        return []


async def _get_trending_topics(start_time: datetime, db: AsyncSession) -> list[dict[str, Any]]:
    try:
        result = await db.execute(select(
            Mention.topic,
            func.count(Mention.id).label('mention_count'),
            func.avg(Mention.engagement_score).label('avg_engagement'),
            func.sum(case((Mention.sentiment == 'positive', 1), else_=0)).label('positive_count'),
            func.sum(case((Mention.sentiment == 'negative', 1), else_=0)).label('negative_count')
        ).where(and_(Mention.timestamp >= start_time, Mention.topic.isnot(None))
        ).group_by(Mention.topic).order_by(func.count(Mention.id).desc()).limit(10))
        
        trending_topics: list[dict[str, Any]] = []
        for row in result:
            if row.topic:
                total = (row.positive_count or 0) + (row.negative_count or 0)
                sentiment_ratio = (row.positive_count or 0) / total if total > 0 else 0.5
                trending_topics.append({
                    "topic": row.topic,
                    "mention_count": row.mention_count,
                    "engagement_score": round(float(row.avg_engagement or 0), 2),
                    "sentiment_ratio": round(sentiment_ratio, 2),
                    "positive_count": row.positive_count or 0,
                    "negative_count": row.negative_count or 0,
                    "trend_score": round(row.mention_count * (row.avg_engagement or 1), 2)
                })
        return trending_topics
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}", exc_info=True)
        return []


async def _get_total_mentions(start_time: datetime, db: AsyncSession) -> int:
    try:
        result = await db.scalar(select(func.count(Mention.id)).where(Mention.timestamp >= start_time))
        return result or 0
    except Exception as e:
        logger.error(f"Error getting total mentions: {e}", exc_info=True)
        return 0


async def _get_sentiment_breakdown(start_time: datetime, db: AsyncSession) -> dict[str, int]:
    try:
        result = await db.execute(select(Mention.sentiment, func.count(Mention.id))
            .where(Mention.timestamp >= start_time).group_by(Mention.sentiment))
        return {(row[0] or 'neutral'): row[1] for row in result}
    except Exception as e:
        logger.error(f"Error getting sentiment breakdown: {e}", exc_info=True)
        return {'neutral': 0, 'positive': 0, 'negative': 0}


async def _get_top_sources(start_time: datetime, db: AsyncSession) -> list[tuple[str, int, float, float]]:
    try:
        result = await db.execute(select(
            Mention.source,
            func.count(Mention.id).label('count'),
            func.avg(Mention.sentiment_score).label('avg_sentiment'),
            func.avg(Mention.engagement_score).label('avg_engagement')
        ).where(Mention.timestamp >= start_time).group_by(Mention.source)
            .order_by(func.count(Mention.id).desc()).limit(10))
        return result.all()
    except Exception as e:
        logger.error(f"Error getting top sources: {e}", exc_info=True)
        return []


async def _get_recent_mentions(db: AsyncSession) -> int:
    try:
        recent_start = datetime.now(timezone.utc) - timedelta(hours=1)
        result = await db.scalar(select(func.count(Mention.id)).where(Mention.timestamp >= recent_start))
        return result or 0
    except Exception as e:
        logger.error(f"Error getting recent mentions: {e}", exc_info=True)
        return 0


async def _generate_time_series(start_time: datetime, hours: int, db: AsyncSession) -> list[dict[str, Any]]:
    try:
        time_series: list[dict[str, Any]] = []
        current = start_time
        now = datetime.now(timezone.utc)
        
        while current <= now:
            next_hour = current + timedelta(hours=1)
            count: int = await db.scalar(select(func.count(Mention.id)).where(
                and_(Mention.timestamp >= current, Mention.timestamp < next_hour)
            )) or 0
            time_series.append({
                "hour": current.strftime('%H:%M'),
                "date": current.strftime('%Y-%m-%d'),
                "count": count
            })
            current = next_hour
        
        return time_series[:24] if hours >= 24 else time_series
    except Exception as e:
        logger.error(f"Error generating time series: {e}", exc_info=True)
        return []