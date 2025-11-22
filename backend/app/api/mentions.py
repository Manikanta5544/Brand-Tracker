from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func, or_
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import logging

from app.core.database import get_db
from app.models.mention import Mention

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def get_mentions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    topic: Optional[str] = None,
    date_range: str = Query("24h"),
    needs_attention: Optional[bool] = None,
    trending_only: Optional[bool] = None,
    is_toxic: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    
    try:
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(date_range, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = select(Mention).where(Mention.timestamp >= start_time)
        count_query = select(func.count(Mention.id)).where(Mention.timestamp >= start_time)
        
        filters: list[Any] = []
        
        if source:
            filters.append(Mention.source == source)
        if sentiment:
            filters.append(Mention.sentiment == sentiment)
        if topic:
            filters.append(Mention.topic == topic)
        if needs_attention is not None:
            filters.append(Mention.needs_attention == needs_attention)
        if trending_only:
            filters.append(Mention.is_trending == True)
        if is_toxic is not None:
            filters.append(Mention.is_toxic == is_toxic)
        if search:
            filters.append(
                or_(
                    Mention.content.ilike(f"%{search}%"),
                    Mention.author.ilike(f"%{search}%"),
                    Mention.brand_mention.ilike(f"%{search}%")
                )
            )
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        total: int = await db.scalar(count_query) or 0
        offset = (page - 1) * limit
        
        result = await db.execute(
            query.order_by(desc(Mention.timestamp)).offset(offset).limit(limit)
        )
        mentions = result.scalars().all()
        
        mentions_data: list[dict[str, Any]] = [mention.to_dict() for mention in mentions]
        
        return {
            "mentions": mentions_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
                "has_next": page < ((total + limit - 1) // limit),
                "has_prev": page > 1
            },
            "filters": {
                "source": source,
                "sentiment": sentiment,
                "topic": topic,
                "date_range": date_range,
                "needs_attention": needs_attention,
                "is_toxic": is_toxic,
                "trending_only": trending_only
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching mentions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch mentions")


@router.get("/trending")
async def get_trending_mentions(
    limit: int = Query(20, ge=1, le=100),
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    try:
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        result = await db.execute(
            select(Mention)
            .where(and_(Mention.timestamp >= start_time, Mention.is_trending == True))
            .order_by(desc(Mention.trend_score))
            .limit(limit)
        )
        mentions = result.scalars().all()
        
        mentions_data: list[dict[str, Any]] = [mention.to_dict() for mention in mentions]
        
        return {
            "trending_mentions": mentions_data,
            "count": len(mentions_data),
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"Error fetching trending mentions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch trending mentions")


@router.get("/attention-needed")
async def get_mentions_needing_attention(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    
    try:
        result = await db.execute(
            select(Mention)
            .where(and_(
                Mention.needs_attention == True,
                Mention.is_processed == True
            ))
            .order_by(desc(Mention.toxicity))
            .limit(limit)
        )
        mentions = result.scalars().all()
        
        mentions_data: list[dict[str, Any]] = [mention.to_dict() for mention in mentions]
        
        return {
            "attention_needed": mentions_data,
            "count": len(mentions_data)
        }
    except Exception as e:
        logger.error(f"Error fetching mentions needing attention: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch attention-needed mentions")


@router.get("/sources")
async def get_sources_statistics(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    
    try:
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 24)
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        result = await db.execute(
            select(
                Mention.source,
                func.count(Mention.id).label('count'),
                func.avg(Mention.sentiment_score).label('avg_sentiment'),
                func.avg(Mention.engagement_score).label('avg_engagement'),
                func.avg(Mention.toxicity).label('avg_toxicity'),
                func.sum(case((Mention.sentiment == 'positive', 1), else_=0)).label('positive_count'),
                func.sum(case((Mention.sentiment == 'negative', 1), else_=0)).label('negative_count'),
                func.sum(case((Mention.is_toxic == True, 1), else_=0)).label('toxic_count')
            ).where(Mention.timestamp >= start_time)
            .group_by(Mention.source)
            .order_by(func.count(Mention.id).desc())
        )
        
        sources: list[dict[str, Any]] = []
        for row in result:
            if row.source:
                sources.append({
                    "source": row.source,
                    "count": row.count,
                    "avg_sentiment": round(float(row.avg_sentiment or 0), 2),
                    "avg_engagement": round(float(row.avg_engagement or 0), 2),
                    "avg_toxicity": round(float(row.avg_toxicity or 0), 2),
                    "positive_count": row.positive_count or 0,
                    "negative_count": row.negative_count or 0,
                    "toxic_count": row.toxic_count or 0
                })
        
        return {
            "sources": sources,
            "total_sources": len(sources),
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"Error fetching sources: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch sources")


@router.get("/{mention_id}")
async def get_mention_detail(
    mention_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    
    try:
        result = await db.execute(
            select(Mention).where(Mention.id == mention_id)
        )
        mention = result.scalars().first()
        
        if not mention:
            raise HTTPException(status_code=404, detail="Mention not found")
        
        return {
            "mention": mention.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching mention detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch mention detail")


@router.patch("/{mention_id}/attention")
async def update_mention_attention(
    mention_id: int,
    needs_attention: bool,
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    
    try:
        result = await db.execute(
            select(Mention).where(Mention.id == mention_id)
        )
        mention = result.scalars().first()
        
        if not mention:
            raise HTTPException(status_code=404, detail="Mention not found")
        
        mention.needs_attention = needs_attention
        await db.commit()
        await db.refresh(mention)
        
        return {
            "status": "success",
            "mention": mention.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating mention attention: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update mention")


def case(*args: Any, **kwargs: Any) -> Any:
    from sqlalchemy import case
    return case(*args, **kwargs)