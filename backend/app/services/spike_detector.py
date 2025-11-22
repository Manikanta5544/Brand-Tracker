from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional, Any
from app.models.mention import Mention

settings = __import__('app.core.config', fromlist=['settings']).settings
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SpikeDetector:

    def __init__(self) -> None:
        self.threshold_multiplier = settings.SPIKE_THRESHOLD_MULTIPLIER

    async def detect_spike(self, db: AsyncSession, hours: int = 24) -> dict[str, Any]:
        try:
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            stmt = select(func.count(Mention.id)).where(
                Mention.timestamp >= current_hour
            )
            result = await db.execute(stmt)
            current_count: int = result.scalar() or 0

            start_time = datetime.utcnow() - timedelta(hours=hours)
            stmt = select(
                func.date_trunc('hour', Mention.timestamp).label('hour'),
                func.count(Mention.id).label('count')
            ).where(
                Mention.timestamp >= start_time,
                Mention.timestamp < current_hour
            ).group_by('hour')

            result = await db.execute(stmt)
            historical_counts = [row.count for row in result]

            if len(historical_counts) < 3:
                return {
                    'is_spike': False,
                    'current_count': current_count,
                    'mean': 0.0,
                    'std': 0.0,
                    'threshold': 0.0
                }

            mean = float(np.mean(historical_counts))
            std = float(np.std(historical_counts))
            threshold = mean + (self.threshold_multiplier * std)

            is_spike = current_count > threshold

            return {
                'is_spike': is_spike,
                'current_count': current_count,
                'mean': mean,
                'std': std,
                'threshold': threshold
            }
        except Exception as e:
            logger.error(f"Spike detection error: {e}", exc_info=True)
            return {
                'is_spike': False,
                'current_count': 0,
                'mean': 0.0,
                'std': 0.0,
                'threshold': 0.0
            }


_spike_detector: Optional[SpikeDetector] = None


def get_spike_detector() -> SpikeDetector:
    global _spike_detector
    if _spike_detector is None:
        _spike_detector = SpikeDetector()
    return _spike_detector