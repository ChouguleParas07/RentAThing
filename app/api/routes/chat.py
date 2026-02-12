from __future__ import annotations

from typing import Annotated, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.core.security import decode_token
from app.db.session import get_db_session
from app.schemas.auth import AuthenticatedUser
from app.schemas.message import MessageCreate, MessageListResponse, MessageRead
from app.services.chat_service import ChatService
from app.services.token_blacklist_service import is_token_blacklisted
from app.db.redis import redis_client
from app.schemas.auth import TokenPayload


router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> ChatService:
    return ChatService(db)


@router.post("/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: MessageCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> MessageRead:
    try:
        return await service.send_message(sender_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/conversations", response_model=MessageListResponse)
async def get_conversation(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[ChatService, Depends(get_chat_service)],
    other_user_id: UUID | None = Query(default=None),
    conversation_id: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> MessageListResponse:
    return await service.get_conversation(
        user_id=current_user.id,
        other_user_id=other_user_id,
        conversation_id=conversation_id,
        skip=skip,
        limit=limit,
    )


class ConnectionManager:
    """In-memory connection manager keyed by conversation."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, conversation_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(conversation_id, []).append(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket) -> None:
        conns = self.active_connections.get(conversation_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active_connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: str, message: dict) -> None:
        for connection in self.active_connections.get(conversation_id, []):
            await connection.send_json(message)


manager = ConnectionManager()


async def _authenticate_websocket(token: str) -> TokenPayload:
    """Authenticate a websocket using a bearer token."""

    try:
        raw_payload = decode_token(token)
        payload = TokenPayload.model_validate(raw_payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if await is_token_blacklisted(redis_client, payload.jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    return payload


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str,
) -> None:
    # Token is expected as query param: ?token=Bearer <jwt> or just <jwt>
    jwt_token = token.replace("Bearer ", "").replace("bearer ", "")
    try:
        payload = await _authenticate_websocket(jwt_token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            receiver_id_str = data.get("receiver_id")
            if not content or not receiver_id_str:
                await websocket.send_json({"error": "content and receiver_id are required"})
                continue

            try:
                receiver_id = UUID(receiver_id_str)
            except ValueError:
                await websocket.send_json({"error": "Invalid receiver_id"})
                continue

            # Persist via ChatService
            async with get_db_session() as db:  # type: ignore
                service = ChatService(db)  # ephemeral service per message
                msg = await service.send_message(
                    sender_id=UUID(payload.sub),
                    payload=MessageCreate(
                        receiver_id=receiver_id,
                        content=content,
                        conversation_id=conversation_id,
                    ),
                )

            await manager.broadcast(
                conversation_id,
                {
                    "id": str(msg.id),
                    "sender_id": str(msg.sender_id),
                    "receiver_id": str(msg.receiver_id),
                    "conversation_id": msg.conversation_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)

