"""
Database models for the Realtime Voice Assistant.
Production-ready SQLAlchemy models with proper relationships and indexing.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import json


Base = declarative_base()


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    """Mixin for UUID primary key."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication and personalization."""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    preferences = Column(JSON, default=dict, nullable=False)
    
    # Voice profile settings
    voice_profile = Column(JSON, default=dict, nullable=False)
    voice_activation_enabled = Column(Boolean, default=True, nullable=False)
    preferred_voice_speed = Column(Float, default=1.0, nullable=False)
    preferred_voice_tone = Column(String(50), default="neutral", nullable=False)
    
    # Relationships
    sessions = relationship("VoiceSession", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('preferred_voice_speed >= 0.5 AND preferred_voice_speed <= 2.0'),
        Index('idx_user_active', 'is_active'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "preferences": self.preferences,
            "voice_profile": self.voice_profile,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class VoiceSession(Base, UUIDMixin, TimestampMixin):
    """Voice conversation sessions."""
    __tablename__ = "voice_sessions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_name = Column(String(100), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    
    # Session metrics
    total_duration = Column(Float, default=0.0, nullable=False)
    total_exchanges = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(Integer, default=0, nullable=False)
    
    # Audio settings for this session
    audio_settings = Column(JSON, default=dict, nullable=False)
    
    # Session context and state
    context = Column(JSON, default=dict, nullable=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    exchanges = relationship("VoiceExchange", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'completed', 'terminated')"),
        Index('idx_session_user_status', 'user_id', 'status'),
        Index('idx_session_last_activity', 'last_activity_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "session_name": self.session_name,
            "status": self.status,
            "total_duration": self.total_duration,
            "total_exchanges": self.total_exchanges,
            "total_tokens_used": self.total_tokens_used,
            "created_at": self.created_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat()
        }


class VoiceExchange(Base, UUIDMixin, TimestampMixin):
    """Individual voice exchanges within a session."""
    __tablename__ = "voice_exchanges"
    
    session_id = Column(UUID(as_uuid=True), ForeignKey("voice_sessions.id"), nullable=False, index=True)
    
    # User input
    user_audio_path = Column(String(500), nullable=True)
    user_transcript = Column(Text, nullable=True)
    user_intent = Column(String(100), nullable=True)
    
    # Assistant response
    assistant_text = Column(Text, nullable=True)
    assistant_audio_path = Column(String(500), nullable=True)
    response_type = Column(String(50), default="text", nullable=False)
    
    # Processing metrics
    processing_duration = Column(Float, nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    
    # Tool calls and function executions
    tools_called = Column(JSON, default=list, nullable=False)
    function_results = Column(JSON, default=dict, nullable=False)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    user_feedback = Column(String(20), nullable=True)
    
    # Relationships
    session = relationship("VoiceSession", back_populates="exchanges")
    
    __table_args__ = (
        CheckConstraint("response_type IN ('text', 'audio', 'function_call', 'error')"),
        CheckConstraint("confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)"),
        CheckConstraint("user_feedback IS NULL OR user_feedback IN ('positive', 'negative', 'neutral')"),
        Index('idx_exchange_session_created', 'session_id', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "user_transcript": self.user_transcript,
            "assistant_text": self.assistant_text,
            "response_type": self.response_type,
            "processing_duration": self.processing_duration,
            "tokens_used": self.tokens_used,
            "tools_called": self.tools_called,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat()
        }


class Memory(Base, UUIDMixin, TimestampMixin):
    """Memory storage for both short-term and long-term memory."""
    __tablename__ = "memories"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Memory classification
    memory_type = Column(String(20), nullable=False, index=True)  # short_term, long_term, episodic, semantic
    category = Column(String(50), nullable=True, index=True)
    
    # Memory content
    key = Column(String(200), nullable=False, index=True)
    content = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Memory metadata
    importance_score = Column(Float, default=0.5, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Retention settings
    expires_at = Column(DateTime(timezone=True), nullable=True)
    auto_expire = Column(Boolean, default=False, nullable=False)
    
    # Context and associations
    context_tags = Column(JSON, default=list, nullable=False)
    related_memories = Column(JSON, default=list, nullable=False)
    
    # Source information
    source_session_id = Column(UUID(as_uuid=True), ForeignKey("voice_sessions.id"), nullable=True)
    source_exchange_id = Column(UUID(as_uuid=True), ForeignKey("voice_exchanges.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    __table_args__ = (
        CheckConstraint("memory_type IN ('short_term', 'long_term', 'episodic', 'semantic')"),
        CheckConstraint("importance_score >= 0.0 AND importance_score <= 1.0"),
        UniqueConstraint('user_id', 'key', name='uq_user_memory_key'),
        Index('idx_memory_user_type', 'user_id', 'memory_type'),
        Index('idx_memory_importance', 'importance_score'),
        Index('idx_memory_expires', 'expires_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "memory_type": self.memory_type,
            "category": self.category,
            "key": self.key,
            "content": self.content,
            "summary": self.summary,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "context_tags": self.context_tags,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }


class Task(Base, UUIDMixin, TimestampMixin):
    """Task tracking and management."""
    __tablename__ = "tasks"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Task identification
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    
    # Task status and priority
    status = Column(String(20), default="pending", nullable=False, index=True)
    priority = Column(String(10), default="medium", nullable=False)
    
    # Task timing
    due_date = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    actual_duration = Column(Integer, nullable=True)  # in minutes
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Task metadata
    tags = Column(JSON, default=list, nullable=False)
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # Context and relationships
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    project_name = Column(String(100), nullable=True)
    
    # Source information
    created_from_session_id = Column(UUID(as_uuid=True), ForeignKey("voice_sessions.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    subtasks = relationship("Task", backref="parent_task", remote_side="Task.id")
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled', 'on_hold')"),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100"),
        Index('idx_task_user_status', 'user_id', 'status'),
        Index('idx_task_due_date', 'due_date'),
        Index('idx_task_priority', 'priority'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "status": self.status,
            "priority": self.priority,
            "progress_percentage": self.progress_percentage,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_duration": self.estimated_duration,
            "tags": self.tags,
            "project_name": self.project_name,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ToolExecution(Base, UUIDMixin, TimestampMixin):
    """Log of tool executions and function calls."""
    __tablename__ = "tool_executions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("voice_sessions.id"), nullable=True, index=True)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey("voice_exchanges.id"), nullable=True, index=True)
    
    # Tool information
    tool_name = Column(String(100), nullable=False, index=True)
    tool_version = Column(String(20), nullable=True)
    
    # Execution details
    input_parameters = Column(JSON, nullable=False)
    output_result = Column(JSON, nullable=True)
    execution_status = Column(String(20), default="pending", nullable=False)
    execution_duration = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Context
    execution_context = Column(JSON, default=dict, nullable=False)
    
    __table_args__ = (
        CheckConstraint("execution_status IN ('pending', 'running', 'completed', 'failed', 'timeout')"),
        Index('idx_tool_user_name', 'user_id', 'tool_name'),
        Index('idx_tool_status', 'execution_status'),
        Index('idx_tool_created', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "tool_name": self.tool_name,
            "input_parameters": self.input_parameters,
            "output_result": self.output_result,
            "execution_status": self.execution_status,
            "execution_duration": self.execution_duration,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
        }


class SystemLog(Base, UUIDMixin, TimestampMixin):
    """System-wide logging and monitoring."""
    __tablename__ = "system_logs"
    
    # Log classification
    log_level = Column(String(10), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    component = Column(String(50), nullable=False, index=True)
    
    # Log content
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    
    # Context information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("voice_sessions.id"), nullable=True)
    
    # Performance metrics
    processing_time = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)  # in MB
    
    __table_args__ = (
        CheckConstraint("log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')"),
        Index('idx_log_level_category', 'log_level', 'category'),
        Index('idx_log_created', 'created_at'),
        Index('idx_log_component', 'component'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "log_level": self.log_level,
            "category": self.category,
            "component": self.component,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat()
        }
