from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.database import get_db, AsyncSessionLocal
from app.models.mention import Mention
from app.models.alert import Alert

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            stats = await get_realtime_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket stats error: {e}")
        manager.disconnect(websocket)

async def get_realtime_stats():
    async with AsyncSessionLocal() as session:
        try:
            recent_start = datetime.now(timezone.utc) - timedelta(minutes=5)
            recent_count = await session.scalar(
                select(func.count(Mention.id)).where(Mention.timestamp >= recent_start)
            ) or 0

            active_alerts = await session.scalar(
                select(func.count(Alert.id)).where(Alert.is_active == True)
            ) or 0

            hour_start = datetime.now(timezone.utc) - timedelta(hours=1)
            sentiment_result = await session.execute(
                select(Mention.sentiment, func.count(Mention.id))
                .where(Mention.timestamp >= hour_start)
                .group_by(Mention.sentiment)
            )
            sentiment_data = {row[0] or 'neutral': row[1] for row in sentiment_result}

            return {
                "type": "realtime_stats",
                "recent_mentions": recent_count,
                "active_alerts": active_alerts,
                "sentiment_breakdown": sentiment_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting realtime stats: {e}")
            return {
                "type": "realtime_stats",
                "error": "Failed to fetch stats",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }