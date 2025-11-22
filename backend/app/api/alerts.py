from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, update, func
from datetime import datetime, timezone, timedelta
from typing import Any

import logging

from app.core.database import get_db
from app.models.alert import Alert
from app.models.mention import Mention

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/active")
async def get_active_alerts(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = await db.execute(
            select(Alert)
            .where(Alert.is_active == True)
            .order_by(desc(Alert.created_at))
        )
        alerts = result.scalars().all()
        
        spike_alerts = await _check_real_time_spikes(db)
        
        alerts_data: list[dict[str, Any]] = []
        for alert in alerts:
            alerts_data.append({
                "id": alert.id,
                "type": alert.alert_type or "info",
                "severity": alert.severity or "medium",
                "message": alert.message or "",
                "timestamp": alert.created_at.isoformat() if alert.created_at else datetime.now(timezone.utc).isoformat(),
                "resolved": bool(alert.is_resolved),
                "source": alert.source or "system"
            })
        
        all_alerts = alerts_data + spike_alerts
        
        return {
            "alerts": all_alerts,
            "total": len(all_alerts),
            "real_time_alerts": len(spike_alerts)
        }
        
    except Exception as e:
        logger.error(f"Error fetching active alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch active alerts: {str(e)}"
        )


async def _check_real_time_spikes(db: AsyncSession) -> list[dict[str, Any]]:
    try:
        spike_alerts: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(minutes=15)
        previous_start = current_start - timedelta(minutes=15)
        
        current_count: int = await db.scalar(
            select(func.count(Mention.id)).where(Mention.timestamp >= current_start)
        ) or 0
        
        previous_count: int = await db.scalar(
            select(func.count(Mention.id)).where(
                and_(Mention.timestamp >= previous_start, Mention.timestamp < current_start)
            )
        ) or 1
        
        if current_count > previous_count * 3:
            spike_alerts.append({
                "id": f"spike_{int(now.timestamp())}",
                "type": "realtime_volume_spike",
                "severity": "high",
                "message": f"Real-time mention spike detected: {current_count} mentions in 15min",
                "timestamp": now.isoformat(),
                "resolved": False,
                "source": "realtime_monitor"
            })
        
        neg_current: int = await db.scalar(
            select(func.count(Mention.id)).where(
                and_(Mention.timestamp >= current_start, Mention.sentiment == 'negative')
            )
        ) or 0
        
        neg_previous: int = await db.scalar(
            select(func.count(Mention.id)).where(
                and_(
                    Mention.timestamp >= previous_start, 
                    Mention.timestamp < current_start, 
                    Mention.sentiment == 'negative'
                )
            )
        ) or 1
        
        if neg_current > neg_previous * 4:
            spike_alerts.append({
                "id": f"negative_spike_{int(now.timestamp())}",
                "type": "realtime_negative_spike", 
                "severity": "critical",
                "message": "Critical: Negative mentions spiking in real-time",
                "timestamp": now.isoformat(),
                "resolved": False,
                "source": "sentiment_monitor"
            })
            
        return spike_alerts
        
    except Exception as e:
        logger.error(f"Error in real-time spike detection: {str(e)}", exc_info=True)
        return []


@router.post("/{alert_id}/mark-read")
async def mark_alert_read(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        await db.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(is_read=True)
        )
        await db.commit()
        
        return {
            "status": "success", 
            "message": "Alert marked as read"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking alert as read: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to mark alert as read: {str(e)}"
        )