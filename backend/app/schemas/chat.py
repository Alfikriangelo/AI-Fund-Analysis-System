"""
Chat Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message schema"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


class ChatQueryRequest(BaseModel):
    """Chat query request schema"""
    query: str
    fund_id: Optional[int] = None
    conversation_id: Optional[str] = None


class SourceDocument(BaseModel):
    """Source document schema"""
    content: str
    metadata: Dict[str, Any]
    score: Optional[float] = None


class ChatQueryResponse(BaseModel):
    """Chat query response schema"""
    answer: str
    sources: List[SourceDocument] = []
    metrics: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None


class ConversationCreate(BaseModel):
    """Conversation creation schema"""
    fund_id: Optional[int] = None


class Conversation(BaseModel):
    """Conversation schema"""
    conversation_id: str
    fund_id: Optional[int] = None
    messages: List[ChatMessage] = []
    created_at: datetime
    updated_at: datetime
