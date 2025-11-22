from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import logging
import asyncio

from app.core.database import get_db
from app.models.mention import Mention

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/daily")
async def get_daily_summary(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:

    try:
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            target_date = datetime.now(timezone.utc).date()
        
        start_time = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_time = start_time + timedelta(days=1)
        
        mentions_result, sentiment_result, sources_result, topics_result, toxicity_result = await asyncio.gather(
            db.execute(select(Mention).where(
                and_(Mention.timestamp >= start_time, Mention.timestamp < end_time)
            ).order_by(desc(Mention.timestamp))),
            db.execute(select(Mention.sentiment, func.count(Mention.id))
                .where(and_(Mention.timestamp >= start_time, Mention.timestamp < end_time))
                .group_by(Mention.sentiment)),
            db.execute(select(Mention.source, func.count(Mention.id))
                .where(and_(Mention.timestamp >= start_time, Mention.timestamp < end_time))
                .group_by(Mention.source).order_by(func.count(Mention.id).desc()).limit(5)),
            db.execute(select(Mention.topic, func.count(Mention.id))
                .where(and_(Mention.timestamp >= start_time, Mention.timestamp < end_time, Mention.topic.isnot(None)))
                .group_by(Mention.topic).order_by(func.count(Mention.id).desc()).limit(5)),
            db.execute(select(func.count(Mention.id))
                .where(and_(Mention.timestamp >= start_time, Mention.timestamp < end_time, Mention.is_toxic == True)))
        )
        
        mentions = mentions_result.scalars().all()
        
        if not mentions:
            return {
                "data": {
                    "date": start_time.date().isoformat(),
                    "summary": "No brand mentions found for this date.",
                    "mention_count": 0,
                    "sources": [],
                    "sentiment_breakdown": {},
                    "topics": [],
                    "toxic_count": 0,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        
        sentiment_breakdown = {row[0] or 'neutral': row[1] for row in sentiment_result}
        top_sources = [{"source": row[0], "count": row[1]} for row in sources_result]
        topics = [{"topic": row[0], "count": row[1]} for row in topics_result if row[0]]
        toxic_count: int = toxicity_result.scalar() or 0
        
        summary = _generate_fallback_summary(mentions, sentiment_breakdown, top_sources, toxic_count)
        
        return {
            "data": {
                "date": start_time.date().isoformat(),
                "summary": summary,
                "summary_type": "automated",
                "mention_count": len(mentions),
                "sources": top_sources,
                "sentiment_breakdown": sentiment_breakdown,
                "topics": topics,
                "toxic_count": toxic_count,
                "positive_count": sentiment_breakdown.get('positive', 0),
                "negative_count": sentiment_breakdown.get('negative', 0),
                "neutral_count": sentiment_breakdown.get('neutral', 0),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating daily summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate daily summary")


@router.get("/weekly")
async def get_weekly_summary(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    

    try:
        if start_date:
            try:
                target_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            today = datetime.now(timezone.utc).date()
            target_date = today - timedelta(days=today.weekday())
        
        start_time = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_time = start_time + timedelta(days=7)
        
        mentions_result, sentiment_result, sources_result, daily_breakdown = await asyncio.gather(
            db.execute(select(Mention).where(
                and_(Mention.timestamp >= start_time, Mention.timestamp < end_time)
            ).order_by(desc(Mention.timestamp))),
            db.execute(select(Mention.sentiment, func.count(Mention.id))
                .where(and_(Mention.timestamp >= start_time, Mention.timestamp < end_time))
                .group_by(Mention.sentiment)),
            db.execute(select(Mention.source, func.count(Mention.id))
                .where(and_(Mention.timestamp >= start_time, Mention.timestamp < end_time))
                .group_by(Mention.source).order_by(func.count(Mention.id).desc()).limit(5)),
            _get_daily_breakdown(start_time, end_time, db)
        )
        
        mentions = mentions_result.scalars().all()
        sentiment_breakdown = {row[0] or 'neutral': row[1] for row in sentiment_result}
        top_sources = [{"source": row[0], "count": row[1]} for row in sources_result]
        
        return {
            "data": {
                "period": f"{start_time.date().isoformat()} to {(end_time - timedelta(days=1)).date().isoformat()}",
                "mention_count": len(mentions),
                "sentiment_breakdown": sentiment_breakdown,
                "top_sources": top_sources,
                "daily_breakdown": daily_breakdown,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating weekly summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate weekly summary")


@router.get("/trending-now")
async def get_trending_summary(
    time_window: str = Query("24h", regex="^(1h|6h|24h)$"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    try:
        hours_map = {"1h": 1, "6h": 6, "24h": 24}
        hours = hours_map.get(time_window, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        trending_result = await db.execute(
            select(
                Mention.topic,
                func.count(Mention.id).label('count'),
                func.avg(Mention.engagement_score).label('avg_engagement'),
                func.avg(Mention.trend_score).label('avg_trend')
            ).where(and_(
                Mention.timestamp >= start_time,
                Mention.is_trending == True,
                Mention.topic.isnot(None)
            )).group_by(Mention.topic)
            .order_by(func.avg(Mention.trend_score).desc())
            .limit(10)
        )
        
        trending_topics: list[dict[str, Any]] = []
        for row in trending_result:
            if row.topic:
                trending_topics.append({
                    "topic": row.topic,
                    "mention_count": row.count,
                    "avg_engagement": round(float(row.avg_engagement or 0), 2),
                    "trend_score": round(float(row.avg_trend or 0), 2)
                })
        
        return {
            "data": {
                "time_window": time_window,
                "trending_topics": trending_topics,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error generating trending summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate trending summary")


async def _get_daily_breakdown(start_time: datetime, end_time: datetime, db: AsyncSession) -> list[dict[str, Any]]:
    try:
        daily_data: list[dict[str, Any]] = []
        current = start_time
        
        while current < end_time:
            next_day = current + timedelta(days=1)
            count: int = await db.scalar(
                select(func.count(Mention.id)).where(
                    and_(Mention.timestamp >= current, Mention.timestamp < next_day)
                )
            ) or 0
            
            sentiment_result = await db.execute(
                select(Mention.sentiment, func.count(Mention.id))
                .where(and_(Mention.timestamp >= current, Mention.timestamp < next_day))
                .group_by(Mention.sentiment)
            )
            sentiment_breakdown = {row[0] or 'neutral': row[1] for row in sentiment_result}
            
            daily_data.append({
                "date": current.date().isoformat(),
                "count": count,
                "sentiment": sentiment_breakdown
            })
            
            current = next_day
        
        return daily_data
    except Exception as e:
        logger.error(f"Error getting daily breakdown: {e}", exc_info=True)
        return []


def _generate_fallback_summary(
    mentions: list[Any],
    sentiment_breakdown: dict[str, int],
    top_sources: list[dict[str, Any]],
    toxic_count: int
) -> str:
   
    total = len(mentions)
    positive = sentiment_breakdown.get('positive', 0)
    negative = sentiment_breakdown.get('negative', 0)
    neutral = sentiment_breakdown.get('neutral', 0)
    top_source = top_sources[0]['source'] if top_sources else "unknown"
    
    summary = f"Daily Summary: {total} total mentions. "
    summary += f"Sentiment: {positive} positive, {negative} negative, {neutral} neutral. "
    summary += f"Top source: {top_source}. "
    
    if toxic_count > 0:
        toxic_percentage = round((toxic_count / total * 100), 1)
        summary += f"⚠{toxic_count} toxic mentions ({toxic_percentage}%). "
    
    if negative > positive * 1.5:
        summary += " Note: Negative mentions are significantly higher than positive ones. "
    elif positive > negative * 2:
        summary += " Great news: Positive mentions are dominating the conversation! "
    
    if total > 100:
        summary += " High volume of mentions detected. "
    
    return summary.strip()