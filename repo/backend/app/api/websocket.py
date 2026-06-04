from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import asyncio
from typing import Dict, List
from ..core.database import get_db
from ..core.database import SurgerySession
from ..models.schemas import WebSocketMessage

router = APIRouter()

active_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    await websocket.accept()
    
    if session_id not in active_connections:
        active_connections[session_id] = []
    
    active_connections[session_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await broadcast_message(session_id, message, websocket)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "无效的消息格式"}
                }))
            
    except WebSocketDisconnect:
        if session_id in active_connections:
            if websocket in active_connections[session_id]:
                active_connections[session_id].remove(websocket)
            if not active_connections[session_id]:
                del active_connections[session_id]


async def broadcast_message(session_id: str, message: dict, sender: WebSocket):
    if session_id in active_connections:
        for connection in active_connections[session_id]:
            if connection != sender:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    pass


@router.get("/connections/{session_id}")
async def get_connections(session_id: str):
    count = len(active_connections.get(session_id, []))
    return {"session_id": session_id, "active_connections": count}


@router.post("/broadcast/{session_id}")
async def send_broadcast(session_id: str, message: WebSocketMessage):
    if session_id in active_connections:
        for connection in active_connections[session_id]:
            try:
                await connection.send_text(json.dumps({
                    "type": message.type,
                    "data": message.data
                }))
            except Exception:
                pass
        return {"message": f"已广播到 {len(active_connections[session_id])} 个连接"}
    return {"message": "没有活动连接"}
